import logging
import sys

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from werkzeug.security import generate_password_hash

from communicator.database import UserSchema
# from .core import UserRole, User, Tariff, RecognitionConfiguration
from communicator.variables import variables

# ================
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


engine = create_engine(
    f"mariadb://"
    f"{variables.mariadb_database_user}:"
    f"{variables.mariadb_database_password}@"
    f"{variables.mariadb_database_host}:"
    f"{variables.mariadb_database_port}/"
    f"{variables.mariadb_database_name}"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
