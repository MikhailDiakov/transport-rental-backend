from app.api.deps import get_current_user_info, get_session, limiter_dep
from app.core.security import create_access_token
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserProfileUpdate, UserRead
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_profile,
    update_user_profile,
)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[limiter_dep(3, 60)],
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_session),
):
    user = await create_user(db, user_in.username, user_in.email, user_in.password)
    return user


@router.post(
    "/login",
    response_model=Token,
    dependencies=[limiter_dep(5, 60)],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"id": str(user.id), "role": str(user.role_id)}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def get_my_user(
    current_user=Depends(get_current_user_info),
    db: AsyncSession = Depends(get_session),
):
    return await get_user_profile(db, current_user["id"])


@router.put("/me/update", response_model=UserRead)
async def update_my_profile(
    data: UserProfileUpdate,
    current_user=Depends(get_current_user_info),
    db: AsyncSession = Depends(get_session),
):
    try:
        user = await update_user_profile(
            db=db,
            user_id=current_user["id"],
            email=data.email,
            old_password=data.old_password,
            new_password=data.new_password,
            confirm_password=data.confirm_password,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
