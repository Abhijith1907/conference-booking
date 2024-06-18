import uvicorn
from fastapi import FastAPI, APIRouter

from app.router import app_router


app = FastAPI(title="Conference Booking application")

app.include_router(app_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
