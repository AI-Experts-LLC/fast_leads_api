#!/usr/bin/env python3
"""
Direct test of AI title filter scoring
Test if AI correctly scores clinical vs facilities roles
"""
import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from app.prompts import AI_TITLE_FILTER_SYSTEM_PROMPT, AI_TITLE_FILTER_USER_PROMPT_TEMPLATE

load_dotenv()

# Test titles - should be rejected (score < 40)
CLINICAL_TITLES = [
    "Director Cardiovascular Service Line - St. Vincent Healthcare",
    "Director of Wound Care Clinic - St. Vincent Healthcare",
    "Director Cardiovascular Imaging - St. Vincent Healthcare",
    "Director of Radiology - St. Vincent Healthcare",
    "Director Emergency Department - St. Vincent Healthcare",
    "Chief of Surgery - St. Vincent Healthcare",
    "VP Nursing Services - St. Vincent Healthcare",
]

# Test titles - should pass (score >= 70)
FACILITIES_TITLES = [
    "Director of Facilities - St. Vincent Healthcare",
    "CFO - St. Vincent Healthcare",
    "VP Operations - St. Vincent Healthcare",
    "Energy Manager - St. Vincent Healthcare",
    "Director Physical Plant - St. Vincent Healthcare",
]

async def score_title(client, title, company_name):
    """Score a single title using AI"""
    prompt = AI_TITLE_FILTER_USER_PROMPT_TEMPLATE.format(
        company_name=company_name,
        title=title,
        snippet=title  # Use title as snippet for simplicity
    )

    full_input = f"{AI_TITLE_FILTER_SYSTEM_PROMPT}\n\n{prompt}"

    api_params = {
        "model": "gpt-5-mini-2025-08-07",
        "input": full_input,
        "text": {"format": {"type": "json_object"}},
        "max_output_tokens": 300,
        "timeout": 20,
        "reasoning": {"effort": "minimal"}
    }

    response = await client.responses.create(**api_params)

    import json

    # Check if response is valid
    if not response or not hasattr(response, 'output') or not response.output:
        print(f"ERROR: Invalid response structure")
        print(f"Response: {response}")
        return 0, "ERROR: Invalid response"

    try:
        # When reasoning is enabled, response.output has 2 items:
        # [0] = ResponseReasoningItem (thinking, content=None)
        # [1] = ResponseOutputMessage (actual response)
        # So we need to access the last item which contains the actual output
        output_item = response.output[-1]  # Get last item (the actual output message)
        output_text = output_item.content[0].text
    except (IndexError, AttributeError, TypeError) as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        print(f"Response.output: {response.output if hasattr(response, 'output') else 'NO OUTPUT'}")
        return 0, f"ERROR: {type(e).__name__}"

    result = json.loads(output_text)

    return result.get("score", 0), result.get("reasoning", "")

async def main():
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    company_name = "St. Vincent Healthcare"

    print("=" * 80)
    print("TESTING AI TITLE FILTER SCORING")
    print("=" * 80)
    print()

    print("CLINICAL TITLES (should score < 40):")
    print("-" * 80)
    for title in CLINICAL_TITLES:
        score, reasoning = await score_title(client, title, company_name)
        status = "✓ CORRECT" if score < 40 else "✗ WRONG"
        print(f"{status} | Score: {score:3d} | {title}")
        print(f"        Reasoning: {reasoning}")
        print()

    print()
    print("FACILITIES TITLES (should score >= 70):")
    print("-" * 80)
    for title in FACILITIES_TITLES:
        score, reasoning = await score_title(client, title, company_name)
        status = "✓ CORRECT" if score >= 70 else "✗ WRONG"
        print(f"{status} | Score: {score:3d} | {title}")
        print(f"        Reasoning: {reasoning}")
        print()

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
