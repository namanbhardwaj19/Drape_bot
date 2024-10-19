from fastapi import FastAPI
from src import drape

app = FastAPI()
app.include_router(drape)
