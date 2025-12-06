from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime


class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True)
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    event_date = Column(String, nullable=True)

    def display_event_date(self):
        return self.event_date if self.event_date else ''