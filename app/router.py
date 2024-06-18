from fastapi import APIRouter
from app.api.v1.conference import router as conference_router
from app.api.v1.user import router as user_router


app_router = APIRouter()

app_router.include_router(router=conference_router, prefix="/v1/conference")
app_router.include_router(router=user_router, prefix="/v1/user")
