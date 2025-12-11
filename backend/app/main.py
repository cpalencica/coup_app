from fastapi import FastAPI
from .routers import game as game_router

app = FastAPI(title="Coup Backend")

app.include_router(game_router.router, prefix="/games")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
