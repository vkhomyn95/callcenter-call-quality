from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, VARCHAR, Boolean
from sqlalchemy.orm import relationship

from communicator.database.database import Base, engine


class Tariff(Base):
    __tablename__ = "tariff"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.utcnow(), nullable=True)
    updated_date = Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow(), nullable=True)
    active = Column(Boolean, default=False)
    total = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey('user.id'), unique=True)

    user = relationship("User", back_populates="tariff")


class UserRole(Base):
    __tablename__ = "user_role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(128), nullable=True)

    users = relationship('User', back_populates='role')


class RecognitionConfiguration(Base):
    __tablename__ = "recognition_configuration"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(VARCHAR(128))
    task_id = Column(VARCHAR(128))
    batch_size = Column(Integer, default=1)
    chunk_length = Column(Integer, default=30)
    sample_rate = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'), unique=True)

    user = relationship('User', back_populates='recognition', uselist=False, foreign_keys=[user_id])


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.utcnow(), nullable=True)
    updated_date = Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow(), nullable=True)
    first_name = Column(VARCHAR(128), nullable=True)
    last_name = Column(VARCHAR(128), nullable=True)
    email = Column(VARCHAR(255), nullable=True)
    phone = Column(VARCHAR(128), nullable=True)
    username = Column(VARCHAR(128), unique=True, nullable=True)
    password = Column(VARCHAR(255), nullable=True)
    api_key = Column(VARCHAR(255), nullable=True)
    uuid = Column(VARCHAR(255), nullable=True)
    audience = Column(VARCHAR(255), nullable=True)
    role_id = Column(Integer, ForeignKey('user_role.id'))

    tariff = relationship('Tariff', uselist=False, back_populates="user")
    recognition = relationship('RecognitionConfiguration', uselist=False, back_populates="user")
    role = relationship('UserRole', back_populates='users')


Base.metadata.create_all(engine)