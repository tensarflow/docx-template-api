from fastapi import Depends, FastAPI
from app.database import engine, Base
from app.routers import templates, generate
from app.security import require_api_key

# No interactive docs and no CORS: only the qr-certificates server calls
# this API, never a browser.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Add database initialization
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

# Template files are only reachable through the authenticated routes below.
app.include_router(templates.router, dependencies=[Depends(require_api_key)])
app.include_router(generate.router, dependencies=[Depends(require_api_key)])

@app.get("/")
def read_root():
    return {"message": "DOCX Template API"}
