import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Template
from fastapi.responses import FileResponse
from typing import Optional

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload-template/")
async def upload_template(
    file: UploadFile = File(...),
    template_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only .docx files allowed")
    
    # If a template_id is provided, update the existing template
    if template_id:
        db_template = db.query(Template).filter(Template.id == template_id).first()
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found; cannot update a non-existing template")
        
        file_path = f"templates/{template_id}.docx"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        contents = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Update the filename (and other details if needed)
        db_template.filename = file.filename
        db.commit()
        
        return {"template_id": template_id, "message": "Template updated"}
    
    # Otherwise, create a new template record
    new_template_id = str(uuid.uuid4())
    file_path = f"templates/{new_template_id}.docx"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    contents = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    db_template = Template(id=new_template_id, filename=file.filename)
    db.add(db_template)
    db.commit()
    
    return {"template_id": new_template_id, "message": "Template uploaded"}

@router.get("/templates")
def list_templates(db: Session = Depends(get_db)):
    try:
        templates = db.query(Template).all()
        return {"templates": [{"id": t.id, "filename": t.filename} for t in templates]}
    except Exception as e:
        print(f"Error querying templates: {e}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-template/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    file_path = f"templates/{template_id}.docx"
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}

@router.get("/download-template/{template_id}")
def download_template(template_id: str):
    file_path = f"templates/{template_id}.docx"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template not found")
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{template_id}.docx"
    ) 