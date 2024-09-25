import logging

from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from communicator.database import UserRole, UserSchema, User, RecognitionConfiguration, Tariff
from communicator.variables import variables


def insert_default_roles(db: Session) -> None:
    try:
        # Insert default roles if they do not exist
        default_roles = ['admin', 'guest']
        for role_name in default_roles:
            if not db.query(UserRole).filter(UserRole.name == role_name).first():
                role = UserRole(name=role_name)
                db.add(role)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f">>>Error inserting default roles: {e}")
    finally:
        db.close()


def insert_default_user(db: Session) -> UserSchema:
    try:
        if not db.query(User).filter(User.username == "admin").first():
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
            db.add(default_user)
            db.commit()
            return UserSchema.from_orm(default_user)
    except Exception as e:
        db.rollback()
        print(f">>>Error inserting default user: {e}")
    finally:
        db.close()


def insert_user(db: Session, user: User) -> UserSchema:
    try:
        db.add(user)
        db.commit()
        return UserSchema.from_orm(user)
    except Exception as e:
        db.rollback()
        print(f">>>Error inserting default user: {e}")
    finally:
        db.close()


def load_user_by_api_key(db: Session, api_key: str):
    try:
        return db.query(User).filter(User.api_key == api_key).first()
    except Exception as e:
        logging.error(f'  >> Error during query: {e}')
        db.rollback()
        return None


def load_user_by_username(db: Session, username: str, email: str) -> UserSchema:
    try:
        user = db.query(User).filter((User.username == username) | (User.email == email)).first()
        return UserSchema.from_orm(user)
    except Exception as e:
        logging.error(f'  >> Error during query: {e}')
        db.rollback()
        return None


def load_user_by_id(db: Session, user_id: int):
    try:
        return db.query(User).filter(User.id == user_id).first()
    except Exception as e:
        logging.error(f'  >> Error during query: {e}')
        db.rollback()
        return None


def load_user_by_uuid(db: Session, user_uuid: str):
    try:
        return db.query(User).filter(User.uuid == user_uuid).first()
    except Exception as e:
        logging.error(f'  >> Error during query: {e}')
        db.rollback()
        return None


def load_users(db: Session, limit: int, offset: int, current_user_id: int):
    try:
        return db.query(User).filter(User.id != current_user_id).limit(limit).offset(offset).all()
    except Exception as e:
        logging.error(f'  >> Error during query: {e}')
        db.rollback()
        return None


def count_users(db: Session):
    try:
        return db.query(User).count()
    except Exception as e:
        logging.error(f'  >> Error during query: {e}')
        db.rollback()
        return 0


def load_simple_users(db: Session):
    try:
        return db.query(User).all()
    except Exception as e:
        logging.error(f'  >> Error during query: {e}')
        db.rollback()
        return None


def increment_user_tariff(db: Session, tariff_id: int, count: int):
    try:
        tariff = db.query(Tariff).filter_by(id=tariff_id).one()
        tariff.total += count
        db.commit()

    except Exception as e:
        logging.error(f'  >> Error: {e}')
        db.rollback()
        return {"success": False, "data": str(e)}


def decrement_user_tariff(db: Session, tariff_id: int, count: int):
    try:
        tariff = db.query(Tariff).filter_by(id=tariff_id).one()
        tariff.total -= count
        db.commit()

    except Exception as e:
        logging.error(f'  >> Error: {e}')
        db.rollback()
        return {"success": False, "data": str(e)}

