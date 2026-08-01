import asyncio
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorCollection

from app.database import (
    get_projects_collection,
    get_question_papers_collection,
    get_syllabi_collection,
)
from app.deps import get_current_user
from app.schemas import (
    DocumentOut,
    DocumentStatus,
    DocumentType,
    DocumentUploadResponse,
    DocumentUploadResult,
)
from app.services.processing import process_question_paper, process_syllabus, schedule
from app.storage import is_allowed_file, save_pdf_pages, save_upload

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


def _collection_for(doc_type: DocumentType) -> AsyncIOMotorCollection:
    return (
        get_question_papers_collection()
        if doc_type == DocumentType.QUESTION_PAPER
        else get_syllabi_collection()
    )


def _parse_project_id(project_id: str) -> ObjectId:
    try:
        return ObjectId(project_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project id"
        )


async def _ensure_project_exists(project_id: str) -> None:
    projects: AsyncIOMotorCollection = get_projects_collection()
    project = await projects.find_one({"_id": _parse_project_id(project_id)})
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )


def _to_document_out(doc: dict) -> DocumentOut:
    return DocumentOut(
        id=str(doc["_id"]),
        project_id=doc["project_id"],
        filename=doc["filename"],
        doc_type=doc["doc_type"],
        status=doc["status"],
        error=doc.get("error"),
        uploaded_at=doc["uploaded_at"],
        updated_at=doc["updated_at"],
    )


@router.post(
    "", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_documents(
    project_id: str,
    question_papers: list[UploadFile] = File(default=[]),
    syllabi: list[UploadFile] = File(default=[]),
    current_user: dict = Depends(get_current_user),
):
    await _ensure_project_exists(project_id)

    uploads = [
        (f, DocumentType.QUESTION_PAPER) for f in question_papers if f.filename
    ] + [(f, DocumentType.SYLLABUS) for f in syllabi if f.filename]
    if not uploads:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided"
        )

    invalid_files = [f.filename for f, _ in uploads if not is_allowed_file(f.filename)]
    if invalid_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type for: {', '.join(invalid_files)}. Only .pdf, .txt, .json are allowed",
        )

    results: list[DocumentUploadResult] = []

    for file, doc_type in uploads:
        file_path = await save_upload(project_id, file)
        now = datetime.now(timezone.utc)

        doc = {
            "project_id": project_id,
            "filename": file.filename,
            "file_path": file_path,
            "doc_type": doc_type.value,
            "status": DocumentStatus.EXTRACTING.value,
            "error": None,
            "pages": [],
            "uploaded_by": str(current_user["_id"]),
            "uploaded_at": now,
            "updated_at": now,
        }
        collection = _collection_for(doc_type)
        result = await collection.insert_one(doc)
        doc_id = result.inserted_id

        pages: list[str] = []
        if Path(file_path).suffix.lower() == ".pdf":
            pages = await asyncio.to_thread(
                save_pdf_pages, project_id, str(doc_id), file_path
            )
            await collection.update_one({"_id": doc_id}, {"$set": {"pages": pages}})

        if doc_type == DocumentType.QUESTION_PAPER:
            schedule(process_question_paper(doc_id, file_path, project_id, pages))
        else:
            schedule(process_syllabus(doc_id, file_path))

        results.append(
            DocumentUploadResult(
                id=str(doc_id), filename=file.filename, doc_type=doc_type
            )
        )

    return DocumentUploadResponse(
        message=f"{len(results)} file(s) received and are being processed",
        documents=results,
    )


@router.get("/status", response_model=list[DocumentOut])
async def get_processing_status(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    await _ensure_project_exists(project_id)

    query = {
        "project_id": project_id,
        "status": {"$ne": DocumentStatus.COMPLETED.value},
    }
    docs = [
        doc
        for collection in (get_question_papers_collection(), get_syllabi_collection())
        async for doc in collection.find(query)
    ]
    docs.sort(key=lambda doc: doc["uploaded_at"])

    return [_to_document_out(doc) for doc in docs]
