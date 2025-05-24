# KREDILAKAY/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.routes import api_router

app = FastAPI(title="KrediLakay API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    # Initialize database connection
    if not engine.dialect.has_table(engine, "users"):
        from app.models.base import Base
        Base.metadata.create_all(bind=engine)
