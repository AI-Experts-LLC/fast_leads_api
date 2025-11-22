"""
Step-by-step manual test for Hybrid Pipeline
Allows you to test each step individually and inspect results
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

TEST_COMPANY = {
    "company_name": "Portneuf Medical Center",
    "company_city": "Pocatello",
    "company_state": "Idaho"
}

print("\n" + "="*80)
print("HYBRID PIPELINE - STEP-BY-STEP TEST")
print("="*80)
print(f"\nCompany: {TEST_COMPANY['company_name']}")
print(f"Location: {TEST_COMPANY['company_city']}, {TEST_COMPANY['company_state']}")

# Check server health
print("\n" + "-"*80)
print("Checking server health...")
try:
    health = requests.get(f"{BASE_URL}/health", timeout=5)
    if health.status_code == 200:
        print("✅ Server is online")
    else:
        print(f"⚠️ Server returned status {health.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Server is not running: {e}")
    print("\nPlease start the server with: hypercorn main:app --reload")
    exit(1)

# STEP 1
print("\n" + "="*80)
print("STEP 1: Parallel Search (Serper + Bright Data)")
print("="*80)
print("\nThis will take 30-90 seconds...")
print("Press Ctrl+C to cancel\n")

start = time.time()
try:
    response1 = requests.post(
        f"{BASE_URL}/discover-leads-step1",
        json=TEST_COMPANY,
        timeout=180
    )
    duration1 = time.time() - start

    print(f"✅ Completed in {duration1:.1f}s")
    print(f"Status: {response1.status_code}")

    if response1.status_code == 200:
        result1 = response1.json()
        data1 = result1.get("data", {})
        summary = data1.get("summary", {})

        print(f"\nResults:")
        print(f"  Serper: {summary.get('serper_count', 0)} prospects")
        print(f"  Bright Data: {summary.get('brightdata_count', 0)} prospects")

        # Save to file
        with open("/tmp/hybrid_step1_result.json", "w") as f:
            json.dump(data1, f, indent=2)
        print(f"\n💾 Results saved to: /tmp/hybrid_step1_result.json")

        # Ask to continue
        print("\n" + "-"*80)
        cont = input("Continue to Step 2? (y/n): ")
        if cont.lower() != 'y':
            print("Exiting...")
            exit(0)

        # STEP 2
        print("\n" + "="*80)
        print("STEP 2: Deduplicate + Enrich")
        print("="*80)
        print("\nThis will take 15-30 seconds...")

        start = time.time()
        response2 = requests.post(
            f"{BASE_URL}/discover-leads-step2",
            json={
                "serper_prospects": data1.get("serper_prospects", []),
                "brightdata_prospects": data1.get("brightdata_prospects", []),
                "company_name": TEST_COMPANY["company_name"],
                "company_city": TEST_COMPANY["company_city"],
                "company_state": TEST_COMPANY["company_state"]
            },
            timeout=180
        )
        duration2 = time.time() - start

        print(f"✅ Completed in {duration2:.1f}s")
        print(f"Status: {response2.status_code}")

        if response2.status_code == 200:
            result2 = response2.json()
            data2 = result2.get("data", {})
            summary = data2.get("summary", {})

            print(f"\nResults:")
            print(f"  Bright Data: {summary.get('brightdata_count', 0)} prospects")
            print(f"  Serper enriched: {summary.get('serper_enriched_count', 0)} prospects")
            print(f"  Duplicates skipped: {summary.get('duplicates_skipped', 0)} prospects")
            print(f"  Total enriched: {summary.get('total_enriched', 0)} prospects")

            # Save to file
            with open("/tmp/hybrid_step2_result.json", "w") as f:
                json.dump(data2, f, indent=2)
            print(f"\n💾 Results saved to: /tmp/hybrid_step2_result.json")

            # Ask to continue
            print("\n" + "-"*80)
            cont = input("Continue to Step 3? (y/n): ")
            if cont.lower() != 'y':
                print("Exiting...")
                exit(0)

            # STEP 3
            print("\n" + "="*80)
            print("STEP 3: AI Ranking & Qualification")
            print("="*80)
            print("\nThis will take 10-20 seconds...")

            start = time.time()
            response3 = requests.post(
                f"{BASE_URL}/discover-leads-step3",
                json={
                    "enriched_prospects": data2.get("enriched_prospects", []),
                    "company_name": TEST_COMPANY["company_name"],
                    "min_score_threshold": 65,
                    "max_prospects": 10
                },
                timeout=180
            )
            duration3 = time.time() - start

            print(f"✅ Completed in {duration3:.1f}s")
            print(f"Status: {response3.status_code}")

            if response3.status_code == 200:
                result3 = response3.json()
                data3 = result3.get("data", {})
                qualified = data3.get("qualified_prospects", [])

                print(f"\nResults:")
                print(f"  Qualified prospects: {len(qualified)}")

                if qualified:
                    print("\n  Top 5 Qualified Prospects:")
                    for i, prospect in enumerate(qualified[:5], 1):
                        ld = prospect.get("linkedin_data", {})
                        ai = prospect.get("ai_ranking", {})
                        name = ld.get("name", "Unknown")
                        title = ld.get("job_title", "Unknown")
                        score = ai.get("score", 0)
                        print(f"    {i}. {name} - {title} (Score: {score})")

                # Save to file
                with open("/tmp/hybrid_step3_result.json", "w") as f:
                    json.dump(data3, f, indent=2)
                print(f"\n💾 Results saved to: /tmp/hybrid_step3_result.json")

                # Ask to continue
                print("\n" + "-"*80)
                cont = input("Continue to Step 4 (Queue Leads)? (y/n): ")
                if cont.lower() != 'y':
                    print("Exiting...")
                    exit(0)

                # STEP 4
                print("\n" + "="*80)
                print("STEP 4: Queue Leads for Approval")
                print("="*80)
                print("\nThis will take 1-2 seconds...")

                start = time.time()
                response4 = requests.post(
                    f"{BASE_URL}/discover-leads-step4",
                    json={
                        "qualified_prospects": qualified,
                        "company_name": TEST_COMPANY["company_name"]
                    },
                    timeout=60
                )
                duration4 = time.time() - start

                print(f"✅ Completed in {duration4:.1f}s")
                print(f"Status: {response4.status_code}")

                if response4.status_code == 200:
                    result4 = response4.json()
                    data4 = result4.get("data", {})

                    print(f"\nResults:")
                    print(f"  Queued: {data4.get('queued', 0)} leads")
                    print(f"  Failed: {data4.get('failed', 0)} leads")
                    print(f"  Total: {data4.get('total', 0)} leads")

                    print("\n" + "="*80)
                    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
                    print("="*80)
                    print(f"\nTotal Time: {duration1 + duration2 + duration3 + duration4:.1f}s")
                    print(f"  Step 1: {duration1:.1f}s")
                    print(f"  Step 2: {duration2:.1f}s")
                    print(f"  Step 3: {duration3:.1f}s")
                    print(f"  Step 4: {duration4:.1f}s")
                    print(f"\n📊 View leads at: {BASE_URL}/dashboard")
                    print(f"📋 Pending updates: {BASE_URL}/pending-updates?record_type=Lead")
                else:
                    print(f"\n❌ Step 4 failed:")
                    print(response4.text)
            else:
                print(f"\n❌ Step 3 failed:")
                print(response3.text)
        else:
            print(f"\n❌ Step 2 failed:")
            print(response2.text)
    else:
        print(f"\n❌ Step 1 failed:")
        print(response1.text)

except KeyboardInterrupt:
    print("\n\n⚠️ Test cancelled by user")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Test complete!")
print("="*80 + "\n")
