from sqlalchemy import Column, String, DateTime
from app.database import Base
import datetime

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow) 