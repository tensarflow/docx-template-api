from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from docxtpl import DocxTemplate
import subprocess
import uuid
import os

router = APIRouter()

class GenerateRequest(BaseModel):
    template_id: str
    data: dict

def convert_to_pdf(docx_path: str, output_dir: str = "generated_docs"):
    pdf_path = os.path.join(output_dir, f"{uuid.uuid4()}.pdf")
    try:
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", output_dir, docx_path
        ], check=True)
        return pdf_path
    except subprocess.CalledProcessError:
        raise RuntimeError("PDF conversion failed")

@router.post("/generate-document/")
async def generate_document(request: GenerateRequest):
    template_path = f"templates/{request.template_id}.docx"
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Process DOCX with Jinja2
    output_docx = f"generated_docs/{uuid.uuid4()}.docx"
    doc = DocxTemplate(template_path)
    doc.render(request.data)
    doc.save(output_docx)
    
    # Convert to PDF
    pdf_path = convert_to_pdf(output_docx)
    
    return FileResponse(pdf_path, filename="document.pdf") 