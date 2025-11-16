# models.py
from sqlalchemy import Column, String, Text, Float
from database import Base

class HelpRequest(Base):
    __tablename__ = "help_requests"
    id = Column(String, primary_key=True, index=True)
    supervisor_id = Column(String, index=True)
    customer_id = Column(String)
    question = Column(Text)
    answer = Column(Text, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(Float)
    resolved_at = Column(Float, nullable=True)

class KnowledgeEntry(Base):
    __tablename__ = "knowledge_base"
    topic_key = Column(String, primary_key=True, index=True)
    question = Column(Text)
    answer = Column(Text)
    verified_by = Column(String)
    timestamp = Column(Float)

class Supervisor(Base):
    __tablename__ = "supervisors"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
