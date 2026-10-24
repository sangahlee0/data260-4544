from pymongo import MongoClient

from .config import settings

_client = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
    return _client


def get_db():
    client = get_client()
    return client[settings.MONGODB_DB]


def get_vulnerabilities_collection():
    db = get_db()
    return db["vulnerabilities"]


### PART 2
def get_messages_collection():
    db = get_db()
    return db["messages"]


def get_summaries_collection():
    db = get_db()
    return db["summaries"]


def get_episodes_collection():
    db = get_db()
    return db["episodes"]
