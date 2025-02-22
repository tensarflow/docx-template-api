from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from fastapi.staticfiles import StaticFiles
from app.routers import templates, generate

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend's domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add database initialization
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

# Mount static files for template storage
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.include_router(templates.router)
app.include_router(generate.router)

@app.get("/")
def read_root():
    return {"message": "DOCX Template API"} 