
import argparse
import asyncio
import edgedb
import json
import progress.bar
import uvloop

async def import_data(data: dict):
    client = edgedb.create_async_client(max_concurrency=32)
    batch_size = 1000

    posts = data["post"]

    # region Load posts
    posts_data = [
        dict(
            content=p["content"],
            upvote=p["upvote"],
            downvote=p["downvote"], 
        ) for p in posts
    ]

    posts_insert_query = r"""
        WITH posts := <json>$posts
        FOR post in json_array_unpack(posts) UNION (
        INSERT Post {
            content := <str>post["content"],
            upvote := <int16>post["upvote"],
            downvote := <int16>post["downvote"],
        }
        );
    """

    start = 0
    posts_bar = progress.bar.Bar("Posts", max=len(posts))
    posts_slice = posts_data[start:start+batch_size]
    while len(posts_slice):
        posts_bar.goto(start)
        await client.query(posts_insert_query, posts=json.dumps(posts_slice))
        start += batch_size
        posts_slice = posts_data[start:start+batch_size]
    posts_bar.goto(posts_bar.max)
    posts_bar.finish()
    
    # endregion

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="The EdgeDB JSON dataset file")
    args = parser.parse_args()

    with open(args.filename) as f:
        data = json.load(f)
    
    uvloop.install()
    asyncio.run(import_data(data))