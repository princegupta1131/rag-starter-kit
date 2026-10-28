"""
COLLECTIONS API: separate knowledge bases (e.g. "HR policies", "Product docs").
Documents are uploaded into one collection; chat can search one collection or all.

    GET    /api/collections
    POST   /api/collections        {"name", "description"}
    DELETE /api/collections/{id}   also deletes its documents
"""
from uuid import UUID

from fastapi import APIRouter

from app.collections_service.schemas import CollectionIn, CollectionOut
from app.core.errors import Conflict, NotFound
from app.repositories import collections as collections_repo

router = APIRouter(prefix="/api/collections", tags=["collections"])


@router.get("", response_model=list[CollectionOut])
def list_collections():
    return collections_repo.list_all()


@router.post("", response_model=CollectionOut, status_code=201)
def create_collection(body: CollectionIn):
    created = collections_repo.create(body.name.strip(), body.description.strip())
    if created is None:
        raise Conflict(f"A collection named '{body.name.strip()}' already exists")
    return created


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: UUID):
    if not collections_repo.delete(collection_id):
        raise NotFound("Collection not found")
