#!/usr/bin/env python3
"""
Web Search Contact Enricher for Salesforce

Uses OpenAI's web search to find comprehensive information about healthcare contacts.
Enriches contacts in focused sections with separate web searches for better results.

Usage:
    python web_search_contact_enricher.py "CONTACT_RECORD_ID" [--overwrite] [--include-linkedin]
"""

import os
import sys
import logging
import json
import argparse
import asyncio
from typing import Optional, Dict, Any, List
from simple_salesforce import Salesforce
from dotenv import load_dotenv
import openai
import time

# Import field validator for data quality
try:
    from .field_validator import FieldValidator
except ImportError:
    try:
        from field_validator import FieldValidator
    except ImportError:
        from enrichers.field_validator import FieldValidator

# Import LinkedIn enricher
try:
    from .linkedin_contact_enricher import LinkedInContactEnricher
except ImportError:
    try:
        from linkedin_contact_enricher import LinkedInContactEnricher
    except ImportError:
        try:
            from enrichers.linkedin_contact_enricher import LinkedInContactEnricher
        except ImportError:
            LinkedInContactEnricher = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenAI Configuration
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini-search-preview")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


class WebSearchContactEnricher:
    """Web search-enabled contact enricher for Salesforce."""

    # Field mapping - ONLY personalized fields (ZoomInfo handles contact info, LinkedIn, phones, education, location)
    FIELD_MAPPING = {
        # Personalized Rapport Fields (Web Search Only)
        'local_sports_team': 'Local_sports_team__c',
        'rapport_summary': 'Rapport_summary__c',
        'rapport_summary_2': 'Rapport_summary_2__c',
        'rapport_summary_3': 'Rapport_summary_3__c',
        'rapport_summary_4': 'Rapport_summary_4__c',
        'miscellaneous_notes': 'Miscellaneous_notes__c',

        # Personalized Work Experience Fields (Web Search Only)
        'role_description': 'Role_description__c',
        'energy_project_history': 'Energy_Project_History__c',
        'why_role_relevant': 'Why_their_role_is_relevant_to_Metrus__c',
        'summary_why_care': 'Summary_Why_should_they_care__c',
        'general_personal_info': 'General_personal_information_notes__c',

        # Email Customization (Web Search Only)
        'campaign_1_subject': 'Campaign_1_Subject_Line__c',
        'campaign_2_subject': 'Campaign_2_Subject_Line__c',
        'campaign_3_subject': 'Campaign_3_Subject_Line__c',
        'campaign_4_subject': 'Campaign_4_Subject_Line__c',
    }

    # NOTE: ZoomInfo enricher handles these fields, so we don't touch them:
    # - LinkedIn_Profile__c, Direct_Phone__c, Mobile_Zoominfo__c, Education__c, Location__c
    # - FirstName, LastName, Email, Phone, Title, Department, Description
    # - Address fields (MailingStreet, MailingCity, etc.)

    # Metrus target personas based on battlecards
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

    def __init__(self):
        """Initialize the enricher with Salesforce and OpenAI connections."""
        self.sf = None
        self.openai_client = None
        self.linkedin_enricher = None

        # Load environment variables
        load_dotenv()

        self._connect_to_salesforce()
        self._setup_openai_client()

    def _connect_to_salesforce(self) -> None:
        """Connect to Salesforce using environment variables."""
        try:
            username = os.getenv('SALESFORCE_USERNAME')
            password = os.getenv('SALESFORCE_PASSWORD')
            security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
            domain = os.getenv('SALESFORCE_DOMAIN', 'login')

            if not username or not password:
                raise ValueError("Missing required Salesforce credentials")

            logger.info("🔗 Connecting to Salesforce...")

            if security_token:
                self.sf = Salesforce(
                    username=username,
                    password=password,
                    security_token=security_token,
                    domain=domain
                )
            else:
                self.sf = Salesforce(
                    username=username,
                    password=password,
                    domain=domain
                )

            # Test connection
            test_result = self.sf.query("SELECT Id FROM Contact LIMIT 1")
            if test_result and test_result.get('totalSize', 0) >= 0:
                logger.info("✅ Successfully connected to Salesforce")
            else:
                raise Exception("Connected but test query failed")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Salesforce: {str(e)}")
            raise

    def _setup_openai_client(self) -> None:
        """Setup OpenAI client with API key."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY environment variable")

            # Initialize OpenAI client with base URL if specified
            if OPENAI_BASE_URL != "https://api.openai.com/v1":
                self.openai_client = openai.OpenAI(
                    api_key=api_key,
                    base_url=OPENAI_BASE_URL
                )
            else:
                self.openai_client = openai.OpenAI(api_key=api_key)

            logger.info("✅ OpenAI client configured with web search capabilities")

        except Exception as e:
            logger.error(f"❌ Failed to setup OpenAI client: {str(e)}")
            raise

    def _setup_linkedin_enricher(self) -> None:
        """Setup LinkedIn enricher module."""
        try:
            if LinkedInContactEnricher is None:
                logger.warning("⚠️ LinkedIn enricher not available - install required dependencies")
                return
            
            self.linkedin_enricher = LinkedInContactEnricher()
            logger.info("✅ LinkedIn enricher module configured")
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup LinkedIn enricher: {str(e)}")
            logger.info("🔧 Continuing without LinkedIn enrichment")
            self.linkedin_enricher = None

    def get_contact_details(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get contact record with account details."""
        try:
            logger.info(f"🔍 Retrieving contact details: {record_id}")

            # Get contact with account information
            contact = self.sf.Contact.get(record_id)
            if not contact:
                logger.warning(f"❌ No contact found for ID: {record_id}")
                return None

            # Get account details if available (including enriched capital history data)
            account_info = {}
            if contact.get('AccountId'):
                try:
                    account = self.sf.Account.get(contact['AccountId'])
                    account_info = {
                        'account_name': account.get('Name', ''),
                        'account_website': account.get('Website', ''),
                        'account_industry': account.get('Industry', ''),
                        'account_description': account.get('Description', ''),
                        # Rich enriched data from Account enricher for rapport building
                        'company_description': account.get('General_Company_Description__c', ''),
                        'hq_location': account.get('HQ_location__c', ''),
                        'employee_count': account.get('Employee_count__c', ''),
                        'geographic_footprint': account.get('Geographic_footprint__c', ''),
                        'company_news': account.get('General_Company_News__c', ''),
                        'capital_history': account.get('Capital_and_project_history__c', ''),
                        'future_capital': account.get('Past_future_capital_uses__c', ''),
                        'infrastructure_upgrades': account.get('Infrastructure_upgrades__c', ''),
                        'energy_projects': account.get('Energy_efficiency_projects__c', ''),
                    }
                    logger.info(f"📊 Retrieved enriched account data including capital history for rapport building")
                except Exception as e:
                    logger.warning(f"⚠️ Could not retrieve account info: {str(e)}")

            # Combine contact and account info
            contact.update(account_info)

            name = f"{contact.get('FirstName', '')} {contact.get('LastName', '')}".strip()
            company = contact.get('account_name', 'Unknown Company')
            logger.info(f"✅ Found contact: {name} at {company}")

            return contact

        except Exception as e:
            logger.error(f"❌ Error retrieving contact: {str(e)}")
            return None

    def check_updatable_fields(self, contact: Dict[str, Any], overwrite: bool = False) -> Dict[str, List[str]]:
        """Check which fields can be updated, organized by section."""
        # Organize fields by section - ONLY personalized fields (ZoomInfo handles basic contact info)
        sections = {
            'personalized_rapport': [
                'local_sports_team', 'rapport_summary', 'rapport_summary_2', 'rapport_summary_3', 'rapport_summary_4', 'miscellaneous_notes'
            ],
            'work_experience': [
                'role_description', 'energy_project_history', 'why_role_relevant',
                'summary_why_care', 'general_personal_info'
            ],
            'email_customization': [
                'campaign_1_subject', 'campaign_2_subject', 'campaign_3_subject', 'campaign_4_subject'
            ]
        }

        updatable_sections = {}

        logger.info("📋 Checking field status by section:")

        for section_name, field_list in sections.items():
            updatable_fields = []
            logger.info(f"\n📂 {section_name.replace('_', ' ').title()}:")

            for field_key in field_list:
                if field_key not in self.FIELD_MAPPING:
                    continue

                salesforce_field = self.FIELD_MAPPING[field_key]
                current_value = contact.get(salesforce_field, '')
                is_empty = not current_value or (isinstance(current_value, str) and len(current_value.strip()) == 0)

                if overwrite or is_empty:
                    updatable_fields.append(field_key)
                    status = "🟢 WILL UPDATE" if overwrite else "🟡 EMPTY - WILL UPDATE"
                else:
                    status = "🔴 HAS DATA - SKIP"

                preview = ""
                if current_value and isinstance(current_value, str):
                    preview = f" (current: {current_value[:30]}{'...' if len(current_value) > 30 else ''})"

                logger.info(f"   {field_key}: {status}{preview}")

            if updatable_fields:
                updatable_sections[section_name] = updatable_fields

        total_updatable = sum(len(fields) for fields in updatable_sections.values())
        logger.info(f"\n📊 Summary: {total_updatable}/{len(self.FIELD_MAPPING)} fields can be updated across {len(updatable_sections)} sections")

        return updatable_sections

    def detect_persona(self, title: str) -> str:
        """Detect Metrus target persona based on job title."""
        title_lower = title.lower().strip()

        for persona, data in self.PERSONAS.items():
            for persona_title in data['titles']:
                if persona_title in title_lower:
                    logger.info(f"🎯 Detected persona: {persona} (matched '{persona_title}' in '{title}')")
                    return persona

        # Default fallback
        logger.info(f"🤷 No specific persona detected for '{title}', defaulting to Director_Facilities")
        return 'Director_Facilities'

    def search_general_information(self, contact: Dict[str, Any]) -> Dict[str, str]:
        """Search for general information about the contact."""
        try:
            first_name = contact.get('FirstName', '')
            last_name = contact.get('LastName', '')
            company = contact.get('account_name', '')
            title = contact.get('Title', '')
            location = contact.get('MailingCity', '') or contact.get('MailingState', '')

            logger.info("🔍 Searching for general contact information...")

            # Detect persona for tailored approach
            persona = self.detect_persona(title)
            persona_context = self.PERSONAS.get(persona, self.PERSONAS['Director_Facilities'])

            # Get account enrichment data and LinkedIn data for more personalized rapport building
            account_context = []
            if contact.get('capital_history'):
                account_context.append(f"Capital History: {contact['capital_history']}")
            if contact.get('infrastructure_upgrades'):
                account_context.append(f"Infrastructure Projects: {contact['infrastructure_upgrades']}")
            if contact.get('energy_projects'):
                account_context.append(f"Energy Projects: {contact['energy_projects']}")
            if contact.get('company_news'):
                account_context.append(f"Company News: {contact['company_news']}")
            if contact.get('future_capital'):
                account_context.append(f"Future Capital Plans: {contact['future_capital']}")

            # Add LinkedIn data if available for additional rapport context
            linkedin_data = contact.get('Full_LinkedIn_Data__c', '') or contact.get('Full_LinkedIn_Data', '')
            if linkedin_data and linkedin_data.strip():
                account_context.append(f"LinkedIn Background: {linkedin_data}")

            account_data = "\n".join(account_context) if account_context else "Limited account information available"

            prompt = f"""Create personalized rapport-building content for this healthcare professional:

Contact Details:
- Name: {first_name} {last_name}
- Company: {company}
- Title: {title}
- Location: {location}
- Detected Role Type: {persona}

Account Context (use this for rapport building):
{account_data}

Please search for and provide ONLY personalized rapport content (use LinkedIn Background above if available for additional context):
1. Local sports teams they might follow based on their location/city
2. Professional background useful for building rapport (like the school they went to, the city they live in, etc.)
3. FOUR rapport-building opening sentences that align with email campaign themes:
   - Professional recognition/achievement focused (Campaign 1 theme)
   - Shared professional interest (Campaign 2 theme)
   - Company-specific observation/infrastructure projects (Campaign 3 theme)
   - Local/regional connection/sports/community (Campaign 4 theme)

Format as JSON with these exact keys:
- local_sports_team: Local sports teams as a simple comma-separated list (e.g., "Dallas Cowboys, Dallas Mavericks" or "Boston Red Sox, Boston Celtics")
- rapport_summary: Professional recognition/achievement opening sentence - NO LINKS (aligns with Campaign 1)
- rapport_summary_2: Shared professional interest opening sentence - NO LINKS (aligns with Campaign 2)
- rapport_summary_3: Company-specific observation/infrastructure project opening sentence - NO LINKS (aligns with Campaign 3)
- rapport_summary_4: Local/regional connection/sports/community opening sentence - NO LINKS (aligns with Campaign 4)
- miscellaneous_notes: Any other interesting personal/professional details for rapport building

IMPORTANT:
1. Each rapport summary should align thematically with its corresponding campaign subject line theme.
2. Use the account context above to craft rapport_summary_3 that references specific capital projects, infrastructure work, or company initiatives.
3. Make all sentences natural and relationship-focused, not sales-focused.
4. NEVER include links, URLs, or citations in rapport summaries - they should be clean, personalized sentences only.
5. Rapport summaries are meant to be opening sentences in emails that show personal research effort.
6. DO NOT include contact info, LinkedIn, or location - focus only on rapport content."""

            # Define expected fields for validation
            expected_fields = ['local_sports_team', 'rapport_summary', 'rapport_summary_2', 'rapport_summary_3', 'rapport_summary_4', 'miscellaneous_notes']

            # Use retry mechanism with validation
            data = self._make_api_call_with_retry(prompt, expected_fields)
            logger.info(f"✅ General information search completed")

            # Refine rapport summaries to be more conversational
            if data:
                data = self._refine_rapport_summaries(data, first_name)

            return data

        except Exception as e:
            logger.error(f"❌ Error searching general information: {str(e)}")
            return {}

    def search_work_experience(self, contact: Dict[str, Any]) -> Dict[str, str]:
        """Search for work experience and career information."""
        try:
            first_name = contact.get('FirstName', '')
            last_name = contact.get('LastName', '')
            company = contact.get('account_name', '')
            title = contact.get('Title', '')

            logger.info("🔍 Searching for work experience information...")

            # Get persona-specific pain points for targeted messaging
            persona = self.detect_persona(title)
            persona_data = self.PERSONAS.get(persona, self.PERSONAS['Director_Facilities'])

            prompt = f"""Find detailed work experience and career information for this healthcare professional:

Contact Details:
- Name: {first_name} {last_name}
- Company: {company}
- Title: {title}
- Detected Persona: {persona}

Persona-Specific Pain Points for {persona}:
{persona_data['pain_points']}

Please search for and provide:
1. How long they've been at their current company
2. How long they've been in their current role
3. Total years of work experience
4. Detailed role description and responsibilities
5. Any energy/sustainability project history
6. INTERNAL SALES INTELLIGENCE: Strategic sales notes about this contact's relevance to Metrus
7. CRITICAL: Second email sentence connecting their role to Metrus based on persona pain points

Format as JSON with these exact keys:
- tenure_current_company: Years/months at current company
- time_in_role: Time in current role
- total_work_experience: Total years of experience
- role_description: Detailed description of current role and responsibilities
- energy_project_history: Any energy/sustainability projects they've been involved in (format as bullet points, not JSON objects)
- why_role_relevant: INTERNAL SALES INTELLIGENCE ONLY: Strategic notes for sales team about this contact's role - Include: decision-making authority level, budget influence, specific pain points they likely face, how Metrus solutions directly address their challenges, and their strategic value as a champion/influencer
- summary_why_care: EXACT format: "As the [their title, but conversationally] at [their company, but conversationally], I'm sure you've faced challenges with [specific pain points from persona above]."
- general_personal_info: Additional professional background notes

CRITICAL for summary_why_care:
- Use EXACT format: "In your role as [title] at [hospital], I'm sure you've faced challenges with [pain points]"
- Reference the persona-specific pain points above
- Make it specific to their detected persona ({persona})
- Examples:
  * CFO: "In your role as CFO at [company], I'm sure you've faced challenges with energy being a top-5 operating cost and emergency repairs blowing budgets."
  * Director_Facilities: "In your role as Senior Director, Facilities Operations & Maintenance at [company], I'm sure you've faced challenges with constant firefighting with old equipment and pressure to cut energy use with limited budget."

Focus on their healthcare industry experience and any connection to facilities, operations, or sustainability.

IMPORTANT FORMATTING:
- Format energy_project_history as clean bullet points with newlines '• Project Name: Description', NOT as JSON objects or Python lists
- Remove any URLs, links, or citations from energy_project_history
- Each bullet point should be on its own line separated by newlines
- Keep all responses clean and readable for business use"""

            # Define expected fields for validation
            expected_fields = ['tenure_current_company', 'time_in_role', 'total_work_experience', 'role_description', 'energy_project_history', 'why_role_relevant', 'summary_why_care', 'general_personal_info']

            # Use retry mechanism with validation
            data = self._make_api_call_with_retry(prompt, expected_fields)
            logger.info(f"✅ Work experience search completed")

            # Refine summary_why_care to be conversational with proper company name
            if data and 'summary_why_care' in data:
                data = self._refine_summary_why_care(data, first_name, company)

            return data

        except Exception as e:
            logger.error(f"❌ Error searching work experience: {str(e)}")
            return {}

    def generate_email_campaigns(self, contact: Dict[str, Any], enriched_data: Dict[str, str]) -> Dict[str, str]:
        """Generate personalized email campaign subject lines."""
        try:
            first_name = contact.get('FirstName', '')
            company = contact.get('account_name', '')
            title = contact.get('Title', '')

            logger.info("📧 Generating email campaign subject lines...")

            # Detect persona for tailored messaging
            persona = self.detect_persona(title)
            persona_context = self.PERSONAS.get(persona, self.PERSONAS['Director_Facilities'])

            # Combine all enriched data for context
            context_info = []
            for key, value in enriched_data.items():
                if value and len(value.strip()) > 0:
                    context_info.append(f"{key}: {value}")

            # Add LinkedIn data if available for additional context
            linkedin_data = contact.get('Full_LinkedIn_Data__c', '') or contact.get('Full_LinkedIn_Data', '')
            if linkedin_data and linkedin_data.strip():
                context_info.append(f"LinkedIn Background: {linkedin_data}")

            context = "\n".join(context_info) if context_info else "Limited background information available"

            prompt = f"""Create 4 personalized email subject lines for this healthcare professional. These should be connection-focused, not salesy.

Contact Details:
- Name: {first_name}
- Company: {company}
- Title: {title}
- Detected Persona: {persona}

Background Information:
{context}

Create 4 different subject lines that focus on building rapport and connection (NOT direct sales pitches). Each should:
1. Be personal and show research effort
2. Hook the reader with genuine interest/curiosity
3. Build trust through non-salesy approach
4. Be 30-50 characters for mobile optimization

Subject line themes (personalized but NOT sales-focused):
1. Professional recognition/achievement angle
2. Industry connection/shared interest angle
3. Company-specific observation/question
4. Local/regional connection angle

Examples of the right tone:
- "Danette, impressive Cleveland Clinic recognition"
- "Fellow facilities professional in Cleveland"
- "Question about infrastructure projects"

Format as JSON with these exact keys:
- campaign_1_subject: Professional recognition-based subject line
- campaign_2_subject: Industry connection-based subject line
- campaign_3_subject: Company-specific observation subject line
- campaign_4_subject: Local/regional connection subject line

Make them personal, curious, and trust-building - NOT sales-focused."""

            # Define expected fields for validation
            expected_fields = ['campaign_1_subject', 'campaign_2_subject', 'campaign_3_subject', 'campaign_4_subject']

            # Use retry mechanism with validation
            data = self._make_api_call_with_retry(prompt, expected_fields, max_retries=2)
            logger.info(f"✅ Email campaigns generated")

            return data

        except Exception as e:
            logger.error(f"❌ Error generating email campaigns: {str(e)}")
            return {}

    def _extract_json_from_response(self, content: str) -> Dict[str, str]:
        """Extract JSON data from OpenAI response content."""
        try:
            # Look for JSON block in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)

                # Ensure all values are strings and not empty
                cleaned_data = {}
                for key, value in data.items():
                    if value and str(value).strip():
                        clean_value = str(value).strip()

                        # Special cleanup for specific fields
                        if key == 'energy_project_history':
                            clean_value = self._clean_energy_project_history(clean_value)
                        elif key == 'local_sports_team':
                            clean_value = self._clean_local_sports_team(clean_value)

                        cleaned_data[key] = clean_value

                return cleaned_data
            else:
                logger.warning("⚠️ No JSON found in response")
                return {}

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Failed to parse JSON: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"❌ Error extracting JSON: {str(e)}")
            return {}

    def _clean_energy_project_history(self, value: str) -> str:
        """Clean up energy project history format from Python list to clean bullet points."""
        try:
            # Remove Python list brackets and quotes
            if value.startswith('[') and value.endswith(']'):
                # Extract content from list format
                import re
                # Remove outer brackets
                content = value[1:-1]
                # Split by quotes and commas, extract bullet point content
                bullets = []

                # Use regex to find quoted strings that contain bullet points
                bullet_pattern = r"'([^']*•[^']*?)'"
                matches = re.findall(bullet_pattern, content)

                for match in matches:
                    # Clean up each bullet point
                    bullet = match.strip()
                    # Remove URLs and citations
                    bullet = re.sub(r'\([^)]*\)', '', bullet)  # Remove parenthetical citations
                    bullet = re.sub(r'https?://[^\s)]+', '', bullet)  # Remove URLs
                    bullet = bullet.strip()
                    if bullet:
                        bullets.append(bullet)

                # Join with newlines
                if bullets:
                    return '\n'.join(bullets)

            # If not in list format, clean up any URLs/citations
            import re
            cleaned = re.sub(r'\([^)]*\)', '', value)  # Remove parenthetical citations
            cleaned = re.sub(r'https?://[^\s)]+', '', cleaned)  # Remove URLs
            return cleaned.strip()

        except Exception as e:
            logger.warning(f"⚠️ Could not clean energy project history: {str(e)}")
            # Return as-is if cleaning fails
            return value

    def _clean_local_sports_team(self, value: str) -> str:
        """Clean up local sports team format from JSON object to simple team names."""
        try:
            result = value

            # If it's a JSON object, extract team names
            if '{' in value and '}' in value:
                import re
                # Extract any team names from JSON-like format (look for common patterns)
                # Match team names that end with common sports team suffixes
                team_suffixes = r'(?:Angels|Astros|Athletics|Blue Jays|Brewers|Cardinals|Cubs|Diamondbacks|Dodgers|Giants|Indians|Guardians|Mariners|Marlins|Mets|Nationals|Orioles|Padres|Phillies|Pirates|Rangers|Rays|Red Sox|Reds|Rockies|Royals|Tigers|Twins|White Sox|Yankees|Braves)'
                team_suffixes += r'|(?:Hawks|Celtics|Nets|Hornets|Bulls|Cavaliers|Mavericks|Nuggets|Pistons|Warriors|Rockets|Pacers|Clippers|Lakers|Grizzlies|Heat|Bucks|Timberwolves|Pelicans|Knicks|Thunder|Magic|76ers|Suns|Trail Blazers|Kings|Spurs|Raptors|Jazz|Wizards)'
                team_suffixes += r'|(?:Falcons|Bills|Panthers|Bears|Bengals|Browns|Cowboys|Broncos|Lions|Packers|Texans|Colts|Jaguars|Chiefs|Raiders|Chargers|Rams|Dolphins|Vikings|Patriots|Saints|Giants|Jets|Eagles|Steelers|49ers|Seahawks|Buccaneers|Titans|Commanders|Cardinals)'
                team_suffixes += r'|(?:Ducks|Coyotes|Bruins|Sabres|Flames|Hurricanes|Blackhawks|Avalanche|Blue Jackets|Stars|Red Wings|Oilers|Panthers|Kings|Wild|Canadiens|Predators|Devils|Islanders|Rangers|Senators|Flyers|Penguins|Blues|Sharks|Kraken|Lightning|Maple Leafs|Canucks|Golden Knights|Capitals|Jets)'
                team_suffixes += r'|(?:United|FC|City|Galaxy|Fire|Revolution|Impact|Crew|Union|Red Bulls|Orlando City|Atlanta United|LAFC|Sounders|Timbers|Rapids|Sporting KC|Real Salt Lake|Whitecaps)'

                team_pattern = f"'([^']*(?:{team_suffixes})[^']*)'"
                matches = re.findall(team_pattern, value)
                if matches:
                    result = ', '.join(matches)
                else:
                    # Fallback: extract any quoted strings that look like team names
                    fallback_pattern = r"'([A-Z][^']*(?:FC|United|City|Team|Club)[^']*)'"
                    fallback_matches = re.findall(fallback_pattern, value)
                    if fallback_matches:
                        result = ', '.join(fallback_matches)

            # Truncate to 255 characters to fit Salesforce field limit
            if len(result) > 255:
                result = result[:252] + '...'
                logger.warning(f"⚠️ Truncated local sports team to 255 characters: {result}")

            return result

        except Exception as e:
            logger.warning(f"⚠️ Could not clean local sports team: {str(e)}")
            # Ensure even error fallback respects character limit
            return value[:255] if len(value) > 255 else value

    def _refine_rapport_summaries(self, data: Dict[str, str], first_name: str) -> Dict[str, str]:
        """Refine rapport summaries to be more conversational and friendly."""
        try:
            logger.info("🎨 Refining rapport summaries to be more conversational...")

            # Extract rapport summaries for refinement
            rapport_fields = ['rapport_summary', 'rapport_summary_2', 'rapport_summary_3', 'rapport_summary_4']
            summaries_to_refine = {}

            for field in rapport_fields:
                if field in data and data[field]:
                    summaries_to_refine[field] = data[field]

            if not summaries_to_refine:
                logger.info("⚠️ No rapport summaries to refine")
                return data

            # Create refinement prompt
            summaries_text = "\n".join([f"- {field}: {summary}" for field, summary in summaries_to_refine.items()])

            prompt = f"""You are reviewing rapport-building email opening sentences to make them more conversational and friendly.

Contact's first name: {first_name}

Current rapport summaries (too formal/robotic):
{summaries_text}

Please refine these to be more conversational, as if speaking to a friend or colleague you respect. Guidelines:
1. Use more natural, casual language while remaining professional
2. Make them sound like genuine personal observations, not formal announcements
3. Use "I noticed" or "I saw" instead of direct statements
4. Keep the core facts but present them more warmly
5. Maintain the same themes but with a friendlier tone
6. Keep each refined summary to 1-2 sentences maximum
7. IMPORTANT: Remove overly specific details that sound unnatural in conversation:
   - Remove full years from dates (say "October 7" not "October 7, 2025")
   - Remove specific rankings unless they're really impressive (top 10, etc.)
   - Remove formal citations or reference numbers
   - Remove overly technical jargon or formal titles

Examples of good transformation:
❌ "Congratulations on Cleveland Clinic's recognition as a top workplace in healthcare, ranking 37th among large companies in the Fortune 2024 list."
✅ "I noticed the recognition your team at Cleveland Clinic got - congratulations!"

❌ "Your leadership in implementing energy-efficient infrastructure projects has significantly contributed to operational success."
✅ "I came across some of the energy projects you've been leading - really impressive work on the infrastructure side."

❌ "With the Chicago Bulls game on October 7, 2025, it's an exciting time for basketball fans in Chicago."
✅ "Hope you're excited about the Bulls game this weekend!"

❌ "The $2.3 million HVAC modernization project completed in Q3 2024 demonstrates your commitment to infrastructure excellence."
✅ "I saw the HVAC upgrades you completed recently - nice work on modernizing the infrastructure."

Format as JSON with these exact keys:
- rapport_summary: Refined version of the professional recognition summary
- rapport_summary_2: Refined version of the shared professional interest summary
- rapport_summary_3: Refined version of the company-specific observation summary
- rapport_summary_4: Refined version of the local/regional connection summary

Make them warm, genuine, and conversational while keeping the same core information."""

            # Define expected fields for validation
            expected_fields = list(summaries_to_refine.keys())

            # Use no-web-search API call with GPT-4o for better language refinement
            refined_data = self._make_api_call_no_web_search(prompt, expected_fields, max_retries=2)

            if refined_data:
                # Update the original data with refined summaries
                for field, refined_summary in refined_data.items():
                    if field in data:
                        data[field] = refined_summary
                        logger.info(f"   ✅ Refined {field}")
                logger.info(f"✅ Successfully refined {len(refined_data)} rapport summaries")
            else:
                logger.warning("⚠️ Failed to refine rapport summaries, keeping originals")

            return data

        except Exception as e:
            logger.error(f"❌ Error refining rapport summaries: {str(e)}")
            return data

    def _refine_summary_why_care(self, data: Dict[str, str], first_name: str, company: str) -> Dict[str, str]:
        """Refine summary_why_care to be conversational with proper company name formatting."""
        try:
            if 'summary_why_care' not in data or not data['summary_why_care']:
                return data

            logger.info("🎨 Refining summary_why_care to be more conversational...")

            current_summary = data['summary_why_care']

            prompt = f"""You are reviewing an email opening sentence to make it more conversational and natural.

Contact's first name: {first_name}
Company name: {company}

Current sentence (too formal/robotic):
{current_summary}

Please refine this to be more conversational and natural. Guidelines:
1. Use natural, casual language while remaining professional
2. Format the company name conversationally (not all caps, no LLC/Inc/Corp suffixes)
3. Make it sound like genuine personal observation, not a formal statement
4. Use "I'm sure" or "I imagine" to soften the approach
5. Keep it to 1-2 sentences maximum
6. Remove overly formal language or corporate jargon
7. Make the company name sound natural in conversation

Examples of good company name formatting:
❌ "CLEVELAND CLINIC HEALTH SYSTEM" → ✅ "Cleveland Clinic"
❌ "BOZEMAN HEALTH DEACONESS REGIONAL MEDICAL CENTER" → ✅ "Bozeman Health"
❌ "ST. VINCENT HEALTHCARE, LLC" → ✅ "St. Vincent Healthcare"
❌ "Providence Health & Services, Inc." → ✅ "Providence Health"

Examples of conversational tone:
❌ "As the Chief Financial Officer at ACME CORPORATION, I am certain you have experienced challenges with energy costs representing a significant operational expense."
✅ "In your role as CFO at Acme, I'm sure you've faced challenges with energy being a top operating cost."

❌ "Given your position as Senior Director, Facilities Operations at MEMORIAL HOSPITAL SYSTEM, you have undoubtedly encountered difficulties with aging infrastructure and emergency repairs."
✅ "I imagine as Senior Director of Facilities at Memorial Hospital, you've dealt with constant firefighting with old equipment and emergency repairs."

Format as JSON with this exact key:
- summary_why_care: Refined conversational version with proper company name formatting

Make it warm, genuine, and conversational while keeping the same core pain points."""

            # Use no-web-search API call with GPT-4o for better language refinement
            refined_data = self._make_api_call_no_web_search(prompt, ['summary_why_care'], max_retries=2)

            if refined_data and 'summary_why_care' in refined_data:
                data['summary_why_care'] = refined_data['summary_why_care']
                logger.info(f"   ✅ Refined summary_why_care")
                logger.info(f"   Original: {current_summary[:80]}...")
                logger.info(f"   Refined:  {refined_data['summary_why_care'][:80]}...")
            else:
                logger.warning("⚠️ Failed to refine summary_why_care, keeping original")

            return data

        except Exception as e:
            logger.error(f"❌ Error refining summary_why_care: {str(e)}")
            return data

    def _validate_response_data(self, data: Dict[str, str], expected_fields: List[str]) -> bool:
        """Validate that response data contains expected fields with reasonable content."""
        if not data:
            return False

        # Check if we have at least some of the expected fields
        found_fields = [field for field in expected_fields if field in data and data[field]]

        # Require at least 50% of expected fields to be present
        min_required = max(1, len(expected_fields) // 2)

        if len(found_fields) < min_required:
            logger.warning(f"⚠️ Validation failed: Only {len(found_fields)}/{len(expected_fields)} expected fields found")
            return False

        # Use our comprehensive field validator for each field
        valid_field_count = 0
        for field, value in data.items():
            if field in expected_fields:
                if FieldValidator.is_valid_field_value(value, field):
                    valid_field_count += 1
                else:
                    logger.warning(f"⚠️ Field '{field}' failed validation: {str(value)[:50]}...")

        # Require at least some valid fields
        if valid_field_count < min_required:
            logger.warning(f"⚠️ Validation failed: Only {valid_field_count}/{len(expected_fields)} fields passed validation")
            return False

        logger.info(f"✅ Validation passed: {valid_field_count}/{len(expected_fields)} fields validated")
        return True

    def _make_api_call_with_retry(self, prompt: str, expected_fields: List[str], max_retries: int = 2) -> Dict[str, str]:
        """Make API call with retry logic and validation."""
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 API call attempt {attempt + 1}/{max_retries}")

                response = self.openai_client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    web_search_options={},
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )

                content = response.choices[0].message.content
                extracted_data = self._extract_json_from_response(content)

                # Validate the response
                if self._validate_response_data(extracted_data, expected_fields):
                    logger.info(f"✅ API call successful on attempt {attempt + 1}")
                    return extracted_data
                else:
                    logger.warning(f"⚠️ Validation failed on attempt {attempt + 1}, retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Brief delay before retry

            except Exception as e:
                logger.error(f"❌ API call failed on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Longer delay on error

        logger.error(f"❌ All {max_retries} attempts failed, returning empty data")
        return {}

    def _make_api_call_no_web_search(self, prompt: str, expected_fields: List[str], max_retries: int = 2) -> Dict[str, str]:
        """Make API call WITHOUT web search using GPT-4o for text refinement tasks."""
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 API call (no web search) attempt {attempt + 1}/{max_retries}")

                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",  # Use GPT-4o for better language refinement
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.7  # Slightly more creative for conversational tone
                )

                content = response.choices[0].message.content
                extracted_data = self._extract_json_from_response(content)

                # Validate the response
                if self._validate_response_data(extracted_data, expected_fields):
                    logger.info(f"✅ API call (no web search) successful on attempt {attempt + 1}")
                    return extracted_data
                else:
                    logger.warning(f"⚠️ Validation failed on attempt {attempt + 1}, retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Brief delay before retry

            except Exception as e:
                logger.error(f"❌ API call (no web search) failed on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Longer delay on error

        logger.error(f"❌ All {max_retries} attempts failed, returning empty data")
        return {}

    def update_contact_fields(self, contact_id: str, field_data: Dict[str, str]) -> bool:
        """Update contact fields in Salesforce with field validation."""
        try:
            logger.info(f"💾 Updating contact {contact_id} with enriched data...")

            # First, clean the field data using our validator
            logger.info(f"🧹 Validating {len(field_data)} fields before Salesforce update...")
            cleaned_field_data = FieldValidator.clean_field_data(field_data, self.FIELD_MAPPING)
            
            if len(cleaned_field_data) < len(field_data):
                removed_count = len(field_data) - len(cleaned_field_data)
                logger.warning(f"🛑 Filtered out {removed_count} invalid fields before update")

            update_data = {}

            for field_key, value in cleaned_field_data.items():
                if value and value.strip() and field_key in self.FIELD_MAPPING:
                    salesforce_field = self.FIELD_MAPPING[field_key]
                    
                    # Final validation before adding to update_data
                    if FieldValidator.is_valid_field_value(value, field_key):
                        update_data[salesforce_field] = value
                        logger.info(f"   ✅ Will update {field_key} -> {salesforce_field}")
                    else:
                        logger.warning(f"   🛑 BLOCKED {field_key}: Failed final validation")

            if not update_data:
                logger.warning("⚠️ No valid fields to update after validation")
                return True

            # Final safety check on the Salesforce update data
            validated_update_data = FieldValidator.validate_salesforce_update_data(update_data)
            
            if len(validated_update_data) < len(update_data):
                blocked_count = len(update_data) - len(validated_update_data)
                logger.warning(f"🛑 Final safety check blocked {blocked_count} additional fields")

            if not validated_update_data:
                logger.warning("⚠️ No fields passed final validation - skipping Salesforce update")
                return True

            self.sf.Contact.update(contact_id, validated_update_data)
            logger.info(f"✅ Successfully updated {len(validated_update_data)} validated fields")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update contact: {str(e)}")
            return False

    async def run_linkedin_enricher(self, record_id: str) -> bool:
        """
        Run LinkedIn enricher to find and scrape LinkedIn profile data.
        
        Args:
            record_id: Salesforce Contact Record ID
            
        Returns:
            True if enrichment succeeded or was skipped, False on error
        """
        try:
            if not self.linkedin_enricher:
                logger.warning("⚠️ LinkedIn enricher not available - skipping")
                return True
            
            logger.info(f"🔗 Running LinkedIn enricher for contact: {record_id}")
            
            # Run the LinkedIn enrichment process (both steps)
            success = await self.linkedin_enricher.process_contact_enrichment(record_id)
            
            if success:
                logger.info("✅ LinkedIn enrichment completed successfully")
            else:
                logger.warning("⚠️ LinkedIn enrichment did not complete successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error running LinkedIn enricher: {str(e)}")
            return False

    async def process_contact_enrichment(self, record_id: str, overwrite: bool = False, 
                                        include_linkedin: bool = False) -> bool:
        """Main method to perform web search contact enrichment with optional LinkedIn enrichment."""
        try:
            logger.info(f"🚀 Starting contact enrichment for record ID: {record_id}")
            logger.info(f"🔧 Overwrite mode: {'ON' if overwrite else 'OFF (empty fields only)'}")
            if include_linkedin:
                logger.info(f"🔗 LinkedIn enrichment: ENABLED")

            # 1. Get contact details
            contact = self.get_contact_details(record_id)
            if not contact:
                logger.error(f"❌ Cannot proceed: Contact not found for {record_id}")
                return False

            first_name = contact.get('FirstName', '')
            last_name = contact.get('LastName', '')
            company = contact.get('account_name', '')
            title = contact.get('Title', '')

            logger.info(f"📋 Contact details:")
            logger.info(f"   Name: {first_name} {last_name}")
            logger.info(f"   Company: {company}")
            logger.info(f"   Title: {title}")

            # 2. Run LinkedIn enricher FIRST if requested (populates LinkedIn profile data)
            if include_linkedin:
                logger.info("\n📊 Step 1: Running LinkedIn enricher...")
                # Setup LinkedIn enricher if not already done
                if not self.linkedin_enricher:
                    self._setup_linkedin_enricher()
                
                if self.linkedin_enricher:
                    linkedin_success = await self.run_linkedin_enricher(record_id)
                    if linkedin_success:
                        logger.info("✅ LinkedIn enrichment completed - profile data populated")
                        # Refresh contact details to get updated fields
                        contact = self.get_contact_details(record_id)
                    else:
                        logger.warning("⚠️ LinkedIn enrichment did not succeed")
                    
                    time.sleep(1)  # Rate limiting between enrichers

            # 3. Run web search enrichment (personalized rapport and campaign fields)
            step_number = 2 if include_linkedin else 1
            logger.info(f"\n📊 Step {step_number}: Running web search enrichment for personalized fields...")

            # 4. Check which fields can be updated by section
            updatable_sections = self.check_updatable_fields(contact, overwrite)

            if not updatable_sections:
                logger.info("✅ All web search fields already have data. Use --overwrite to update anyway.")
                return True

            # 6. Process each section with web searches
            all_enriched_data = {}

            # Process Personalized Rapport
            if 'personalized_rapport' in updatable_sections:
                logger.info("\n🔍 Processing Personalized Rapport section...")
                rapport_data = self.search_general_information(contact)
                all_enriched_data.update(rapport_data)
                time.sleep(2)  # Rate limiting

            # Process Work Experience
            if 'work_experience' in updatable_sections:
                logger.info("\n🔍 Processing Work Experience section...")
                work_data = self.search_work_experience(contact)
                all_enriched_data.update(work_data)
                time.sleep(2)  # Rate limiting

            # Process Email Customization (uses previous data for context)
            if 'email_customization' in updatable_sections:
                logger.info("\n📧 Processing Email Customization section...")
                email_data = self.generate_email_campaigns(contact, all_enriched_data)
                all_enriched_data.update(email_data)
                time.sleep(1)

            # Note: Standard fields (Title, Department, Description) and contact info
            # (LinkedIn profile data, phones, education, location) can be handled by LinkedIn enricher

            # 7. Filter and validate data before updating
            logger.info(f"🧹 Validating enriched data before update...")
            
            # First, filter to only include updatable fields
            all_updatable_fields = []
            for fields in updatable_sections.values():
                all_updatable_fields.extend(fields)

            filtered_data = {}
            for field_key, value in all_enriched_data.items():
                if field_key in all_updatable_fields and value and value.strip():
                    filtered_data[field_key] = value

            if not filtered_data:
                logger.warning("⚠️ No enriched data to update")
                return True
            
            # Apply field validation to remove invalid responses
            update_field_data = FieldValidator.clean_field_data(filtered_data, self.FIELD_MAPPING)
            
            if len(update_field_data) < len(filtered_data):
                removed_count = len(filtered_data) - len(update_field_data)
                logger.warning(f"🛑 Validation removed {removed_count} fields with invalid data")

            if not update_field_data:
                logger.warning("⚠️ No valid enriched data to update after validation")
                return True

            # 8. Show preview
            logger.info("\n📝 Enrichment results preview:")
            logger.info("-" * 60)
            for field_key, value in update_field_data.items():
                preview = value[:100] + "..." if len(value) > 100 else value
                logger.info(f"{field_key}: {preview}")
            logger.info("-" * 60)

            # 9. Confirm before updating
            try:
                user_input = input(f"\nUpdate {len(update_field_data)} fields in Salesforce? (Y/n): ")
                if user_input.lower() in ['n', 'no']:
                    logger.info("✅ Enrichment cancelled per user request")
                    return True
            except EOFError:
                logger.info("🤖 Automated mode: Proceeding with update")

            # 10. Update the contact
            success = self.update_contact_fields(contact['Id'], update_field_data)

            if success:
                logger.info("✅ Contact enrichment completed successfully")
                logger.info(f"📊 Updated {len(update_field_data)} web search fields in Salesforce")
                if include_linkedin:
                    logger.info("🔗 LinkedIn fields also enriched")
            else:
                logger.error("❌ Failed to update contact fields")

            return success

        except Exception as e:
            logger.error(f"❌ Error processing contact enrichment: {str(e)}")
            return False


async def main_async():
    """Main async function to run the script."""
    parser = argparse.ArgumentParser(description='Web Search Salesforce Contact Enricher')
    parser.add_argument('record_id', help='Salesforce Contact Record ID')
    parser.add_argument('--overwrite', action='store_true',
                       help='Update all fields including those with existing data')
    parser.add_argument('--include-linkedin', action='store_true',
                       help='Include LinkedIn profile scraping (Full LinkedIn Data field)')

    args = parser.parse_args()

    try:
        enricher = WebSearchContactEnricher()
        success = await enricher.process_contact_enrichment(
            args.record_id, 
            args.overwrite,
            args.include_linkedin
        )

        if success:
            print(f"\n✅ Successfully processed contact: {args.record_id}")
            if args.overwrite:
                print("🔧 Used overwrite mode - updated all fields")
            else:
                print("🛡️ Safe mode - only updated empty fields")
            if args.include_linkedin:
                print("🔗 Included LinkedIn enrichment")
        else:
            print(f"\n❌ Failed to process contact: {args.record_id}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Script failed: {str(e)}")
        sys.exit(1)


def main():
    """Main function wrapper to run async main."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()