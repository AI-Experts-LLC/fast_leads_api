"""
Redis Queue (RQ) service for background job processing
"""
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
from rq import Queue, Worker
from rq.job import Job
from rq.exceptions import NoSuchJobError
import json
import uuid

from app.core.config import get_settings

settings = get_settings()

# Redis connection
redis_conn = redis.from_url(settings.redis_url)

# Queue instances
enrichment_queue = Queue('enrichment', connection=redis_conn)
high_priority_queue = Queue('high_priority', connection=redis_conn, default_timeout=1800)  # 30 min timeout
low_priority_queue = Queue('low_priority', connection=redis_conn, default_timeout=3600)   # 60 min timeout


class QueueService:
    """Service for managing background job queues"""
    
    def __init__(self):
        self.redis_conn = redis_conn
        self.default_queue = enrichment_queue
    
    def enqueue_enrichment_job(
        self, 
        account_data: Dict[str, Any], 
        priority: str = "normal",
        timeout: Optional[int] = None
    ) -> str:
        """
        Enqueue an account enrichment job
        
        Args:
            account_data: Salesforce account data
            priority: Job priority (high, normal, low)
            timeout: Job timeout in seconds
            
        Returns:
            Job ID string
        """
        job_id = str(uuid.uuid4())
        
        # Select queue based on priority
        if priority == "high":
            queue = high_priority_queue
            timeout = timeout or 1800  # 30 minutes
        elif priority == "low":
            queue = low_priority_queue  
            timeout = timeout or 3600  # 60 minutes
        else:
            queue = enrichment_queue
            timeout = timeout or 2400  # 40 minutes
        
        # Enqueue the job
        job = queue.enqueue(
            'app.services.enrichment.process_account_enrichment',
            account_data,
            job_id=job_id,
            timeout=timeout,
            meta={
                'account_id': account_data.get('Id'),
                'account_name': account_data.get('Name'),
                'priority': priority,
                'enqueued_at': datetime.utcnow().isoformat()
            }
        )
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status and progress
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status information
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            
            status_info = {
                "job_id": job_id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "progress": job.meta.get('progress', 0),
                "result": job.result,
                "exc_info": job.exc_info,
                "meta": job.meta
            }
            
            # Add timing information
            if job.started_at and job.ended_at:
                duration = (job.ended_at - job.started_at).total_seconds()
                status_info["duration_seconds"] = duration
            
            return status_info
            
        except NoSuchJobError:
            return {
                "job_id": job_id,
                "status": "not_found",
                "error": "Job not found in queue"
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e)
            }
    
    def update_job_progress(self, job_id: str, progress: int, message: str = None):
        """
        Update job progress
        
        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            job.meta['progress'] = progress
            if message:
                job.meta['progress_message'] = message
            job.meta['last_updated'] = datetime.utcnow().isoformat()
            job.save_meta()
        except NoSuchJobError:
            # Job not found, log this but don't raise error
            pass
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued or running job
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if successfully cancelled, False otherwise
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            if job.get_status() in ['queued', 'started']:
                job.cancel()
                return True
            return False
        except NoSuchJobError:
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics
        
        Returns:
            Queue statistics including counts and worker info
        """
        stats = {}
        
        for queue_name, queue in [
            ('enrichment', enrichment_queue),
            ('high_priority', high_priority_queue),
            ('low_priority', low_priority_queue)
        ]:
            stats[queue_name] = {
                'length': len(queue),
                'scheduled_length': len(queue.scheduled_job_registry),
                'started_length': len(queue.started_job_registry),
                'finished_length': len(queue.finished_job_registry),
                'failed_length': len(queue.failed_job_registry)
            }
        
        # Worker statistics
        workers = Worker.all(connection=self.redis_conn)
        stats['workers'] = {
            'total': len(workers),
            'active': len([w for w in workers if w.get_state() == 'busy']),
            'idle': len([w for w in workers if w.get_state() == 'idle'])
        }
        
        return stats
    
    def get_failed_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of failed jobs
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of failed job information
        """
        failed_jobs = []
        
        for queue in [enrichment_queue, high_priority_queue, low_priority_queue]:
            for job in queue.failed_job_registry.get_job_ids()[:limit]:
                try:
                    job_obj = Job.fetch(job, connection=self.redis_conn)
                    failed_jobs.append({
                        'job_id': job,
                        'queue': queue.name,
                        'failed_at': job_obj.ended_at.isoformat() if job_obj.ended_at else None,
                        'exception': job_obj.exc_info,
                        'meta': job_obj.meta
                    })
                except NoSuchJobError:
                    continue
        
        return failed_jobs[:limit]
    
    def retry_failed_job(self, job_id: str) -> bool:
        """
        Retry a failed job
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if successfully requeued, False otherwise
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            if job.get_status() == 'failed':
                job.requeue()
                return True
            return False
        except NoSuchJobError:
            return False


# Global queue service instance
queue_service = QueueService()


def get_queue_service() -> QueueService:
    """Get queue service instance"""
    return queue_service


# Worker startup function
def start_worker(queues: List[str] = None):
    """
    Start RQ worker
    
    Args:
        queues: List of queue names to process
    """
    if queues is None:
        queues = ['high_priority', 'enrichment', 'low_priority']
    
    # Create worker with connection
    worker = Worker(queues, connection=redis_conn)
    worker.work()
