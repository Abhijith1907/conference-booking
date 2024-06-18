from fastapi import APIRouter, Request, status
from models.user import User
from models.exceptions import UserExists
from starlette.responses import JSONResponse


from app.utils.db_utils import LocalDB


router = APIRouter()

user_registry = LocalDB("user")


@router.post("")
def create_user(user: User, request: Request):
    """
    Creates a new user with the given payload
    """
    user = user.dict(exclude_unset=True)

    try:

        user_exists = user_registry.get_record(user["user_id"])
        if user_exists == False:
            user_record = user_registry.create_record(user, "user_id")
        else:
            raise UserExists()

        resp = {"data": user_record}
        status_code = status.HTTP_201_CREATED

    except UserExists as e:
        resp = {"error": {"code": 409, "message": "User already exists"}}
        status_code = status.HTTP_409_CONFLICT

    return JSONResponse(resp, status_code=status_code)
