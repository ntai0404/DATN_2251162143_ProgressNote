from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class RegulationMetadata(Base):
    __tablename__ = 'regulation_metadata'
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512))
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    category = Column(String(100)) # e.g., "Đào tạo", "Công tác sinh viên"
    
    chunks = relationship("TextChunk", back_populates="regulation")

class TextChunk(Base):
    __tablename__ = 'text_chunks'
    
    id = Column(Integer, primary_key=True)
    regulation_id = Column(Integer, ForeignKey('regulation_metadata.id'))
    article_title = Column(String(255))
    content = Column(Text, nullable=False)
    vector_id = Column(Integer) # ID mapping to Qdrant point_id
    page_number = Column(Integer)
    
    regulation = relationship("RegulationMetadata", back_populates="chunks")

class ConversationLog(Base):
    __tablename__ = 'conversation_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100))
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    feedback_score = Column(Integer, nullable=True) # 1-5 or thumb up/down
