from fastapi import FastAPI, HTTPException
import lancedb
from lancedb.pydantic import LanceModel
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Json
from contextlib import asynccontextmanager

class FileSchema(LanceModel):
    filename: str
    content: str  # base64 encoded content
    content_type: str
    upload_date: str
    file_size: int
    metadata: str  # Store metadata as JSON string instead of dict

class FileResponse(BaseModel):
    filename: str
    content: str
    content_type: str
    metadata: dict

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = lancedb.connect("file_storage")
    if "files" not in db.table_names():
        db.create_table("files", schema=FileSchema)
    yield

app = FastAPI(lifespan=lifespan)
db = lancedb.connect("file_storage")

@app.post("/files/")
async def upload_file(file: FileSchema):
    table = db.open_table("files")
    # Convert metadata dict to JSON string before storing
    if isinstance(file.metadata, dict):
        file.metadata = Json.dumps(file.metadata)
    table.add([file])
    return {"message": "File uploaded successfully", "filename": file.filename}

@app.get("/files/{filename}", response_model=FileResponse)
async def get_file(filename: str):
    table = db.open_table("files")
    results = table.search().where(f"filename = '{filename}'").to_list()
    
    if not results:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = results[0]
    return FileResponse(
        filename=file_data["filename"],
        content=file_data["content"],
        content_type=file_data["content_type"],
        metadata=Json.loads(file_data["metadata"])  # Convert JSON string back to dict
    )
