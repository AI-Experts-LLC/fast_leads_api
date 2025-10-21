"""
Fetch example Salesforce objects for documentation
Saves 3 accounts and 3 contacts to example_objects/ folder
"""
import asyncio
import json
from dotenv import load_dotenv
from app.services.salesforce import salesforce_service

async def fetch_example_objects():
    """Fetch 3 accounts and 3 contacts from Salesforce with all fields"""

    # Connect to Salesforce
    print("Connecting to Salesforce...")
    success = await salesforce_service.connect()
    if not success:
        print("Failed to connect to Salesforce")
        return

    print("Connected successfully!\n")

    # Get 3 accounts with all fields
    print("Fetching 3 example accounts...")
    accounts_query = """
        SELECT FIELDS(ALL)
        FROM Account
        WHERE Type = 'Customer'
        LIMIT 3
    """

    try:
        accounts_result = salesforce_service.sf.query(accounts_query)
        accounts = accounts_result['records']

        # Save each account
        for i, account in enumerate(accounts, 1):
            filename = f"example_objects/account_example_{i}.json"
            with open(filename, 'w') as f:
                json.dump(account, f, indent=2, default=str)
            print(f"✅ Saved: {filename}")
            print(f"   Account: {account.get('Name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error fetching accounts: {e}")

    print()

    # Get 3 contacts with all fields
    print("Fetching 3 example contacts...")
    contacts_query = """
        SELECT FIELDS(ALL)
        FROM Contact
        WHERE Email != null
        LIMIT 3
    """

    try:
        contacts_result = salesforce_service.sf.query(contacts_query)
        contacts = contacts_result['records']

        # Save each contact
        for i, contact in enumerate(contacts, 1):
            filename = f"example_objects/contact_example_{i}.json"
            with open(filename, 'w') as f:
                json.dump(contact, f, indent=2, default=str)
            print(f"✅ Saved: {filename}")
            print(f"   Contact: {contact.get('FirstName', '')} {contact.get('LastName', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error fetching contacts: {e}")

    print("\n✨ Complete! Example objects saved to example_objects/ folder")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Run the async function
    asyncio.run(fetch_example_objects())
