from fastapi import APIRouter, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError

from app.database import get_users_collection
from app.schemas import Token, UserLogin, UserSignup
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignup):
    users: AsyncIOMotorCollection = get_users_collection()

    try:
        result = await users.insert_one(
            {"email": user.email, "hashed_password": hash_password(user.password)}
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    access_token = create_access_token(subject=str(result.inserted_id))
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    users: AsyncIOMotorCollection = get_users_collection()
    existing_user = await users.find_one({"email": user.email})

    if not existing_user or not verify_password(user.password, existing_user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(subject=str(existing_user["_id"]))
    return Token(access_token=access_token)
