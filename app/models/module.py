from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    order = Column(Integer, default=1)
    status = Column(String, default="Ongoing") # Ongoing, Completed
    
    # Relationships
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=True) # Optional filter by batch
    
    chapters = relationship("Chapter", back_populates="module", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    order = Column(Integer, default=1)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    
    module = relationship("Module", back_populates="chapters")
