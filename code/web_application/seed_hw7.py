"""
HW7 – User seeder
Creates three users in MySQL with bcrypt-hashed passwords and JWT roles.

Roles
-----
reader    – can only list/read domain entities
writer    – can create domain entities
moderator – can create AND delete domain entities

Run from the web_application/ directory:
    python seed_hw7.py
"""

import os
import sys

# Make sure backend/ and app/ are importable when running from web_application/
sys.path.insert(0, os.path.dirname(__file__))

from app.core.security import get_password_hash
from backend import models
from backend.database import SessionLocal

HW7_USERS = [
    {
        "username": "alice",
        "email": "alice@s4544.local",
        "password": "alice123",
        "role": "reader",
    },
    {
        "username": "bob",
        "email": "bob@s4544.local",
        "password": "bob123",
        "role": "writer",
    },
    {
        "username": "charlie",
        "email": "charlie@s4544.local",
        "password": "charlie123",
        "role": "moderator",
    },
]


def seed():
    db = SessionLocal()
    created = 0
    skipped = 0

    for u in HW7_USERS:
        existing = (
            db.query(models.User).filter(models.User.username == u["username"]).first()
        )
        if existing:
            print(f"  SKIP  {u['username']} (already exists, role={existing.role})")
            skipped += 1
            continue

        db.add(
            models.User(
                username=u["username"],
                email=u["email"],
                name=u["username"].capitalize(),  # kept for backwards compat
                password_hash=get_password_hash(u["password"]),
                role=u["role"],
            )
        )
        print(f"  CREATE {u['username']}  role={u['role']}")
        created += 1

    db.commit()
    db.close()
    print(f"\nDone — {created} created, {skipped} skipped.")


if __name__ == "__main__":
    seed()
