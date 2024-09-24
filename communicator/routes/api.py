from fastapi import APIRouter, Query

from starlette.requests import Request
from werkzeug.security import generate_password_hash

from communicator.database import mariadb, UserSchema, RecognitionConfiguration, Tariff, User
from communicator.variables import variables

router = APIRouter()


@router.get("/{uuid}")
async def get_user(uuid: str, access_token: str = Query(None, alias="access_token")):
    if not access_token or access_token == "":
        return {"success": False, "data": "Invalid access token"}

    if not uuid or uuid == "":
        return {"success": False, "data": "Invalid UUID"}

    if access_token != variables.license_server_access_token:
        return {"success": False, "data": "Invalid access token"}

    user = mariadb.load_user_by_uuid(uuid)

    return {
        "success": True,
        "data": UserSchema().model_validate(user).model_dump(exclude=("recognition", "role", "password"))
    }


@router.post("")
async def create_user(request: Request, access_token: str = Query(None, alias="access_token")):
    if not access_token or access_token == "":
        return {"success": False, "data": "Invalid access token"}

    if access_token != variables.license_server_access_token:
        return {"success": False, "data": "Invalid access token"}

    payload = await request.json()

    if "uuid" not in payload:
        return {"success": False, "data": "Missing uuid"}

    user = mariadb.load_user_by_uuid(payload["uuid"])

    if user is not None:
        return {"success": False, "data": "User already exists"}

    if "password" not in payload:
        return {"success": False, "data": "Missing password"}

    if "username" not in payload:
        return {"success": False, "data": "Missing username"}

    user = mariadb.load_user_by_username(payload["username"], payload["email"])
    if user is not None:
        return {"success": False, "data": "User already exists with defined email or username"}

    user_schema = UserSchema(**payload)
    user_schema.role_id = 2
    user_schema.password = generate_password_hash(payload["password"])
    user_schema.tariff = Tariff()
    user_schema.recognition = RecognitionConfiguration()

    inserted_user = mariadb.insert_user(User(**user_schema.model_dump()))

    return {
        "success": True,
        "data": UserSchema().model_validate(inserted_user).model_dump(exclude=("recognition", "role", "password"))
    }


@router.post("/<uuid>/license")
def increment_user_license(
        uuid: str,
        access_token: str = Query(None, alias="access_token"),
        count: int = Query(0, alias="count")
):
    if not access_token or access_token == "":
        return {"success": False, "data": "Invalid access token"}

    if not uuid or uuid == "":
        return {"success": False, "data": "Invalid UUID"}

    if access_token != variables.license_server_access_token:
        return {"success": False, "data": "Invalid access token"}

    if not count or count == 0:
        return {"success": False, "data": "Invalid license count, should be greater than 0"}

    user = mariadb.load_user_by_uuid(uuid)

    if not user:
        return {"success": False, "data": "User does not exist with requested uuid"}

    mariadb.increment_user_tariff(user.tariff.id, count)

    return {"success": True, "data": "Successfully incremented user tariff"}
