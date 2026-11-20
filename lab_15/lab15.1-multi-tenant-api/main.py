import os
import time
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pymongo import MongoClient, ASCENDING, DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel, Field
from typing import Literal


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

MONGO_URI = os.environ["MONGO_URI"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

RATE_LIMIT = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client["tasktracker"]
users = db["users"]
tasks = db["tasks"]
rate_limits = db["rate_limits"]

app = FastAPI(
    title="TaskTracker Multi-Tenant API",
    description="MongoDB-backed multi-tenant SaaS task management API",
    version="1.0"
)

security = HTTPBearer()

TOKEN_EXPIRE_MINUTES = 60


# --------------------------------------------------
# DATABASE INDEXES
# --------------------------------------------------

users.create_index(
    [("tenant_id", ASCENDING), ("username", ASCENDING)],
    unique=True,
    name="tenant_username_unique"
)

tasks.create_index(
    [("tenant_id", ASCENDING), ("created_at", DESCENDING)],
    name="tenant_created_at"
)

tasks.create_index(
    [("tenant_id", ASCENDING), ("owner_id", ASCENDING)],
    name="tenant_owner"
)

rate_limits.create_index(
    [("key", ASCENDING), ("window_start", ASCENDING)],
    unique=True,
    name="rate_limit_key_window"
)

rate_limits.create_index(
    [("expires_at", ASCENDING)],
    expireAfterSeconds=0,
    name="rate_limit_ttl"
)


# --------------------------------------------------
# PASSWORD HASHING
# --------------------------------------------------

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        310000
    )

    return salt, hashed.hex()


def verify_password(password, salt, stored_hash):
    _, calculated_hash = hash_password(password, salt)

    return hmac.compare_digest(
        calculated_hash,
        stored_hash
    )


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class LoginRequest(BaseModel):
    tenant_id: str
    username: str
    password: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: Literal["low", "medium", "high"] = "medium"


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    priority: Literal["low", "medium", "high"] | None = None
    status: Literal["open", "in_progress", "completed"] | None = None


# --------------------------------------------------
# JWT LOGIN
# --------------------------------------------------

@app.post("/auth/token")
def login(data: LoginRequest):

    user = users.find_one({
        "tenant_id": data.tenant_id,
        "username": data.username
    })

    if not user or not verify_password(
        data.password,
        user["password_salt"],
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant, username or password"
        )

    now = datetime.now(timezone.utc)

    payload = {
        "sub": user["user_id"],
        "tenant_id": user["tenant_id"],
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRE_MINUTES * 60
    }


# --------------------------------------------------
# JWT AUTHENTICATION
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role")

        if not user_id or not tenant_id:
            raise HTTPException(401, "Invalid token claims")

        if role not in ["admin", "user"]:
            raise HTTPException(403, "Invalid user role")

        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": role
        }

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


# --------------------------------------------------
# MONGODB-BACKED RATE LIMITING
# --------------------------------------------------

def enforce_rate_limit(user=Depends(get_current_user)):

    now_epoch = int(time.time())
    window_start_epoch = (now_epoch // RATE_WINDOW) * RATE_WINDOW

    window_start = datetime.fromtimestamp(
        window_start_epoch,
        tz=timezone.utc
    )

    expires_at = window_start + timedelta(seconds=RATE_WINDOW * 2)

    rate_key = f'{user["tenant_id"]}:{user["user_id"]}'

    query = {
        "key": rate_key,
        "window_start": window_start
    }

    update = {
        "$inc": {"count": 1},
        "$setOnInsert": {
            "key": rate_key,
            "window_start": window_start,
            "expires_at": expires_at
        }
    }

    try:
        counter = rate_limits.find_one_and_update(
            query,
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    except DuplicateKeyError:
        counter = rate_limits.find_one_and_update(
            query,
            {"$inc": {"count": 1}},
            return_document=ReturnDocument.AFTER
        )

    if counter["count"] > RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )


# --------------------------------------------------
# TENANT AND OWNER FILTER
# --------------------------------------------------

def task_access_filter(user, task_id=None):

    query = {
        "tenant_id": user["tenant_id"]
    }

    if task_id is not None:

        if not ObjectId.is_valid(task_id):
            raise HTTPException(400, "Invalid task ID")

        query["_id"] = ObjectId(task_id)

    if user["role"] != "admin":
        query["owner_id"] = user["user_id"]

    return query


# --------------------------------------------------
# RESPONSE SERIALIZATION
# --------------------------------------------------

def serialize_task(task):

    task["id"] = str(task.pop("_id"))

    if isinstance(task.get("created_at"), datetime):
        task["created_at"] = task["created_at"].isoformat()

    return task


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "TaskTracker API is running",
        "database": "tasktracker"
    }


@app.get("/health")
def health():
    client.admin.command("ping")
    return {"status": "healthy", "mongodb": "connected"}


# --------------------------------------------------
# CREATE TASK
# --------------------------------------------------

@app.post(
    "/tasks/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit)]
)
def create_task(
    task: TaskCreate,
    user=Depends(get_current_user)
):

    document = {
        "tenant_id": user["tenant_id"],
        "owner_id": user["user_id"],
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": "open",
        "created_at": datetime.now(timezone.utc)
    }

    result = tasks.insert_one(document)
    document["_id"] = result.inserted_id

    return serialize_task(document)


# --------------------------------------------------
# LIST TASKS
# --------------------------------------------------

@app.get(
    "/tasks/",
    dependencies=[Depends(enforce_rate_limit)]
)
def list_tasks(user=Depends(get_current_user)):

    query = task_access_filter(user)

    results = tasks.find(query).sort(
        "created_at",
        DESCENDING
    )

    return [serialize_task(task) for task in results]


# --------------------------------------------------
# GET ONE TASK
# --------------------------------------------------

@app.get(
    "/tasks/{task_id}",
    dependencies=[Depends(enforce_rate_limit)]
)
def get_task(
    task_id: str,
    user=Depends(get_current_user)
):

    task = tasks.find_one(
        task_access_filter(user, task_id)
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found or access denied"
        )

    return serialize_task(task)


# --------------------------------------------------
# UPDATE TASK
# --------------------------------------------------

@app.put(
    "/tasks/{task_id}",
    dependencies=[Depends(enforce_rate_limit)]
)
def update_task(
    task_id: str,
    update: TaskUpdate,
    user=Depends(get_current_user)
):

    changes = update.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if not changes:
        raise HTTPException(400, "No update fields provided")

    result = tasks.update_one(
        task_access_filter(user, task_id),
        {"$set": changes}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Task not found or access denied"
        )

    updated = tasks.find_one(
        task_access_filter(user, task_id)
    )

    return serialize_task(updated)


# --------------------------------------------------
# DELETE TASK
# --------------------------------------------------

@app.delete(
    "/tasks/{task_id}",
    dependencies=[Depends(enforce_rate_limit)]
)
def delete_task(
    task_id: str,
    user=Depends(get_current_user)
):

    result = tasks.delete_one(
        task_access_filter(user, task_id)
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Task not found or access denied"
        )

    return {
        "message": "Task deleted successfully"
    }


# --------------------------------------------------
# ADMIN: VIEW TENANT USERS
# --------------------------------------------------

@app.get(
    "/admin/users",
    dependencies=[Depends(enforce_rate_limit)]
)
def list_tenant_users(user=Depends(get_current_user)):

    if user["role"] != "admin":
        raise HTTPException(403, "Admin access required")

    result = users.find(
        {"tenant_id": user["tenant_id"]},
        {"password_hash": 0, "password_salt": 0, "_id": 0}
    )

    return list(result)