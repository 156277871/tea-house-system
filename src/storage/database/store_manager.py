from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from storage.database.shared.model import Store, StoreStatus


class StoreCreate(BaseModel):
    name: str = Field(..., description="门店名称")
    code: str = Field(..., description="门店编码")
    address: str = Field(..., description="门店地址")
    phone: str = Field(..., description="联系电话")
    manager_name: Optional[str] = Field(None, description="店长姓名")
    manager_phone: Optional[str] = Field(None, description="店长电话")
    open_time: Optional[str] = Field(None, description="营业开始时间")
    close_time: Optional[str] = Field(None, description="营业结束时间")


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    status: Optional[StoreStatus] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None


class StoreManager:
    """门店管理 Manager"""

    def create_store(self, db: Session, store_in: StoreCreate) -> Store:
        """创建门店"""
        store_data = store_in.model_dump()
        store_data['status'] = StoreStatus.ACTIVE
        db_store = Store(**store_data)
        db.add(db_store)
        try:
            db.commit()
            db.refresh(db_store)
            return db_store
        except Exception:
            db.rollback()
            raise

    def get_stores(self, db: Session, skip: int = 0, limit: int = 100,
                   status: Optional[StoreStatus] = None) -> List[Store]:
        """获取门店列表"""
        query = db.query(Store)
        if status:
            query = query.filter(Store.status == status)
        return query.order_by(Store.id).offset(skip).limit(limit).all()

    def get_store_by_id(self, db: Session, store_id: int) -> Optional[Store]:
        """根据ID获取门店"""
        return db.query(Store).filter(Store.id == store_id).first()

    def get_store_by_code(self, db: Session, code: str) -> Optional[Store]:
        """根据编码获取门店"""
        return db.query(Store).filter(Store.code == code).first()

    def update_store(self, db: Session, store_id: int,
                     store_in: StoreUpdate) -> Optional[Store]:
        """更新门店信息"""
        db_store = self.get_store_by_id(db, store_id)
        if not db_store:
            return None
        update_data = store_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_store, field):
                setattr(db_store, field, value)
        db.add(db_store)
        try:
            db.commit()
            db.refresh(db_store)
            return db_store
        except Exception:
            db.rollback()
            raise

    def delete_store(self, db: Session, store_id: int) -> bool:
        """删除门店"""
        db_store = self.get_store_by_id(db, store_id)
        if not db_store:
            return False
        # 软删除，改为inactive状态
        db_store.status = StoreStatus.INACTIVE
        db.add(db_store)
        try:
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise

    def get_active_stores(self, db: Session) -> List[Store]:
        """获取所有活跃门店"""
        return db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()

    def count_stores(self, db: Session, status: Optional[StoreStatus] = None) -> int:
        """统计门店数量"""
        query = db.query(Store)
        if status:
            query = query.filter(Store.status == status)
        return query.count()
