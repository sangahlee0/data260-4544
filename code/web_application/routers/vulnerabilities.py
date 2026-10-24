from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from mongo.db import get_vulnerabilities_collection
from mongo.schemas import VulnerabilityCreate, VulnerabilityOut, VulnerabilityUpdate
from mongo.utils import (
    is_valid_object_id,
    now_utc,
    serialize_vulnerability,
    to_object_id,
)

router = APIRouter(prefix="/api/vulnerabilities", tags=["Vulnerabilities"])


@router.post("", response_model=VulnerabilityOut, status_code=status.HTTP_201_CREATED)
def create_vulnerability(payload: VulnerabilityCreate):
    col = get_vulnerabilities_collection()
    doc = payload.model_dump()

    ts = now_utc()
    doc["created_at"] = ts
    doc["updated_at"] = ts

    try:
        res = col.insert_one(doc)
        created = col.find_one({"_id": res.inserted_id})
        return serialize_vulnerability(created)
    except PyMongoError:
        raise HTTPException(
            status_code=500, detail="Database error while creating vulnerability."
        )


@router.get("", response_model=list[VulnerabilityOut])
def get_all_vulnerabilities():
    col = get_vulnerabilities_collection()

    try:
        docs = list(col.find().sort("created_at", -1))
        return [serialize_vulnerability(d) for d in docs]
    except PyMongoError:
        raise HTTPException(
            status_code=500, detail="Database error while fetching vulnerabilities."
        )


@router.get("/{vulnerability_id}", response_model=VulnerabilityOut)
def get_one_vulnerability(vulnerability_id: str):
    if not is_valid_object_id(vulnerability_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_vulnerabilities_collection()

    try:
        doc = col.find_one({"_id": to_object_id(vulnerability_id)})

        if not doc:
            raise HTTPException(status_code=404, detail="Vulnerability not found.")

        return serialize_vulnerability(doc)

    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(
            status_code=500, detail="Database error while fetching vulnerability."
        )


@router.put("/{vulnerability_id}", response_model=VulnerabilityOut)
def update_vulnerability(vulnerability_id: str, payload: VulnerabilityUpdate):
    if not is_valid_object_id(vulnerability_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_vulnerabilities_collection()

    try:
        existing = col.find_one({"_id": to_object_id(vulnerability_id)})

        if not existing:
            raise HTTPException(status_code=404, detail="Vulnerability not found.")

        updates = payload.model_dump(exclude_unset=True)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided to update.")

        updates["updated_at"] = now_utc()

        col.update_one({"_id": to_object_id(vulnerability_id)}, {"$set": updates})

        updated = col.find_one({"_id": to_object_id(vulnerability_id)})

        return serialize_vulnerability(updated)

    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(
            status_code=500, detail="Database error while updating vulnerability."
        )


@router.delete("/{vulnerability_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vulnerability(vulnerability_id: str):
    if not is_valid_object_id(vulnerability_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_vulnerabilities_collection()

    try:
        res = col.delete_one({"_id": to_object_id(vulnerability_id)})

        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Vulnerability not found.")

        return

    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(
            status_code=500, detail="Database error while deleting vulnerability."
        )
