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
import traceback

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
    try:
        if image_data.startswith('http'):
            # Handle URL
            response = requests.get(image_data)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '').lower()
            
            if 'svg' in content_type:
                # Convert SVG to PNG using cairosvg
                import cairosvg
                png_data = cairosvg.svg2png(bytestring=response.content)
                image = Image.open(BytesIO(png_data))
            else:
                image = Image.open(BytesIO(response.content))
            
            print(f"Image format from URL: {image.format}")
            print(image_data)
        else:
            # Handle base64
            print("Base64 data received:", image_data[:30], "...")
            if image_data.startswith('data:image'):
                content_type = image_data.split(';')[0].split('/')[1].lower()
                # Remove the data URL scheme
                image_data = image_data.split(',', 1)[1]
            
            # Decode base64 string
            decoded_data = base64.b64decode(image_data + "=" * (4 - len(image_data) % 4))
            
            if content_type == 'svg+xml':
                # Convert SVG to PNG using cairosvg
                import cairosvg
                png_data = cairosvg.svg2png(bytestring=decoded_data)
                image = Image.open(BytesIO(png_data))
            else:
                image = Image.open(BytesIO(decoded_data))

        # Convert to InlineImage
        print(f"Converting image to InlineImage format with format: {image.format}")
        image_stream = BytesIO()
        image.save(image_stream, format='PNG')  # Always save as PNG for consistency
        image_stream.seek(0)
        print(f"Image conversion to InlineImage format completed with format: PNG")
        return InlineImage(doc, image_stream, width=Mm(20))

    except Exception as e:
        print(f"Error processing image data: {e}")
        raise ValueError(f"Invalid image data provided: {str(e)}")

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
        
        # Log stacktrace
        traceback.print_exc()
        
        raise HTTPException(status_code=500, detail=str(e))