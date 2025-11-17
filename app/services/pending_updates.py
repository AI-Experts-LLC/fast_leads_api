"""
Service for managing pending Salesforce updates.
Handles queuing, approval, and execution of Salesforce updates.
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import PendingUpdate, UpdateStatus, RecordType
from datetime import datetime

logger = logging.getLogger(__name__)


class PendingUpdatesService:
    """Service for managing pending Salesforce updates."""

    def __init__(self, db_session: AsyncSession, sf_connection=None):
        """
        Initialize the pending updates service.

        Args:
            db_session: Async database session
            sf_connection: Salesforce connection (simple_salesforce)
        """
        self.db = db_session
        self.sf = sf_connection

    async def queue_update(
        self,
        record_type: RecordType,
        record_id: str,
        field_updates: Dict[str, any],
        record_name: Optional[str] = None,
        enrichment_type: Optional[str] = None
    ) -> PendingUpdate:
        """
        Queue a Salesforce update for approval.

        Args:
            record_type: "Account" or "Contact"
            record_id: Salesforce record ID
            field_updates: Dictionary of field names to values
            record_name: Display name for the record
            enrichment_type: Type of enrichment (e.g., "web_search_account")

        Returns:
            Created PendingUpdate record
        """
        try:
            pending_update = PendingUpdate(
                record_type=record_type,
                record_id=record_id,
                record_name=record_name,
                field_updates=field_updates,
                enrichment_type=enrichment_type,
                status=UpdateStatus.PENDING
            )

            self.db.add(pending_update)
            await self.db.commit()
            await self.db.refresh(pending_update)

            logger.info(
                f"✅ Queued {record_type.value} update for {record_id} "
                f"({len(field_updates)} fields) - ID: {pending_update.id}"
            )

            return pending_update

        except Exception as e:
            logger.error(f"❌ Failed to queue update: {str(e)}")
            await self.db.rollback()
            raise

    async def get_pending_updates(
        self,
        record_type: Optional[RecordType] = None,
        status: UpdateStatus = UpdateStatus.PENDING,
        limit: int = 100
    ) -> List[PendingUpdate]:
        """
        Get pending updates filtered by record type and status.

        Args:
            record_type: Filter by "Account" or "Contact" (optional)
            status: Filter by status (default: PENDING)
            limit: Maximum number of records to return

        Returns:
            List of PendingUpdate records
        """
        try:
            query = select(PendingUpdate).where(PendingUpdate.status == status)

            if record_type:
                query = query.where(PendingUpdate.record_type == record_type)

            query = query.order_by(PendingUpdate.created_at.desc()).limit(limit)

            result = await self.db.execute(query)
            updates = result.scalars().all()

            logger.info(f"📋 Retrieved {len(updates)} pending updates")
            return updates

        except Exception as e:
            logger.error(f"❌ Failed to retrieve pending updates: {str(e)}")
            raise

    async def approve_update(
        self,
        update_id: int,
        approved_by: Optional[str] = None
    ) -> bool:
        """
        Approve and execute a pending update to Salesforce.

        Args:
            update_id: ID of the pending update
            approved_by: Username/identifier of who approved

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the pending update
            result = await self.db.execute(
                select(PendingUpdate).where(PendingUpdate.id == update_id)
            )
            pending_update = result.scalar_one_or_none()

            if not pending_update:
                logger.error(f"❌ Pending update {update_id} not found")
                return False

            if pending_update.status != UpdateStatus.PENDING:
                logger.warning(f"⚠️ Update {update_id} already {pending_update.status.value}")
                return False

            # Execute Salesforce update
            if self.sf:
                try:
                    if pending_update.record_type == RecordType.ACCOUNT:
                        self.sf.Account.update(
                            pending_update.record_id,
                            pending_update.field_updates
                        )
                    elif pending_update.record_type == RecordType.CONTACT:
                        self.sf.Contact.update(
                            pending_update.record_id,
                            pending_update.field_updates
                        )

                    logger.info(
                        f"✅ Applied {len(pending_update.field_updates)} field updates "
                        f"to {pending_update.record_type.value} {pending_update.record_id}"
                    )
                except Exception as sf_error:
                    logger.error(f"❌ Salesforce update failed: {str(sf_error)}")
                    return False
            else:
                logger.warning("⚠️ No Salesforce connection - simulating approval")

            # Update status in database
            pending_update.status = UpdateStatus.APPROVED
            pending_update.approved_by = approved_by
            pending_update.approved_at = datetime.utcnow()
            pending_update.updated_at = datetime.utcnow()

            await self.db.commit()

            logger.info(f"✅ Approved and executed update {update_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to approve update {update_id}: {str(e)}")
            await self.db.rollback()
            return False

    async def approve_all_pending(
        self,
        record_type: Optional[RecordType] = None,
        approved_by: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Approve and execute all pending updates.

        Args:
            record_type: Filter by "Account" or "Contact" (optional)
            approved_by: Username/identifier of who approved

        Returns:
            Dictionary with counts: {"success": X, "failed": Y, "total": Z}
        """
        pending_updates = await self.get_pending_updates(
            record_type=record_type,
            status=UpdateStatus.PENDING
        )

        success_count = 0
        failed_count = 0

        for update in pending_updates:
            if await self.approve_update(update.id, approved_by):
                success_count += 1
            else:
                failed_count += 1

        total = success_count + failed_count
        logger.info(
            f"✅ Bulk approval complete: {success_count}/{total} successful, "
            f"{failed_count} failed"
        )

        return {
            "success": success_count,
            "failed": failed_count,
            "total": total
        }

    async def reject_update(self, update_id: int) -> bool:
        """
        Reject a pending update (marks as rejected, no Salesforce update).

        Args:
            update_id: ID of the pending update

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(PendingUpdate).where(PendingUpdate.id == update_id)
            )
            pending_update = result.scalar_one_or_none()

            if not pending_update:
                logger.error(f"❌ Pending update {update_id} not found")
                return False

            if pending_update.status != UpdateStatus.PENDING:
                logger.warning(f"⚠️ Update {update_id} already {pending_update.status.value}")
                return False

            pending_update.status = UpdateStatus.REJECTED
            pending_update.updated_at = datetime.utcnow()

            await self.db.commit()

            logger.info(f"✅ Rejected update {update_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to reject update {update_id}: {str(e)}")
            await self.db.rollback()
            return False
