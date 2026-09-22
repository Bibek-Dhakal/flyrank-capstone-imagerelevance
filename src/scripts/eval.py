import asyncio

import httpx

EVAL_DATASET = [
    {
        "title": "The clever Red Fox",
        "content": "Red foxes have a beautiful orange coat and a bushy tail. They roam the forests and fields.",
        "expected_category_or_subject": ["fox", "red fox"],
    },
    {
        "title": "Winter Wolves",
        "content": "Wolves travel in packs through the snow. They are formidable wild predators.",
        "expected_category_or_subject": ["wolf", "wolves"],
    },
    {
        "title": "Man's best friend",
        "content": "Domestic dogs make great pets. Beagles in particular are friendly and loveable.",
        "expected_category_or_subject": ["dog", "beagle", "puppy"],
    },
    {
        "title": "The Mighty Brown Bear",
        "content": "Brown bears can be found catching salmon in rivers. They are massive mammals.",
        "expected_category_or_subject": ["bear", "brown bear"],
    },
    {
        "title": "Graceful Deer",
        "content": "A deer with large antlers walking peacefully through the woods.",
        "expected_category_or_subject": ["deer", "buck"],
    },
    {
        "title": "Wild Tigers",
        "content": "Tigers are large cats with distinct striped coats, native to Asia.",
        "expected_category_or_subject": ["tiger", "cat"],
    },
    {
        "title": "Tall Giraffes",
        "content": "Giraffes use their long necks to eat leaves from tall trees in the savanna.",
        "expected_category_or_subject": ["giraffe"],
    },
    {
        "title": "Giant Elephants",
        "content": "Elephants are known for their large trunks and tusks.",
        "expected_category_or_subject": ["elephant"],
    },
    {
        "title": "Arctic Fox survival",
        "content": "Unlike the red fox, the arctic fox turns white in the winter to blend into the snow.",
        "expected_category_or_subject": ["arctic fox", "fox"],
    },
    {
        "title": "Black guard dogs",
        "content": "A black coated dog can look intimidating but often they are very loyal.",
        "expected_category_or_subject": ["dog"],
    },
]


async def run_evaluation():
    print(f"Starting Evaluation on {len(EVAL_DATASET)} posts...")
    correct_matches = 0
    total_processed = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for item in EVAL_DATASET:
            print(f"\nEvaluating: '{item['title']}'")

            # 1. Create Post
            post_req = await client.post(
                "http://localhost:8000/api/v1/posts/",
                json={"title": item["title"], "content": item["content"]},
            )
            if post_req.status_code != 200:
                print("Failed to create post. Skipping.")
                continue

            post_id = post_req.json()["id"]

            # Wait a tiny bit for DB consistency
            await asyncio.sleep(1)

            # 2. Get Match
            match_req = await client.get(f"http://localhost:8000/api/v1/posts/{post_id}/images")
            if match_req.status_code != 200:
                print(f"Failed to match: {match_req.text}")
                continue

            match_data = match_req.json()
            status = match_data["status"]
            reason = match_data["reason"]
            tags = match_data.get("image_tags") or {}

            print(f"  Result Status: {status}")
            print(f"  Reason: {reason}")

            if status == "ACCEPTED" and tags:
                subject = str(tags.get("subject", "")).lower()
                category = str(tags.get("category", "")).lower()

                # Check if expected tags are in the AI's tags
                expected_list = item["expected_category_or_subject"]
                is_correct = any(expected in subject for expected in expected_list) or any(
                    expected in category for expected in expected_list
                )

                if is_correct:
                    print("  Verdict: CORRECT MATCH ✅")
                    correct_matches += 1
                else:
                    print(
                        f"  Verdict: WRONG MATCH ❌ (Expected {expected_list}, got {subject}/{category})"
                    )
            else:
                print("  Verdict: NO MATCH FOUND ⚠️ (Or Guard Rejected)")

            total_processed += 1

            # Throttle to respect Gemini Free Tier rate limits (15-20 RPM max)
            print("  Throttling for 4 seconds to respect API rate limits...")
            await asyncio.sleep(4)

    precision = (correct_matches / total_processed) * 100 if total_processed > 0 else 0
    print("\n" + "=" * 40)
    print("EVALUATION COMPLETE")
    print(f"Total Posts Evaluated: {total_processed}")
    print(f"Correct Matches: {correct_matches}")
    print(f"TOP-1 PRECISION: {precision:.2f}%")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
