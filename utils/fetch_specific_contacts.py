"""
Fetch specific Salesforce contacts for documentation
"""
import asyncio
import json
from dotenv import load_dotenv
from app.services.salesforce import salesforce_service

async def fetch_specific_contacts():
    """Fetch specific contacts by ID from Salesforce with all fields"""

    # Specific contact IDs to fetch
    contact_ids = [
        "003VR00000ZPZV5YAP",
        "003VR00000ZPakDYAT",
        "003VR00000ZPVz1YAH"
    ]

    # Connect to Salesforce
    print("Connecting to Salesforce...")
    success = await salesforce_service.connect()
    if not success:
        print("Failed to connect to Salesforce")
        return

    print("Connected successfully!\n")

    # Fetch each contact
    print("Fetching specific contacts...\n")
    for i, contact_id in enumerate(contact_ids, 1):
        try:
            # Query contact with all fields
            contact_query = f"""
                SELECT FIELDS(ALL)
                FROM Contact
                WHERE Id = '{contact_id}'
            """

            result = salesforce_service.sf.query(contact_query)

            if result['totalSize'] > 0:
                contact = result['records'][0]

                # Save contact
                filename = f"example_objects/contact_example_{i}.json"
                with open(filename, 'w') as f:
                    json.dump(contact, f, indent=2, default=str)

                print(f"✅ Saved: {filename}")
                print(f"   ID: {contact_id}")
                print(f"   Name: {contact.get('FirstName', '')} {contact.get('LastName', 'Unknown')}")
                print(f"   Title: {contact.get('Title', 'N/A')}")
                print(f"   Email: {contact.get('Email', 'N/A')}")
                print()
            else:
                print(f"❌ Contact not found: {contact_id}\n")

        except Exception as e:
            print(f"❌ Error fetching contact {contact_id}: {e}\n")

    print("✨ Complete! Specific contacts saved to example_objects/ folder")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Run the async function
    asyncio.run(fetch_specific_contacts())
