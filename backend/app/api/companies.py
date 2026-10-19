from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/api/companies", tags=["Company Management"])

@router.get("", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    return db.scalars(select(Company).order_by(Company.name)).all()

@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    existing_name = db.scalar(select(Company).where(Company.name == payload.name))
    if existing_name:
        raise HTTPException(status_code=409, detail="Company name already exists")

    existing_code = db.scalar(select(Company).where(Company.code == payload.code))
    if existing_code:
        raise HTTPException(status_code=409, detail="Company code already exists")

    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: UUID, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: UUID, payload: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    values = payload.model_dump(exclude_unset=True)

    if "name" in values:
        duplicate = db.scalar(select(Company).where(Company.name == values["name"], Company.id != company_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Company name already exists")

    if "code" in values:
        duplicate = db.scalar(select(Company).where(Company.code == values["code"], Company.id != company_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Company code already exists")

    for key, value in values.items():
        setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return company

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: UUID, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.is_active = False
    db.commit()
