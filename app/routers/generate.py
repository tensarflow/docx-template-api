from fastapi import APIRouter, HTTPException, BackgroundTasks
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
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the filename without extension
    base_name = os.path.splitext(os.path.basename(docx_path))[0]
    pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
    
    try:
        result = subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", output_dir, docx_path
        ], check=True, capture_output=True, text=True)
        
        # Verify the PDF was created
        if not os.path.exists(pdf_path):
            raise RuntimeError(f"PDF not created. LibreOffice output: {result.stdout} {result.stderr}")
            
        return pdf_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"PDF conversion failed: {e.stdout} {e.stderr}")

def cleanup_files(output_docx: str, pdf_path: str):
    if output_docx and os.path.exists(output_docx):
        os.remove(output_docx)
    if pdf_path and os.path.exists(pdf_path):
        os.remove(pdf_path)

@router.post("/generate-document/")
async def generate_document(request: GenerateRequest, background_tasks: BackgroundTasks):
    print(f"Generating document for template: {request.template_id}")
    # Create directories if they don't exist
    os.makedirs("templates", exist_ok=True)
    os.makedirs("generated_docs", exist_ok=True)
    
    template_path = f"templates/{request.template_id}.docx"
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template not found")
    
    output_docx = None
    pdf_path = None
    
    try:
        # Generate unique ID for the document
        doc_id = str(uuid.uuid4())
        output_docx = f"generated_docs/{doc_id}.docx"
        
        # Process DOCX with Jinja2
        doc = DocxTemplate(template_path)
        doc.render(request.data)
        doc.save(output_docx)
        
        # Convert to PDF
        pdf_path = convert_to_pdf(output_docx)
        
        # Verify the PDF exists before returning
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF generation failed")
            
        # Add cleanup task to run after response is sent
        background_tasks.add_task(cleanup_files, output_docx, pdf_path)
            
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename="document.pdf",
            headers={
                "Content-Disposition": "attachment; filename=document.pdf",
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        # Clean up files if there's an error
        if output_docx and os.path.exists(output_docx):
            os.remove(output_docx)
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)
        raise HTTPException(status_code=500, detail=str(e))