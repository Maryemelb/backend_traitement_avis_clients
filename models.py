from datetime import datetime, timezone
from database import Base
from sqlalchemy import TIMESTAMP, Column, String, Integer, DateTime,ForeignKey, text
class User(Base):
    __tablename__ = 'User'
    id= Column(Integer, primary_key= True)
    email= Column(String, unique=True, nullable=False)
    password= Column(String, nullable=False)
    token=Column(String, nullable=True)
    created_at=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Avis(Base):
    __tablename__= 'Avis'
    id= Column(Integer, primary_key= True)
    comment= Column(String, nullable=False)
    score=Column(String, nullable=True)
    created_at=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user_id= Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), nullable=False )