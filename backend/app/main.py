from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.business import router as business_router
from app.api.routes.product import router as product_router
from app.api.routes.user import router as user_router
from app.db.session import get_db

app = FastAPI(
    title="Verifactu APP",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(business_router)
app.include_router(user_router)
app.include_router(product_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check(
    db: Session = Depends(get_db),
):
    result = db.execute(
        text("SELECT 1")
    ).scalar()

    return {
        "status": "ok",
        "database": result,
    }