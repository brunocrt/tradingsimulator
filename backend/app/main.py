from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Autonomous Multi-Agent Stock Trading Simulator",
    description="Risk-first stock trading research and paper-trading simulation API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict:
    return {
        "name": "Autonomous Multi-Agent Stock Trading Simulator",
        "liveTradingEnabled": False,
        "docs": "/docs",
    }

