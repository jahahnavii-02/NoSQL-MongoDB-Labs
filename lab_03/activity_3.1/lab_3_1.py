from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

print("Connected to MongoDB")

db = client["university_db"]

print("Database selected:", db.name)

courses = db["courses"]

courses.delete_many({})

print("Courses collection selected")

course1 = {
    "title": "Database Management Systems",
    "code": "CS401",
    "instructor": "Dr. Sharma",
    "students": [
        {
            "name": "Rahul",
            "id": "S101",
            "grade": "A"
        },
        {
            "name": "Priya",
            "id": "S102",
            "grade": "B+"
        },
        {
            "name": "Arjun",
            "id": "S103",
            "grade": "A-"
        }
    ],
    "schedule": {
        "days": ["Monday", "Wednesday"],
        "time": "10:00 AM - 11:00 AM",
        "room": "Room 201"
    }
}

result = courses.insert_one(course1)

print("Course inserted successfully")
print("Course ID:", result.inserted_id)

course2 = {
    "title": "Computer Networks",
    "code": "CS402",
    "instructor": "Dr. Mehta",
    "students": [
        {
            "name": "Sneha",
            "id": "S104",
            "grade": "A"
        },
        {
            "name": "Vikram",
            "id": "S105",
            "grade": "B"
        },
        {
            "name": "Ananya",
            "id": "S106",
            "grade": "A+"
        }
    ],
    "schedule": {
        "days": ["Tuesday", "Thursday"],
        "time": "11:00 AM - 12:00 PM",
        "room": "Room 202"
    }
}

result = courses.insert_one(course2)

print("Second course inserted successfully")

course3 = {
    "title": "Operating Systems",
    "code": "CS403",
    "instructor": "Dr. Sharma",
    "students": [
        {
            "name": "Karan",
            "id": "S107",
            "grade": "B+"
        },
        {
            "name": "Neha",
            "id": "S108",
            "grade": "A"
        },
        {
            "name": "Aman",
            "id": "S109",
            "grade": "A-"
        }
    ],
    "schedule": {
        "days": ["Monday", "Friday"],
        "time": "2:00 PM - 3:00 PM",
        "room": "Room 203"
    }
}

result = courses.insert_one(course3)

print("Third course inserted successfully")

print("\nCourses that meet on Monday:")

monday_courses = courses.find({
    "schedule.days": "Monday"
})

for course in monday_courses:
    print(course["code"], "-", course["title"])

    # Schema validation

validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "title",
            "code",
            "instructor",
            "schedule"
        ]
    }
}

db.command(
    "collMod",
    "courses",
    validator=validator,
    validationLevel="strict",
    validationAction="error"
)

print("\nSchema validation added successfully")

# Test schema validation

invalid_course = {
    "title": "Artificial Intelligence",
    "code": "CS404",
    "instructor": "Dr. Rao"
}

try:
    courses.insert_one(invalid_course)
    print("Invalid course inserted")
except Exception as e:
    print("Validation error: Invalid course rejected")

    # Find students taught by a specific instructor

instructor = "Dr. Sharma"

print("\nStudents enrolled in courses taught by", instructor, ":")

courses_by_instructor = courses.find({
    "instructor": instructor
})

for course in courses_by_instructor:
    print("\nCourse:", course["code"], "-", course["title"])

    for student in course["students"]:
        print(
            student["name"],
            "| ID:", student["id"],
            "| Grade:", student["grade"]
        )

        # Add prerequisites

courses.update_one(
    {"code": "CS402"},
    {"$set": {"prerequisites": ["CS401"]}}
)

print("\nPrerequisite added to CS402")

courses.update_one(
    {"code": "CS403"},
    {"$set": {"prerequisites": ["CS401"]}}
)

print("Prerequisite added to CS403")

# Justification:
# Prerequisites are embedded as an array of course codes because
# they are small and closely related to the course. Storing only
# the prerequisite course codes avoids duplicating complete course
# documents and makes the prerequisite information easy to access.