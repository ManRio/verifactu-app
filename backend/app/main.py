from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.business import router as business_router
from app.db.session import get_db

app = FastAPI(
    title="Verifactu APP",
    version="0.1.0",
)

app.include_router(business_router)

@app.get("/health")
def health_check():
    return {"status":"ok"}

@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()

    return{
        "status": "ok",
        "database": result,
    }