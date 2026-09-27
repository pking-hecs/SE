from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from backend.app.models.schema import Project, User, Base
from backend.app.core.auth import auth_handler
from fastapi.security import OAuth2PasswordBearer
from backend.app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class ProjectCreate(BaseModel):
    name: str
    description: str = None
    owner_id: int

class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int

    class Config:
        from_attributes = True

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectOut)
async def create_project(project_in: ProjectCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth_handler.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    new_project = Project(name=project_in.name, description=project_in.description, owner_id=project_in.owner_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/", response_model=List[ProjectOut])
async def list_projects(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth_handler.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Filter by user role: Admin sees all, others see their own
    if payload["role"] == "ADMIN":
        return db.query(Project).all()

    return db.query(Project).filter(Project.owner_id == int(payload["sub"])).all()

@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth_handler.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project
