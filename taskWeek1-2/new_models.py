from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Regulation(Base):
    """
    Core model for TLU Regulation documents found via dynamic discovery.
    """
    __tablename__ = "regulations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    source_url = Column(String(1024), unique=True, index=True) # "Link động" traceability
    domain = Column(String(100)) # e.g., 'daotao.tlu.edu.vn'
    file_type = Column(String(10)) # 'PDF' or 'HTML'
    file_hash = Column(String(64)) # To handle document updates/duplicates
    
    # Metadata for filtering
    category = Column(String(100))
    published_date = Column(DateTime)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    chunks = relationship("RegulationChunk", back_populates="regulation", cascade="all, delete-orphan")

class RegulationChunk(Base):
    """
    Granular text segments for Hybrid Retrieval.
    Includes hierarchy and page markers for precise citations.
    """
    __tablename__ = "regulation_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    regulation_id = Column(Integer, ForeignKey("regulations.id"))
    
    content = Column(Text, nullable=False)
    
    # RAG specific metadata
    page_number = Column(Integer)
    chunk_index = Column(Integer)
    hierarchy_path = Column(Text) # e.g., "Chương II > Điều 5 > Khoản 1"
    
    # Link to Vector Storage
    vector_id = Column(String(100), index=True) # Point ID in Qdrant
    
    regulation = relationship("Regulation", back_populates="chunks")

# Index for full-text search optimization
Index('idx_regulation_content', RegulationChunk.content, postgresql_using='gin')
