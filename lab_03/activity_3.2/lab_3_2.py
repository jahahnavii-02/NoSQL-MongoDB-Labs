from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

print("Connected to MongoDB")

db = client["blog_db"]

print("Database selected:", db.name)

posts = db["posts"]
comments = db["comments"]

posts.delete_many({})
comments.delete_many({})

print("Posts collection created")
print("Comments collection created")

post1 = {
    "post_id": 1,
    "title": "Introduction to MongoDB",
    "author": "Jahnavi",
    "content": "MongoDB is a NoSQL database that stores data in flexible documents.",
    "media": {
        "image": "mongodb.png",
        "video": "mongodb_intro.mp4"
    }
}

result = posts.insert_one(post1)

print("First post inserted successfully")
print("Post ID:", result.inserted_id)

post2 = {
    "post_id": 2,
    "title": "Understanding NoSQL Databases",
    "author": "Rahul",
    "content": "NoSQL databases are useful for flexible and scalable data storage.",
    "media": {
        "image": "nosql.png",
        "video": "nosql_intro.mp4"
    }
}

posts.insert_one(post2)

print("Second post inserted successfully")

post3 = {
    "post_id": 3,
    "title": "MongoDB CRUD Operations",
    "author": "Priya",
    "content": "CRUD operations are used to create, read, update, and delete documents in MongoDB.",
    "media": {
        "image": "mongodb_crud.png",
        "video": "mongodb_crud.mp4"
    }
}

posts.insert_one(post3)

print("Third post inserted successfully")

post4 = {
    "post_id": 4,
    "title": "Embedded vs Referenced Documents",
    "author": "Ananya",
    "content": "MongoDB supports both embedded and referenced document designs.",
    "media": {
        "image": "embedded_vs_referenced.png",
        "video": "embedded_vs_referenced.mp4"
    }
}

posts.insert_one(post4)

print("Fourth post inserted successfully")

post5 = {
    "post_id": 5,
    "title": "MongoDB Aggregation Pipeline",
    "author": "Vikram",
    "content": "The aggregation pipeline processes documents through a sequence of stages.",
    "media": {
        "image": "aggregation.png",
        "video": "aggregation_tutorial.mp4"
    }
}

posts.insert_one(post5)

print("Fifth post inserted successfully")

print("\nTotal posts:", posts.count_documents({}))

comment1 = {
    "comment_id": 1,
    "post_id": 1,
    "user": "Amit",
    "text": "Very informative post!"
}

comments.insert_one(comment1)

print("Comment 1 inserted successfully")
comment2 = {
    "comment_id": 2,
    "post_id": 1,
    "user": "Priya",
    "text": "This explains MongoDB very clearly."
}

comments.insert_one(comment2)

print("Comment 2 inserted successfully")
comment3 = {
    "comment_id": 3,
    "post_id": 2,
    "user": "Arjun",
    "text": "A useful introduction to NoSQL databases."
}

comments.insert_one(comment3)

print("Comment 3 inserted successfully")
comment4 = {
    "comment_id": 4,
    "post_id": 2,
    "user": "Neha",
    "text": "The scalability explanation was helpful."
}

comments.insert_one(comment4)

print("Comment 4 inserted successfully")
comment5 = {
    "comment_id": 5,
    "post_id": 3,
    "user": "Karan",
    "text": "The CRUD operations are easy to understand with this example."
}

comments.insert_one(comment5)

print("Comment 5 inserted successfully")
comment6 = {
    "comment_id": 6,
    "post_id": 3,
    "user": "Sneha",
    "text": "This is a good practical example of CRUD."
}

comments.insert_one(comment6)

print("Comment 6 inserted successfully")
comment7 = {
    "comment_id": 7,
    "post_id": 4,
    "user": "Riya",
    "text": "The comparison between embedded and referenced design is useful."
}

comment8 = {
    "comment_id": 8,
    "post_id": 4,
    "user": "Vikram",
    "text": "I understand the difference much better now."
}

comment9 = {
    "comment_id": 9,
    "post_id": 5,
    "user": "Ananya",
    "text": "The aggregation pipeline example is helpful."
}

comment10 = {
    "comment_id": 10,
    "post_id": 5,
    "user": "Rahul",
    "text": "Great explanation of aggregation."
}

comments.insert_many([
    comment7,
    comment8,
    comment9,
    comment10
])

print("Comments 7-10 inserted successfully")
print("\nTotal comments:", comments.count_documents({}))

# Retrieve a post with its comments using $lookup

pipeline = [
    {
        "$match": {
            "post_id": 1
        }
    },
    {
        "$lookup": {
            "from": "comments",
            "localField": "post_id",
            "foreignField": "post_id",
            "as": "comments"
        }
    }
]

result = posts.aggregate(pipeline)

for post in result:
    print("\nPost:", post["title"])
    print("Comments:")

    for comment in post["comments"]:
        print(
            comment["user"],
            ":",
            comment["text"]
        )

        # Create collection for embedded design

embedded_posts = db["embedded_posts"]

embedded_posts.delete_many({})

print("\nEmbedded posts collection created")

# Migrate posts from referenced design to embedded design

for post in posts.find():
    post_comments = list(
        comments.find(
            {"post_id": post["post_id"]},
            {"_id": 0}
        )
    )

    post["comments"] = post_comments

    embedded_posts.insert_one(post)

print("Migration completed successfully")

# Compare database queries

print("\n--- Query Comparison ---")

print("Referenced design:")
print("1 query to retrieve the post")
print("1 query using $lookup to retrieve the comments")
print("Total: 1 aggregation query")

print("\nEmbedded design:")
print("1 query retrieves the post and embedded comments")
print("Total: 1 query")

# Try it yourself: 10,000 comments

print("\n--- Try It Yourself ---")
print("If a post has 10,000 comments, embedding all comments")
print("would make the post document very large and harder to update.")
print("It could also affect performance and approach MongoDB's")
print("16 MB document size limit.")
print("Therefore, I would use a referenced design where comments")
print("are stored in a separate collection and linked using post_id.")