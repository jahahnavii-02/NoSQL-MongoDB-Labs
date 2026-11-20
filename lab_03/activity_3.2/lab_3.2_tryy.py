from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

db = client["blog_db"]

posts = db["large_posts"]
comments = db["large_comments"]

# Clear previous data
posts.delete_many({})
comments.delete_many({})

# Create one post
post = {
    "post_id": 1,
    "title": "Post with 10,000 Comments",
    "author": "Jahnavi",
    "content": "This post demonstrates why embedding a very large number of comments can be problematic."
}

posts.insert_one(post)

# Create 10,000 comments using a referenced design
comment_documents = []

for i in range(1, 10001):
    comment_documents.append({
        "comment_id": i,
        "post_id": 1,
        "user": f"User{i}",
        "text": f"This is comment number {i}."
    })

comments.insert_many(comment_documents)

print("Post created successfully.")
print("Total comments:", comments.count_documents({"post_id": 1}))

print("\n--- Try It Yourself ---")
print("Scenario: A post has 10,000 comments.")

print("\nWhy embedding is problematic:")
print("1. The post document becomes very large.")
print("2. Updating individual comments becomes more expensive.")
print("3. Loading the complete post may require unnecessary data.")
print("4. A very large document can approach MongoDB's 16 MB document size limit.")

print("\nAlternative design:")
print("Use a referenced design.")
print("Store the post and comments in separate collections.")
print("Link each comment to the post using post_id.")

print("\nReferenced design implemented successfully.")