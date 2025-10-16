"""AI生成日志模型"""
from sqlalchemy import Column, Integer, String, DateTime, func, Index
from app.core.database import Base


class AIGenerationLog(Base):
    """AI生成日志"""
    __tablename__ = "ai_generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, comment="用户ID，游客为NULL")
    ip_address = Column(String(50), nullable=False, comment="IP地址")
    word = Column(String(100), nullable=False, comment="生成的单词")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    __table_args__ = (
        Index('idx_ai_gen_user_date', 'user_id', 'created_at'),
        Index('idx_ai_gen_ip_date', 'ip_address', 'created_at'),
    )
