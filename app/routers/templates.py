import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Template

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload-template/")
async def upload_template(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only .docx files allowed")
    
    template_id = str(uuid.uuid4())
    file_path = f"templates/{template_id}.docx"
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    contents = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Save to database
    db_template = Template(id=template_id, filename=file.filename)
    db.add(db_template)
    db.commit()
    
    return {"template_id": template_id}

@router.get("/templates/")
def list_templates(db: Session = Depends(get_db)):
    templates = db.query(Template).all()
    return {"templates": [{"id": t.id, "filename": t.filename} for t in templates]}

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