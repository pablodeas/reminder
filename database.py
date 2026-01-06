from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

db_path = f'{BASE_DIR}/data/database.db'

#engine = create_engine('sqlite:///data/database.db')
engine = create_engine(f'sqlite:///{db_path}')
Base = declarative_base()
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
