import logging
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from .schemas import UserSchema
from .core import Base, UserRole, User, RecognitionConfiguration, Tariff
from communicator.variables import variables


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

                self.insert_default_roles()
                self.insert_default_user()

            except Exception as e:
                logging.error(f'  >> Error connecting to the database: {e}')
                sys.exit(1)
        else:
            raise Exception("{}: Cannot construct, an instance is already running.".format(__file__))

    def insert_default_roles(self) -> None:
        try:
            # Insert default roles if they do not exist
            default_roles = ['admin', 'guest']
            for role_name in default_roles:
                if not self.session.query(UserRole).filter(UserRole.name == role_name).first():
                    role = UserRole(name=role_name)
                    self.session.add(role)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f">>>Error inserting default roles: {e}")
        finally:
            self.session.close()

    def insert_default_user(self) -> UserSchema:
        try:
            if not self.session.query(User).filter(User.username == "admin").first():
                default_user = User(
                    username="admin",
                    password=generate_password_hash(variables.admin_default_password),
                    first_name="Administrator",
                    last_name="VoIPTime",
                    email="support@voiptime.net",
                    role_id=1,
                    tariff=Tariff(),
                    recognition=RecognitionConfiguration()
                )
                self.session.add(default_user)
                self.session.commit()
                return UserSchema.from_orm(default_user)
        except Exception as e:
            self.session.rollback()
            print(f">>>Error inserting default user: {e}")
        finally:
            self.session.close()

    def insert_user(self, user: User) -> UserSchema:
        try:
            self.session.add(user)
            self.session.commit()
            return UserSchema.from_orm(user)
        except Exception as e:
            self.session.rollback()
            print(f">>>Error inserting default user: {e}")
        finally:
            self.session.close()

    def load_user_by_api_key(self, api_key: str):
        try:
            return self.session.query(User).filter(User.api_key == api_key).first()
        except Exception as e:
            logging.error(f'  >> Error during query: {e}')
            self.session.rollback()
            return None

    def load_user_by_username(self, username: str, email: str) -> UserSchema:
        try:
            user = self.session.query(User).filter((User.username == username) | (User.email == email)).first()
            return UserSchema.from_orm(user)
        except Exception as e:
            logging.error(f'  >> Error during query: {e}')
            self.session.rollback()
            return None

    def load_user_by_id(self, user_id: int):
        try:
            return self.session.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logging.error(f'  >> Error during query: {e}')
            self.session.rollback()
            return None

    def load_user_by_uuid(self, user_uuid: str):
        try:
            return self.session.query(User).filter(User.uuid == user_uuid).first()
        except Exception as e:
            logging.error(f'  >> Error during query: {e}')
            self.session.rollback()
            return None

    def load_users(self, limit: int, offset: int, current_user_id: int):
        try:
            return self.session.query(User).filter(User.id != current_user_id).limit(limit).offset(offset).all()
        except Exception as e:
            logging.error(f'  >> Error during query: {e}')
            self.session.rollback()
            return None

    def count_users(self):
        try:
            return self.session.query(User).count()
        except Exception as e:
            logging.error(f'  >> Error during query: {e}')
            self.session.rollback()
            return 0

    def load_simple_users(self):
        try:
            return self.session.query(User).all()
        except Exception as e:
            logging.error(f'  >> Error during query: {e}')
            self.session.rollback()
            return None

    def increment_user_tariff(self, tariff_id: int, count: int):
        try:
            tariff = self.session.query(Tariff).filter_by(id=tariff_id).one()
            tariff.total += count
            self.session.commit()

        except Exception as e:
            logging.error(f'  >> Error: {e}')
            self.session.rollback()
            return {"success": False, "data": str(e)}

    def decrement_user_tariff(self, tariff_id: int, count: int):
        try:
            tariff = self.session.query(Tariff).filter_by(id=tariff_id).one()
            tariff.total -= count
            self.session.commit()

        except Exception as e:
            logging.error(f'  >> Error: {e}')
            self.session.rollback()
            return {"success": False, "data": str(e)}


mariadb = MariaDatabase()
