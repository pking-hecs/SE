from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.services.gemini_service import gemini_service
from backend.app.api.routes import auth, projects, analysis, approvals, history
from backend.app import history_store
from backend.app.models.schema import Base, Project, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI(title=settings.APP_NAME)

# Database Setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(analysis.router)
app.include_router(approvals.router)
app.include_router(history.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """
    Ensures that a default project exists so users can start chatting immediately.
    """
    history_store.initialize()
    db = SessionLocal()
    try:
        # 1. Ensure a default admin user exists
        admin = db.query(User).filter(User.email == "admin@bank.com").first()
        if not admin:
            from backend.app.core.auth import auth_handler
            admin = User(
                email="admin@bank.com",
                password_hash=auth_handler.hash_password("SecurePassword123"),
                role="ADMIN"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("Created default admin user: admin@bank.com")

        # 2. Ensure Project 1 exists
        project = db.query(Project).filter(Project.id == 1).first()
        if not project:
            project = Project(
                id=1,
                name="Digital Customer Onboarding",
                description="Default Demo Project",
                owner_id=admin.id
            )
            db.add(project)
            db.commit()
            print("Automatically created Project 1 for immediate use.")
    except Exception as e:
        print(f"Startup bootstrap error: {e}")
    finally:
        db.close()

@app.get("/api/system/health")
async def health_check():
    ai_ready = await gemini_service.health_check()
    return {
        "status": "healthy",
        "ai_engine": "ready" if ai_ready else "unavailable",
        "database": "connected",
        "redis": "connected"
    }

@app.get("/api/system/ai-status")
async def ai_status():
    ai_ready = await gemini_service.health_check()
    return {
        "model": "advanced-ai-flash",
        "base_url": "ai-api",
        "status": "ready" if ai_ready else "unavailable"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
