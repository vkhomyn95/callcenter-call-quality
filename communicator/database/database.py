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

# class AsyncDatabaseSession:
#     def __init__(self):
#         self._session = None
#         self._engine = None
#
#     def __getattr__(self, name):
#         return getattr(self._session, name)
#
#     def init(self):
#         self._engine = create_async_engine(
#         f"mariadb://"
#             f"{variables.mariadb_database_user}:"
#             f"{variables.mariadb_database_password}@"
#             f"{variables.mariadb_database_host}:"
#             f"{variables.mariadb_database_port}/"
#             f"{variables.mariadb_database_name}",
#             future=True,
#             echo=True,
#         )
#         self._session = sessionmaker(
#             self._engine, expire_on_commit=False, class_=AsyncSession
#         )()
#
#     async def create_all(self):
#         self._engine.begin
#
#
# db = AsyncDatabaseSession()
#
# database = create_engine(Config.SYNC_DB_CONFIG, echo=True)
#
# # ================
#
#
# engine = create_async_engine(
#     f"mariadb://"
#     f"{variables.mariadb_database_user}:"
#     f"{variables.mariadb_database_password}@"
#     f"{variables.mariadb_database_host}:"
#     f"{variables.mariadb_database_port}/"
#     f"{variables.mariadb_database_name}"
# )
#
# Base = declarative_base()
#
# async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# class MariaDatabase:
#     _database_instance = None
#
#     @staticmethod
#     def instance():
#         return MariaDatabase._database_instance
#
#     def __init__(self) -> None:
#         if MariaDatabase._database_instance is None:
#             try:
#                 self.engine = create_engine(
#                     f"mariadb://"
#                     f"{variables.mariadb_database_user}:"
#                     f"{variables.mariadb_database_password}@"
#                     f"{variables.mariadb_database_host}:"
#                     f"{variables.mariadb_database_port}/"
#                     f"{variables.mariadb_database_name}")
#
#                 self.SessionLocal = sessionmaker(
#                     autocommit=False,
#                     autoflush=False,
#                     bind=self.engine
#                 )
#                 Base.metadata.create_all(bind=self.engine)
#                 MariaDatabase._database_instance = self
#                 self.session = self.SessionLocal()
#
#                 self.insert_default_roles()
#                 self.insert_default_user()
#
#             except Exception as e:
#                 logging.error(f'  >> Error connecting to the database: {e}')
#                 sys.exit(1)
#         else:
#             raise Exception("{}: Cannot construct, an instance is already running.".format(__file__))


# def insert_default_roles(db: Session) -> None:
#     try:
#         # Insert default roles if they do not exist
#         default_roles = ['admin', 'guest']
#         for role_name in default_roles:
#             if not db.query(UserRole).filter(UserRole.name == role_name).first():
#                 role = UserRole(name=role_name)
#                 db.add(role)
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         print(f">>>Error inserting default roles: {e}")
#     finally:
#         db.close()
#
#
# def insert_default_user(db: Session) -> UserSchema:
#     try:
#         if not db.query(User).filter(User.username == "admin").first():
#             default_user = User(
#                 username="admin",
#                 password=generate_password_hash(variables.admin_default_password),
#                 first_name="Administrator",
#                 last_name="VoIPTime",
#                 email="support@voiptime.net",
#                 role_id=1,
#                 tariff=Tariff(),
#                 recognition=RecognitionConfiguration()
#             )
#             db.add(default_user)
#             db.commit()
#             return UserSchema.from_orm(default_user)
#     except Exception as e:
#         db.rollback()
#         print(f">>>Error inserting default user: {e}")
#     finally:
#         db.close()
#
#
# def insert_user(db: Session, user: User) -> UserSchema:
#     try:
#         db.add(user)
#         db.commit()
#         return UserSchema.from_orm(user)
#     except Exception as e:
#         db.rollback()
#         print(f">>>Error inserting default user: {e}")
#     finally:
#         db.close()
#
#
# def load_user_by_api_key(db: Session, api_key: str):
#     try:
#         return db.query(User).filter(User.api_key == api_key).first()
#     except Exception as e:
#         logging.error(f'  >> Error during query: {e}')
#         db.rollback()
#         return None
#
#
# def load_user_by_username(db: Session, username: str, email: str) -> UserSchema:
#     try:
#         user = db.query(User).filter((User.username == username) | (User.email == email)).first()
#         return UserSchema.from_orm(user)
#     except Exception as e:
#         logging.error(f'  >> Error during query: {e}')
#         db.rollback()
#         return None
#
#
# def load_user_by_id(db: Session, user_id: int):
#     try:
#         return db.query(User).filter(User.id == user_id).first()
#     except Exception as e:
#         logging.error(f'  >> Error during query: {e}')
#         db.rollback()
#         return None
#
#
# def load_user_by_uuid(db: Session, user_uuid: str):
#     try:
#         return db.query(User).filter(User.uuid == user_uuid).first()
#     except Exception as e:
#         logging.error(f'  >> Error during query: {e}')
#         db.rollback()
#         return None
#
#
# def load_users(db: Session, limit: int, offset: int, current_user_id: int):
#     try:
#         return db.query(User).filter(User.id != current_user_id).limit(limit).offset(offset).all()
#     except Exception as e:
#         logging.error(f'  >> Error during query: {e}')
#         db.rollback()
#         return None
#
#
# def count_users(db: Session):
#     try:
#         return db.query(User).count()
#     except Exception as e:
#         logging.error(f'  >> Error during query: {e}')
#         db.rollback()
#         return 0
#
#
# def load_simple_users(db: Session):
#     try:
#         return db.query(User).all()
#     except Exception as e:
#         logging.error(f'  >> Error during query: {e}')
#         db.rollback()
#         return None
#
#
# def increment_user_tariff(db: Session, tariff_id: int, count: int):
#     try:
#         tariff = db.query(Tariff).filter_by(id=tariff_id).one()
#         tariff.total += count
#         db.commit()
#
#     except Exception as e:
#         logging.error(f'  >> Error: {e}')
#         db.rollback()
#         return {"success": False, "data": str(e)}
#
#
# def decrement_user_tariff(db: Session, tariff_id: int, count: int):
#     try:
#         tariff = db.query(Tariff).filter_by(id=tariff_id).one()
#         tariff.total -= count
#         db.commit()
#
#     except Exception as e:
#         logging.error(f'  >> Error: {e}')
#         db.rollback()
#         return {"success": False, "data": str(e)}
#
