from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from starlette.requests import Request
from werkzeug.security import generate_password_hash

from communicator.database import UserSchema, RecognitionConfiguration, Tariff, User
from communicator.database.database import get_db
from communicator.utils.crud import load_user_by_uuid, load_user_by_username, insert_user, increment_user_tariff
from communicator.variables import variables

router = APIRouter()


@router.get("/{uuid}")
async def get_user(
        uuid: str,
        access_token: str = Query(None, alias="access_token"),
        db: Session = Depends(get_db)
):
    if not access_token or access_token == "":
        return {"success": False, "data": "Invalid access token"}

    if not uuid or uuid == "":
        return {"success": False, "data": "Invalid UUID"}

    if access_token != variables.license_server_access_token:
        return {"success": False, "data": "Invalid access token"}

    user = load_user_by_uuid(db, uuid)

    return {
        "success": True,
        "data": UserSchema().model_validate(user).model_dump(exclude=("recognition", "role", "password"))
    }


@router.post("")
async def create_user(
        request: Request,
        access_token: str = Query(None, alias="access_token"),
        db: Session = Depends(get_db)
):
    if not access_token or access_token == "":
        return {"success": False, "data": "Invalid access token"}

    if access_token != variables.license_server_access_token:
        return {"success": False, "data": "Invalid access token"}

    payload = await request.json()

    if "uuid" not in payload:
        return {"success": False, "data": "Missing uuid"}

    user = load_user_by_uuid(db, payload["uuid"])

    if user is not None:
        return {"success": False, "data": "User already exists"}

    if "password" not in payload:
        return {"success": False, "data": "Missing password"}

    if "username" not in payload:
        return {"success": False, "data": "Missing username"}

    user = load_user_by_username(db, payload["username"], payload["email"])
    if user is not None:
        return {"success": False, "data": "User already exists with defined email or username"}

    user_schema = UserSchema(**payload)
    user_schema.role_id = 2
    user_schema.password = generate_password_hash(payload["password"])
    user_schema.tariff = Tariff()
    user_schema.recognition = RecognitionConfiguration()

    inserted_user = insert_user(db, User(**user_schema.model_dump()))

    return {
        "success": True,
        "data": UserSchema().model_validate(inserted_user).model_dump(exclude=("recognition", "role", "password"))
    }


@router.post("/<uuid>/license")
def increment_user_license(
        uuid: str,
        access_token: str = Query(None, alias="access_token"),
        count: int = Query(0, alias="count"),
        db: Session = Depends(get_db)
):
    if not access_token or access_token == "":
        return {"success": False, "data": "Invalid access token"}

    if not uuid or uuid == "":
        return {"success": False, "data": "Invalid UUID"}

    if access_token != variables.license_server_access_token:
        return {"success": False, "data": "Invalid access token"}

    if not count or count == 0:
        return {"success": False, "data": "Invalid license count, should be greater than 0"}

    user = load_user_by_uuid(db, uuid)

    if not user:
        return {"success": False, "data": "User does not exist with requested uuid"}

    increment_user_tariff(db, user.tariff.id, count)

    return {"success": True, "data": "Successfully incremented user tariff"}
