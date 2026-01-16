from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from storage.database.shared.model import Product


class ProductCreate(BaseModel):
    name: str = Field(..., description="商品名称")
    code: str = Field(..., description="商品编码")
    category: str = Field(..., description="商品分类")
    price: float = Field(..., description="单价")
    cost_price: Optional[float] = Field(None, description="成本价")
    unit: str = Field(..., description="单位")
    description: Optional[str] = Field(None, description="商品描述")
    image_url: Optional[str] = Field(None, description="商品图片URL")


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[bool] = None


class ProductManager:
    """商品管理 Manager"""

    def create_product(self, db: Session, product_in: ProductCreate) -> Product:
        """创建商品"""
        product_data = product_in.model_dump()
        product_data['status'] = True
        db_product = Product(**product_data)
        db.add(db_product)
        try:
            db.commit()
            db.refresh(db_product)
            return db_product
        except Exception:
            db.rollback()
            raise

    def get_products(self, db: Session, skip: int = 0, limit: int = 100,
                     category: Optional[str] = None,
                     status: Optional[bool] = None,
                     keyword: Optional[str] = None) -> List[Product]:
        """获取商品列表"""
        query = db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        if status is not None:
            query = query.filter(Product.status == status)
        if keyword:
            query = query.filter(
                (Product.name.like(f"%{keyword}%")) |
                (Product.code.like(f"%{keyword}%"))
            )
        return query.order_by(Product.id).offset(skip).limit(limit).all()

    def get_product_by_id(self, db: Session, product_id: int) -> Optional[Product]:
        """根据ID获取商品"""
        return db.query(Product).filter(Product.id == product_id).first()

    def get_product_by_code(self, db: Session, code: str) -> Optional[Product]:
        """根据编码获取商品"""
        return db.query(Product).filter(Product.code == code).first()

    def update_product(self, db: Session, product_id: int,
                      product_in: ProductUpdate) -> Optional[Product]:
        """更新商品信息"""
        db_product = self.get_product_by_id(db, product_id)
        if not db_product:
            return None
        update_data = product_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_product, field):
                setattr(db_product, field, value)
        db.add(db_product)
        try:
            db.commit()
            db.refresh(db_product)
            return db_product
        except Exception:
            db.rollback()
            raise

    def delete_product(self, db: Session, product_id: int) -> bool:
        """删除商品（软删除）"""
        db_product = self.get_product_by_id(db, product_id)
        if not db_product:
            return False
        db_product.status = False
        db.add(db_product)
        try:
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise

    def get_categories(self, db: Session) -> List[str]:
        """获取所有商品分类"""
        from sqlalchemy import distinct
        categories = db.query(distinct(Product.category)).filter(
            Product.status == True
        ).all()
        return [c[0] for c in categories if c[0]]

    def count_products(self, db: Session, category: Optional[str] = None) -> int:
        """统计商品数量"""
        query = db.query(Product).filter(Product.status == True)
        if category:
            query = query.filter(Product.category == category)
        return query.count()
