from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection

from app.database import get_projects_collection
from app.deps import get_current_user
from app.schemas import ProjectCreate, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_project_out(project: dict, current_user_id: str) -> ProjectOut:
    return ProjectOut(
        id=str(project["_id"]),
        name=project["name"],
        description=project.get("description"),
        owner_id=project["owner_id"],
        owner_email=project["owner_email"],
        created_at=project["created_at"],
        is_owner=project["owner_id"] == current_user_id,
    )


def _parse_project_id(project_id: str) -> ObjectId:
    try:
        return ObjectId(project_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project id")


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    projects: AsyncIOMotorCollection = get_projects_collection()

    doc = {
        "name": project.name,
        "description": project.description,
        "owner_id": str(current_user["_id"]),
        "owner_email": current_user["email"],
        "created_at": datetime.now(timezone.utc),
    }
    result = await projects.insert_one(doc)
    doc["_id"] = result.inserted_id

    return _to_project_out(doc, str(current_user["_id"]))


@router.get("", response_model=list[ProjectOut])
async def list_projects(current_user: dict = Depends(get_current_user)):
    projects: AsyncIOMotorCollection = get_projects_collection()
    current_user_id = str(current_user["_id"])

    return [
        _to_project_out(project, current_user_id)
        async for project in projects.find().sort("created_at", -1)
    ]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    projects: AsyncIOMotorCollection = get_projects_collection()
    project = await projects.find_one({"_id": _parse_project_id(project_id)})

    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return _to_project_out(project, str(current_user["_id"]))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    projects: AsyncIOMotorCollection = get_projects_collection()
    project = await projects.find_one({"_id": _parse_project_id(project_id)})

    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project["owner_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own projects"
        )

    await projects.delete_one({"_id": project["_id"]})
