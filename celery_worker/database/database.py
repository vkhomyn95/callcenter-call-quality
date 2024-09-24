import logging
import sys
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, VARCHAR
from sqlalchemy import create_engine, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from celery_worker.variables import variables

Base = declarative_base()


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


class MariaDatabase:
    _database_instance = None

    @staticmethod
    def instance():
        return MariaDatabase._database_instance

    def __init__(self) -> None:
        if MariaDatabase._database_instance is None:
            try:
                self.engine = create_engine(
                    f"mariadb://"
                    f"{variables.mariadb_database_user}:"
                    f"{variables.mariadb_database_password}@"
                    f"{variables.mariadb_database_host}:"
                    f"{variables.mariadb_database_port}/"
                    f"{variables.mariadb_database_name}")

                self.SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
                Base.metadata.create_all(bind=self.engine)
                MariaDatabase._database_instance = self
                self.session = self.SessionLocal()

            except Exception as e:
                logging.error(f'  >> Error connecting to the database: {e}')
                sys.exit(1)
        else:
            raise Exception("{}: Cannot construct, an instance is already running.".format(__file__))

    def load_user_by_id(self, user_id: int):
        try:
            return self.session.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logging.error(f'  >> Error during query: {e}')
            self.session.rollback()
            return None


mariadb = MariaDatabase()
