from fastapi import FastAPI
from database import Base, engine
from routers import members, sessions, trainers

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gym Management API", version="1.0.0")

app.include_router(members.router)
app.include_router(trainers.router)
app.include_router(sessions.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
