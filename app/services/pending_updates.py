"""
Service for managing pending Salesforce updates.
Handles queuing, approval, and execution of Salesforce updates.
"""
import logging
import json
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import PendingUpdate, UpdateStatus, RecordType
from datetime import datetime

# Import contact enricher for persona detection and field mapping
try:
    from app.enrichers.web_search_contact_enricher import WebSearchContactEnricher
except ImportError:
    try:
        from enrichers.web_search_contact_enricher import WebSearchContactEnricher
    except ImportError:
        WebSearchContactEnricher = None

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
                    elif pending_update.record_type == RecordType.LEAD:
                        # For new leads, CREATE instead of UPDATE
                        result = self.sf.Lead.create(pending_update.field_updates)
                        lead_id = result.get('id')
                        pending_update.record_id = lead_id

                        # Queue the new lead for enrichment
                        # This will be picked up by a batch process to enrich leads with
                        # AI-generated fields (rapport summaries, campaign subjects, etc.)
                        if lead_id:
                            try:
                                await self.queue_update(
                                    record_type=RecordType.LEAD,
                                    record_id=lead_id,
                                    field_updates={
                                        "Description": (pending_update.field_updates.get("Description", "") +
                                                       "\n\n⏳ Queued for AI enrichment")
                                    },
                                    record_name=f"ENRICH: {pending_update.record_name}",
                                    enrichment_type="web_search_lead_enrichment"
                                )
                                logger.info(f"📋 Queued lead {lead_id} for AI enrichment (web search)")
                            except Exception as enrich_error:
                                logger.warning(f"⚠️ Failed to queue lead for enrichment: {str(enrich_error)}")

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

    async def queue_lead_batch(
        self,
        prospects: List[Dict],
        company_name: str,
        company_account_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Queue multiple discovered leads for approval with comprehensive enrichment.

        Uses the WebSearchContactEnricher for persona detection and field mapping
        to ensure consistency with contact enrichment.

        Args:
            prospects: List of qualified prospects from discovery
            company_name: Company name for context
            company_account_id: Salesforce Account ID to link leads to (optional)

        Returns:
            Dictionary with counts: {"success": X, "failed": Y, "total": Z}
        """
        success_count = 0
        failed_count = 0

        # Use the contact enricher's personas and detection logic
        if not WebSearchContactEnricher:
            logger.error("❌ WebSearchContactEnricher not available")
            return {"success": 0, "failed": len(prospects), "total": len(prospects)}

        # Get personas from the contact enricher class
        PERSONAS = WebSearchContactEnricher.PERSONAS

        # Create a temporary enricher instance for persona detection
        # (we don't need Salesforce connection, just the detect_persona method)
        class PersonaDetector:
            """Helper class to use contact enricher's persona detection."""
            PERSONAS = WebSearchContactEnricher.PERSONAS

            @staticmethod
            def detect_persona(title: str) -> dict:
                """Detect persona from job title using contact enricher logic."""
                title_lower = title.lower().strip()
                for persona_name, persona_data in PersonaDetector.PERSONAS.items():
                    for persona_title in persona_data['titles']:
                        if persona_title in title_lower:
                            return {'name': persona_name, **persona_data}
                # Default fallback
                return {'name': 'Director_Facilities', **PersonaDetector.PERSONAS['Director_Facilities']}

        for prospect in prospects:
            try:
                linkedin_data = prospect.get("linkedin_data", {})
                ai_ranking = prospect.get("ai_ranking", {})

                # Build comprehensive LinkedIn data JSON for Full_LinkedIn_Data__c field
                full_linkedin_data = {
                    "name": linkedin_data.get("name", ""),
                    "first_name": linkedin_data.get("first_name", ""),
                    "last_name": linkedin_data.get("last_name", ""),
                    "job_title": linkedin_data.get("job_title", ""),
                    "company": linkedin_data.get("company", ""),
                    "location": linkedin_data.get("location", ""),
                    "city": linkedin_data.get("city", ""),
                    "state": linkedin_data.get("state", ""),
                    "country": linkedin_data.get("country", ""),
                    "url": linkedin_data.get("url", ""),
                    "email": linkedin_data.get("email", ""),
                    "phone": linkedin_data.get("phone", ""),
                    "headline": linkedin_data.get("headline", ""),
                    "summary": linkedin_data.get("summary", ""),
                    "experience": linkedin_data.get("experience", []),
                    "education": linkedin_data.get("education", []),
                    "skills": linkedin_data.get("skills", []),
                    "connections": linkedin_data.get("connections", ""),
                }

                # ONLY populate fields we have complete data for from LinkedIn/Bright Data
                # All AI-generated enrichment fields (rapport, campaigns, etc.) will be populated
                # by web_search_contact_enricher AFTER the lead is approved and created
                lead_fields = {
                    # Standard Lead fields (from LinkedIn data)
                    "FirstName": linkedin_data.get("first_name", ""),
                    "LastName": linkedin_data.get("last_name", ""),
                    "Company": company_name,
                    "Title": linkedin_data.get("job_title", ""),
                    "Email": linkedin_data.get("email", ""),
                    "Phone": linkedin_data.get("phone", ""),
                    "City": linkedin_data.get("city", ""),
                    "State": linkedin_data.get("state", ""),
                    "Country": linkedin_data.get("country", ""),
                    "Description": ai_ranking.get("reasoning", ""),
                    "LeadSource": "Hybrid Prospect Discovery",
                    "Status": "New",
                    "Rating": "Hot" if ai_ranking.get("ranking_score", 0) >= 80 else "Warm",

                    # LinkedIn Profile Data (Custom Fields)
                    "LinkedIn__c": linkedin_data.get("url", ""),
                    "Full_LinkedIn_Data__c": json.dumps(full_linkedin_data, indent=2) if full_linkedin_data else "",
                }

                # Add LinkedIn headline to description if available
                if linkedin_data.get("headline"):
                    lead_fields["Description"] = f"{ai_ranking.get('reasoning', '')}\n\nLinkedIn: {linkedin_data.get('headline', '')}"

                # Link to account if provided
                if company_account_id:
                    lead_fields["Account__c"] = company_account_id  # Custom field linking to Account

                # Remove empty fields
                lead_fields = {k: v for k, v in lead_fields.items() if v}

                # Queue the lead
                await self.queue_update(
                    record_type=RecordType.LEAD,
                    record_id="PENDING",  # Will be set after creation
                    field_updates=lead_fields,
                    record_name=f"{linkedin_data.get('first_name', '')} {linkedin_data.get('last_name', '')}".strip(),
                    enrichment_type="hybrid_prospect_discovery"
                )

                success_count += 1
                logger.info(f"✅ Queued lead: {linkedin_data.get('name', 'Unknown')} ({persona_name}) with {len(lead_fields)} enriched fields")

            except Exception as e:
                logger.error(f"❌ Failed to queue lead: {str(e)}")
                failed_count += 1

        total = success_count + failed_count
        logger.info(
            f"✅ Queued {success_count}/{total} leads for approval, "
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
