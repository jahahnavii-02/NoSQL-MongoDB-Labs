from pymongo import MongoClient

# Connect to MongoDB Atlas
atlas_client = MongoClient("mongodb+srv://jahahnavii_db_user:Jahnavi2106@cluster0.ui5jrcz.mongodb.net/?appName=Cluster0")

# Connect to MongoDB running in Docker
docker_client = MongoClient("mongodb://127.0.0.1:27017/")
# Get server information
atlas_info = atlas_client.server_info()
docker_info = docker_client.server_info()

# Display server versions
print("Atlas MongoDB version:", atlas_info["version"])
print("Docker MongoDB version:", docker_info["version"])

# Compare versions
if atlas_info["version"] == docker_info["version"]:
    print("Both MongoDB servers have the same version.")
else:
    print("MongoDB server versions are different.")

# Close connections
atlas_client.close()
docker_client.close()