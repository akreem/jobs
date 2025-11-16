from sqlalchemy import Column, Integer, String, Text
from db import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    keejob_id = Column(String)
    source = Column(String, default="keejob")
    title = Column(String)
    company = Column(String)
    location = Column(String)
    url = Column(String, unique=True)
    description = Column(Text)
    date_posted = Column(String)
