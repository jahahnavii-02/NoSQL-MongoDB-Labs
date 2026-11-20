from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

db = client["university_db"]
courses = db["courses"]

print("Database selected: university_db")

# Add prerequisite to CS402
courses.update_one(
    {"code": "CS402"},
    {"$set": {"prerequisites": ["CS401"]}}
)

print("Prerequisite added to CS402")

# Add prerequisite to CS403
courses.update_one(
    {"code": "CS403"},
    {"$set": {"prerequisites": ["CS401"]}}
)

print("Prerequisite added to CS403")

# Display courses with prerequisites
print("\n--- Courses with Prerequisites ---")

for course in courses.find(
    {"prerequisites": {"$exists": True}},
    {"_id": 0, "title": 1, "code": 1, "prerequisites": 1}
):
    print(course)

# Justification
print("\n--- Justification ---")
print("Prerequisites are embedded as an array of course codes")
print("because they are small and closely related to each course.")
print("Only the prerequisite course codes are stored, avoiding")
print("duplication of complete course documents and making the")
print("prerequisite information easy to access.")