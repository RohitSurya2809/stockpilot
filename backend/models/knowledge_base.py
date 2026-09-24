"""
Knowledge Base Model for LLM Assistant RAG
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, func, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from models.database import Base


class KnowledgeBase(Base):
    """
    Knowledge base for lightweight RAG using PostgreSQL Full-Text Search.

    Stores business context, definitions, policies, and FAQs for the LLM assistant.
    """
    __tablename__ = "knowledge_base"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Knowledge Classification
    category = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Category: policy, definition, process, faq, explanation"
    )

    # Searchable Content
    key = Column(String(200), nullable=False, index=True, comment="Searchable keywords/title")
    content = Column(Text, nullable=False, comment="The actual knowledge content")

    # Full-Text Search Vector
    tsv = Column(TSVECTOR, nullable=True, comment="Full-text search vector")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Record creation time")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Record last update time")

    def __repr__(self):
        return f"<KnowledgeBase(category='{self.category}', key='{self.key}')>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "category": self.category,
            "key": self.key,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Create Full-Text Search Index
# This will be created when tables are initialized
__table_args__ = (
    Index(
        'idx_knowledge_fts',
        'tsv',
        postgresql_using='gin'
    ),
)
