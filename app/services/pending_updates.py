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
                        pending_update.record_id = result.get('id', pending_update.record_id)

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

        Args:
            prospects: List of qualified prospects from discovery
            company_name: Company name for context
            company_account_id: Salesforce Account ID to link leads to (optional)

        Returns:
            Dictionary with counts: {"success": X, "failed": Y, "total": Z}
        """
        success_count = 0
        failed_count = 0

        # Persona definitions for detection and field population
        PERSONAS = {
            'CFO': {
                'titles': ['cfo', 'chief financial officer', 'finance director', 'vp finance', 'vice president finance'],
                'pain_points': 'Energy is a top-5 line item in operating costs, emergency repairs blow budgets, hard to prioritize infrastructure vs revenue-driving projects',
                'value_prop': 'Zero CapEx financing, predictable long-term costs, linking savings directly to margin improvement'
            },
            'VP_Operations': {
                'titles': ['vp operations', 'vice president operations', 'operations director', 'chief operations officer', 'chief operating officer', 'coo'],
                'pain_points': 'Downtime disrupts patient care, staffing shortages exacerbate operational stress, aging systems are constant headaches',
                'value_prop': 'Reliability and resilience with no downtime, smoother day-to-day ops with less staff distraction'
            },
            'Director_Facilities': {
                'titles': ['facilities director', 'director facilities', 'facilities manager', 'maintenance director', 'plant operations', 'senior director facilities', 'senior director, facilities'],
                'pain_points': 'Constant firefighting with old equipment, pressure to cut energy use with limited budget, rising costs of emergency repairs',
                'value_prop': 'Fewer emergencies and maintenance headaches, partnership with experts, proven vendor performance'
            },
            'Director_Sustainability': {
                'titles': ['sustainability director', 'director sustainability', 'environmental director', 'energy manager', 'senior energy engineer', 'energy engineer', 'sustainability manager'],
                'pain_points': 'Ambitious climate targets without clear funding, difficulty getting buy-in across departments, need to show measurable progress',
                'value_prop': 'Partner in hitting sustainability goals without CapEx, measurable carbon reduction, success stories to share'
            }
        }

        def detect_persona(title: str) -> dict:
            """Detect persona from job title and return persona data."""
            title_lower = title.lower().strip()
            for persona_name, persona_data in PERSONAS.items():
                for persona_title in persona_data['titles']:
                    if persona_title in title_lower:
                        return {'name': persona_name, **persona_data}
            # Default fallback
            return {'name': 'Director_Facilities', **PERSONAS['Director_Facilities']}

        for prospect in prospects:
            try:
                linkedin_data = prospect.get("linkedin_data", {})
                ai_ranking = prospect.get("ai_ranking", {})

                # Detect persona from job title
                title = linkedin_data.get("job_title", "")
                persona = detect_persona(title)

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

                # Extract basic lead fields
                lead_fields = {
                    # Standard Lead fields
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

                    # LinkedIn & Contact Info (Custom Fields)
                    "LinkedIn__c": linkedin_data.get("url", ""),
                    "Full_LinkedIn_Data__c": json.dumps(full_linkedin_data, indent=2) if full_linkedin_data else "",

                    # Work Experience Fields (Custom Fields)
                    "Role_description__c": f"{title} at {company_name}. {linkedin_data.get('headline', '')}",
                    "Why_their_role_is_relevant_to_Metrus__c": f"As a {title}, this prospect is responsible for decisions related to: {persona.get('pain_points', '')}",
                    "Summary_Why_should_they_care__c": f"Metrus offers: {persona.get('value_prop', '')}",

                    # Persona & Pain Points (Custom Fields)
                    "Persona__c": persona.get('name', 'Director_Facilities'),
                    "Pain_Points__c": persona.get('pain_points', ''),
                    "Value_Proposition__c": persona.get('value_prop', ''),

                    # General Personal Information (Custom Fields)
                    "General_personal_information_notes__c": f"LinkedIn: {linkedin_data.get('url', '')}. Headline: {linkedin_data.get('headline', '')}. Location: {linkedin_data.get('location', '')}. Connections: {linkedin_data.get('connections', '')}",

                    # Miscellaneous Notes (Custom Fields)
                    "Miscellaneous_notes__c": f"AI Qualification Score: {ai_ranking.get('ranking_score', 0)}/100. Discovery Method: Hybrid (Serper + Bright Data). Source: {prospect.get('source', 'unknown')}",
                }

                # Add work experience summary if available
                experience = linkedin_data.get("experience", [])
                if experience and len(experience) > 0:
                    experience_summary = "\n\n".join([
                        f"• {exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')} ({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})"
                        for exp in experience[:3]  # Top 3 experiences
                    ])
                    lead_fields["Energy_Project_History__c"] = f"Work Experience:\n{experience_summary}"

                # Add education summary if available
                education = linkedin_data.get("education", [])
                if education and len(education) > 0:
                    education_summary = "\n".join([
                        f"• {edu.get('degree', '')} from {edu.get('school', 'Unknown')}"
                        for edu in education[:2]  # Top 2 education entries
                    ])
                    if lead_fields.get("General_personal_information_notes__c"):
                        lead_fields["General_personal_information_notes__c"] += f"\n\nEducation:\n{education_summary}"

                # Generate persona-specific email campaign subject lines (Custom Fields)
                persona_name = persona.get('name', 'Director_Facilities')
                if persona_name == 'CFO':
                    lead_fields["Campaign_1_Subject_Line__c"] = f"Lower energy costs at {company_name} without CapEx"
                    lead_fields["Campaign_2_Subject_Line__c"] = f"Predictable infrastructure budgets for {company_name}"
                    lead_fields["Campaign_3_Subject_Line__c"] = f"Link energy savings directly to margins"
                    lead_fields["Campaign_4_Subject_Line__c"] = f"Zero-cost energy upgrades for {company_name}"
                elif persona_name == 'VP_Operations':
                    lead_fields["Campaign_1_Subject_Line__c"] = f"Eliminate downtime at {company_name}"
                    lead_fields["Campaign_2_Subject_Line__c"] = f"Reduce operational stress with reliable infrastructure"
                    lead_fields["Campaign_3_Subject_Line__c"] = f"Free up staff time at {company_name}"
                    lead_fields["Campaign_4_Subject_Line__c"] = f"Resilient systems for uninterrupted patient care"
                elif persona_name == 'Director_Sustainability':
                    lead_fields["Campaign_1_Subject_Line__c"] = f"Meet {company_name}'s climate goals without CapEx"
                    lead_fields["Campaign_2_Subject_Line__c"] = f"Measurable carbon reduction at {company_name}"
                    lead_fields["Campaign_3_Subject_Line__c"] = f"Success stories for sustainability initiatives"
                    lead_fields["Campaign_4_Subject_Line__c"] = f"Partner in sustainability goals at {company_name}"
                else:  # Director_Facilities (default)
                    lead_fields["Campaign_1_Subject_Line__c"] = f"End emergency repairs at {company_name}"
                    lead_fields["Campaign_2_Subject_Line__c"] = f"Reduce maintenance headaches with expert partnership"
                    lead_fields["Campaign_3_Subject_Line__c"] = f"Cut energy costs at {company_name} with proven vendor"
                    lead_fields["Campaign_4_Subject_Line__c"] = f"Reliable infrastructure without budget strain"

                # Generate rapport summaries based on available data (Custom Fields)
                # Rapport Summary 1: LinkedIn headline and experience
                if linkedin_data.get("headline"):
                    lead_fields["Rapport_summary__c"] = f"Noted your experience as {linkedin_data.get('headline')}. Your background in healthcare operations aligns perfectly with Metrus's expertise."

                # Rapport Summary 2: Location-based
                if linkedin_data.get("location"):
                    lead_fields["Rapport_summary_2__c"] = f"Based in {linkedin_data.get('location')}, you understand the unique infrastructure challenges facing healthcare facilities in your region."

                # Rapport Summary 3: Persona-specific pain points
                lead_fields["Rapport_summary_3__c"] = f"As a {title}, you likely face: {persona.get('pain_points', '')}. Metrus specializes in solving exactly these challenges."

                # Rapport Summary 4: Company size/scale
                if linkedin_data.get("connections"):
                    lead_fields["Rapport_summary_4__c"] = f"With {linkedin_data.get('connections')} connections on LinkedIn, you're clearly well-connected in the healthcare infrastructure space. We'd value the opportunity to add to your network."

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
