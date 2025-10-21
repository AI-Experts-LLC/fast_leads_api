"""
Analyze example Salesforce objects to generate field summaries
"""
import json
import glob
from collections import defaultdict

def analyze_fields(object_type):
    """Analyze fields from example objects"""
    files = glob.glob(f"example_objects/{object_type}_example_*.json")

    all_fields = defaultdict(set)
    field_types = {}

    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)

            for field, value in data.items():
                if field == 'attributes':
                    continue

                # Track field presence
                all_fields[field].add(file)

                # Track field type
                if field not in field_types:
                    field_types[field] = type(value).__name__

    return all_fields, field_types, len(files)

def main():
    print("=" * 80)
    print("SALESFORCE OBJECT FIELD ANALYSIS")
    print("=" * 80)

    # Analyze accounts
    print("\n📊 ACCOUNT FIELDS\n")
    account_fields, account_types, account_count = analyze_fields("account")
    print(f"Total accounts analyzed: {account_count}")
    print(f"Total unique fields: {len(account_fields)}")

    # Categorize account fields
    standard_fields = []
    custom_fields = []

    for field in sorted(account_fields.keys()):
        if field.endswith('__c'):
            custom_fields.append(field)
        else:
            standard_fields.append(field)

    print(f"\nStandard fields: {len(standard_fields)}")
    print(f"Custom fields: {len(custom_fields)}")

    # Show custom fields (Metrus specific)
    print("\n🔧 Custom Fields (Metrus Energy Specific):")
    for field in custom_fields[:20]:  # First 20
        print(f"  - {field} ({account_types[field]})")
    if len(custom_fields) > 20:
        print(f"  ... and {len(custom_fields) - 20} more")

    # Analyze contacts
    print("\n" + "=" * 80)
    print("\n👤 CONTACT FIELDS\n")
    contact_fields, contact_types, contact_count = analyze_fields("contact")
    print(f"Total contacts analyzed: {contact_count}")
    print(f"Total unique fields: {len(contact_fields)}")

    # Categorize contact fields
    standard_fields = []
    custom_fields = []

    for field in sorted(contact_fields.keys()):
        if field.endswith('__c'):
            custom_fields.append(field)
        else:
            standard_fields.append(field)

    print(f"\nStandard fields: {len(standard_fields)}")
    print(f"Custom fields: {len(custom_fields)}")

    # Show custom fields
    print("\n🔧 Custom Fields (Metrus Energy Specific):")
    for field in custom_fields:
        print(f"  - {field} ({contact_types[field]})")

    # Save field lists to text files
    with open("example_objects/account_fields.txt", 'w') as f:
        f.write("ACCOUNT FIELDS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total: {len(account_fields)} fields\n\n")

        f.write(f"STANDARD FIELDS ({len(standard_fields)}):\n")
        f.write("-" * 80 + "\n")
        for field in sorted([f for f in account_fields.keys() if not f.endswith('__c')]):
            f.write(f"{field}: {account_types[field]}\n")

        f.write(f"\n\nCUSTOM FIELDS ({len(custom_fields)}):\n")
        f.write("-" * 80 + "\n")
        for field in sorted([f for f in account_fields.keys() if f.endswith('__c')]):
            f.write(f"{field}: {account_types[field]}\n")

    with open("example_objects/contact_fields.txt", 'w') as f:
        f.write("CONTACT FIELDS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total: {len(contact_fields)} fields\n\n")

        standard = [f for f in contact_fields.keys() if not f.endswith('__c')]
        custom = [f for f in contact_fields.keys() if f.endswith('__c')]

        f.write(f"STANDARD FIELDS ({len(standard)}):\n")
        f.write("-" * 80 + "\n")
        for field in sorted(standard):
            f.write(f"{field}: {contact_types[field]}\n")

        f.write(f"\n\nCUSTOM FIELDS ({len(custom)}):\n")
        f.write("-" * 80 + "\n")
        for field in sorted(custom):
            f.write(f"{field}: {contact_types[field]}\n")

    print("\n" + "=" * 80)
    print("\n✅ Field lists saved:")
    print("   - example_objects/account_fields.txt")
    print("   - example_objects/contact_fields.txt")

if __name__ == "__main__":
    main()
