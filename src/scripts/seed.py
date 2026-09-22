import asyncio

import httpx

# Using the user's exact local filenames, served via the FastAPI static mount!
IMAGES = [
    {"url": "http://127.0.0.1:8000/public/images/red_fox.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/wolf.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/dog.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/brown_bear.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/deer.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/tiger.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/giraffe.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/elephant.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/artic_fox.jpg"},
    {"url": "http://127.0.0.1:8000/public/images/black_dog.jpg"},
]


async def seed():
    print("Seeding database via API...")
    async with httpx.AsyncClient() as client:
        # 1. Ingest images
        try:
            res = await client.post("http://localhost:8000/api/v1/images/ingest", json=IMAGES)
            print(f"Ingest Request Status: {res.status_code}")
            print(res.json())
        except Exception as e:
            print(f"Failed to reach API: {e}")
            return

        print("\nImages queued! Monitoring background processing...")
        print("This may take 15-45 seconds depending on AI limits...")

        # 2. Monitor processing
        while True:
            try:
                res = await client.get("http://localhost:8000/api/v1/images/")
                images = res.json()

                # Check for images that are still processing or pending
                pending = [img for img in images if img["status"] in ["pending", "processing"]]
                failed = [img for img in images if img["status"] == "failed"]
                completed = [img for img in images if img["status"] == "completed"]

                print(
                    f"Status: {len(completed)} completed | {len(failed)} failed | {len(pending)} pending..."
                )

                if not pending:
                    print("\nAll background jobs finished!")
                    break

                await asyncio.sleep(3)

            except Exception as e:
                print(f"Error checking status: {e}")
                await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(seed())
