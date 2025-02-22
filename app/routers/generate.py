from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi.responses import FileResponse
from docxtpl import DocxTemplate, InlineImage
import subprocess
import uuid
import os
from io import BytesIO
from PIL import Image
import base64
import requests
from docx.shared import Mm

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

# Function to convert base64 or URL to InlineImage
def get_image(image_data, doc):
    if image_data.startswith('http'):
        # Handle URL
        response = requests.get(image_data)
        image = Image.open(BytesIO(response.content))
    else:
        # Handle base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
    
    # Convert to InlineImage
    image_stream = BytesIO()
    image.save(image_stream, format=image.format)
    image_stream.seek(0)
    return InlineImage(doc, image_stream, width=Mm(50))  # Adjust width as needed

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
        
        doc = DocxTemplate(template_path)
        
        # Process images in the data
        for key, value in request.data.items():
            if isinstance(value, str) and (value.startswith('http') or value.startswith('data:image')):
                request.data[key] = get_image(value, doc)
        
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