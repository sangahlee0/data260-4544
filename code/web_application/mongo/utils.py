from bson import ObjectId
from datetime import datetime, timezone
from .db import get_messages_collection, get_summaries_collection, get_episodes_collection


def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def is_valid_object_id(value: str) -> bool:
    try:
        ObjectId(value)
        return True
    except Exception:
        return False

def to_object_id(value: str) -> ObjectId:
    return ObjectId(value)

def serialize_vulnerability(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "vulnerability_name": doc.get("vulnerability_name"),
        "description": doc.get("description"),
        "status": doc.get("status"),
        "severity": doc.get("severity"),
        "discovered_at": doc.get("discovered_at"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


### PART 2
def save_message(user_id: str, session_id: str, role: str, content: str):
    col = get_messages_collection()

    doc = {
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": now_utc()
    }

    col.insert_one(doc)


def get_recent_messages(user_id: str, session_id: str, limit: int = 16):
    col = get_messages_collection()

    docs = list(
        col.find({
            "user_id": user_id,
            "session_id": session_id}).sort("created_at", -1).limit(limit)
    )

    return list(reversed(docs))


def get_session_summary(user_id: str, session_id: str):
    col = get_summaries_collection()

    return col.find_one(
        {
            "user_id": user_id,
            "session_id": session_id,
            "scope": "session"
        },
        sort=[("created_at", -1)]
    )


def get_latest_session_summary(user_id: str):
    col = get_summaries_collection()

    return col.find_one(
        {
            "user_id": user_id,
            "scope": "session",
        },
        sort=[("created_at", -1)],
    )


def get_user_summary(user_id: str):
    col = get_summaries_collection()

    return col.find_one(
        {
            "user_id": user_id,
            "scope": "user"
        },
        sort=[("created_at", -1)]
    )


def save_episode(
    user_id: str,
    session_id: str,
    fact: str,
    importance: float,
    embedding: list[float]
):
    col = get_episodes_collection()

    doc = {
        "user_id": user_id,
        "session_id": session_id,
        "fact": fact,
        "importance": importance,
        "embedding": embedding,
        "created_at": now_utc()
    }

    col.insert_one(doc)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    # How similar two embedding lists are. 1 means the same, 0 means unrelated.
    dot = 0.0
    left_size = 0.0
    right_size = 0.0

    for a, b in zip(left, right):
        dot += a * b
        left_size += a * a
        right_size += b * b

    if left_size == 0 or right_size == 0:
        return 0.0

    return dot / ((left_size ** 0.5) * (right_size ** 0.5))


def get_relevant_episodes(user_id: str, query_embedding: list[float], limit: int = 3):
    col = get_episodes_collection()
    docs = list(col.find({"user_id": user_id}))

    # give each fact a score, then put the highest scores first
    for doc in docs:
        embedding = doc.get("embedding")
        if embedding is None:
            embedding = []
        doc["score"] = cosine_similarity(query_embedding, embedding)

    docs.sort(key=lambda doc: doc["score"], reverse=True)

    top = []
    for doc in docs:
        if len(top) == limit:
            break
        top.append(doc)

    return top


def count_user_messages(user_id: str, session_id: str) -> int:
    col = get_messages_collection()
    return col.count_documents({
        "user_id": user_id,
        "session_id": session_id,
        "role": "user",
    })


def save_summary(user_id: str, session_id: str | None, scope: str, text: str):
    col = get_summaries_collection()
    col.insert_one({
        "user_id": user_id,
        "session_id": session_id,
        "scope": scope,
        "text": text,
        "created_at": now_utc(),
    })


def count_session_summaries(user_id: str) -> int:
    col = get_summaries_collection()
    return col.count_documents({"user_id": user_id, "scope": "session"})


def get_session_summary_texts(user_id: str, limit: int = 6) -> list[str]:
    col = get_summaries_collection()
    docs = list(
        col.find({"user_id": user_id, "scope": "session"})
        .sort("created_at", -1)
        .limit(limit)
    )
    docs.reverse()

    texts = []
    for doc in docs:
        text = doc.get("text")
        if text:
            texts.append(text)
    return texts


def get_user_messages(user_id: str, limit: int = 16):
    col = get_messages_collection()
    docs = list(
        col.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    )
    docs.reverse()
    return docs


def get_recent_episodes(user_id: str, limit: int = 20):
    col = get_episodes_collection()
    docs = list(
        col.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    )
    docs.reverse()
    return docs


def get_recent_summaries(user_id: str, limit: int = 5):
    col = get_summaries_collection()
    return list(
        col.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    )


def get_daily_message_counts(user_id: str):
    col = get_messages_collection()
    counts = {}

    for doc in col.find({"user_id": user_id}):
        created_at = doc.get("created_at")
        if created_at is None:
            continue
        day = created_at.strftime("%Y-%m-%d")
        if day not in counts:
            counts[day] = 0
        counts[day] = counts[day] + 1

    daily_counts = []
    for day in sorted(counts):
        daily_counts.append({"date": day, "count": counts[day]})
    return daily_counts


def serialize_message(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id"),
        "session_id": doc.get("session_id"),
        "role": doc.get("role"),
        "content": doc.get("content"),
        "created_at": doc.get("created_at"),
    }


def serialize_summary(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id"),
        "session_id": doc.get("session_id"),
        "scope": doc.get("scope"),
        "text": doc.get("text"),
        "created_at": doc.get("created_at"),
    }


def serialize_episode(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id"),
        "session_id": doc.get("session_id"),
        "fact": doc.get("fact"),
        "importance": doc.get("importance"),
        "created_at": doc.get("created_at"),
    }