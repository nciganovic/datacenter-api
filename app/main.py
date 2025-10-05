from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import create_db, create_dummy_data
from app.routers import racks, devices

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    #create_dummy_data()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(racks.router)
app.include_router(devices.router)

@app.get("/")
def home():
    return {"hello": "world"}
