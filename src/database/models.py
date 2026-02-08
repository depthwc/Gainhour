from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Activity(Base):
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True)
    type = Column(String)  # 'app' or 'irl'
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    icon_path = Column(String, nullable=True)
    discord_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    logs = relationship("ActivityLog", back_populates="activity")

    def __repr__(self):
        return f"<Activity(name='{self.name}', type='{self.type}')>"

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    
    activity = relationship("Activity", back_populates="logs")

    def __repr__(self):
        return f"<ActivityLog(activity_id='{self.activity_id}', start='{self.start_time}')>"

class Setting(Base):
    __tablename__ = 'settings'
    
    key = Column(String, primary_key=True)
    value = Column(String)

def init_db(db_path="gainhour.db"):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
