from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"hello": "world"}

@app.get("/test")
def test():
    return {"test": "passed"}