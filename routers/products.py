from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal

router = APIRouter(prefix="/products", tags=["Products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    product_id = crud.create_entry(db, models.Product, product, return_id=True)
    return {"product_id": product_id}

@router.get("/", response_model=list[schemas.Product])
def read_products(db: Session = Depends(get_db)):
    products = crud.get_all(db, models.Product)
    return [{"productId": p.id,
             "category": p.category,
             "name": p.name,
             "description": p.description,
             "price": p.price} for p in products]


@router.get("/category/{category}", response_model=list[schemas.Product])
def get_products_by_category(category: str, db: Session = Depends(get_db)):
    products = crud.get_products_by_category(db, category)
    return [{"productId": p.id,
             "category": p.category,
             "name": p.name,
             "description": p.description,
             "price": p.price} for p in products]

@router.get("/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_by_id(db, models.Product, "id", product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"productId": product.id,
            "category": product.category,
            "name": product.name,
            "description": product.description,
            "price": product.price}

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    success = crud.delete_by_id(db, models.Product, "id", product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@router.put("/{product_id}")
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    success = crud.update_by_id(db, models.Product, "id", product_id, product)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}