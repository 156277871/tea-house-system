from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from storage.database.shared.model import Inventory, InventoryLog, InventoryChangeType


class InventoryCreate(BaseModel):
    store_id: int = Field(..., description="门店ID")
    product_id: int = Field(..., description="商品ID")
    quantity: float = Field(default=0.0, description="初始库存数量")
    warning_threshold: float = Field(default=10.0, description="预警阈值")


class InventoryUpdate(BaseModel):
    quantity: Optional[float] = None
    warning_threshold: Optional[float] = None


class InventoryManager:
    """库存管理 Manager"""

    def create_inventory(self, db: Session, inventory_in: InventoryCreate) -> Inventory:
        """创建库存记录"""
        inventory_data = inventory_in.model_dump()
        db_inventory = Inventory(**inventory_data)
        db.add(db_inventory)
        try:
            db.commit()
            db.refresh(db_inventory)
            return db_inventory
        except Exception:
            db.rollback()
            raise

    def get_inventories(self, db: Session, skip: int = 0, limit: int = 100,
                       store_id: Optional[int] = None,
                       product_id: Optional[int] = None,
                       low_stock_only: bool = False) -> List[Inventory]:
        """获取库存列表"""
        query = db.query(Inventory)
        if store_id:
            query = query.filter(Inventory.store_id == store_id)
        if product_id:
            query = query.filter(Inventory.product_id == product_id)
        if low_stock_only:
            query = query.filter(Inventory.quantity <= Inventory.warning_threshold)
        return query.order_by(Inventory.id).offset(skip).limit(limit).all()

    def get_inventory_by_id(self, db: Session, inventory_id: int) -> Optional[Inventory]:
        """根据ID获取库存"""
        return db.query(Inventory).filter(Inventory.id == inventory_id).first()

    def get_store_inventory(self, db: Session, store_id: int,
                           product_id: int) -> Optional[Inventory]:
        """获取指定门店的商品库存"""
        return db.query(Inventory).filter(
            Inventory.store_id == store_id,
            Inventory.product_id == product_id
        ).first()

    def update_inventory(self, db: Session, inventory_id: int,
                        inventory_in: InventoryUpdate) -> Optional[Inventory]:
        """更新库存信息"""
        db_inventory = self.get_inventory_by_id(db, inventory_id)
        if not db_inventory:
            return None
        update_data = inventory_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_inventory, field):
                setattr(db_inventory, field, value)
        db.add(db_inventory)
        try:
            db.commit()
            db.refresh(db_inventory)
            return db_inventory
        except Exception:
            db.rollback()
            raise

    def adjust_inventory(self, db: Session, store_id: int, product_id: int,
                        quantity: float, operation_type: str,
                        operator_id: Optional[int] = None,
                        remark: Optional[str] = None) -> Inventory:
        """
        调整库存（入库、出库、调拨）
        quantity: 变动数量，正数为入库，负数为出库
        operation_type: 操作类型（purchase采购/sale销售/adjust调整/loss损耗）
        """
        db_inventory = self.get_store_inventory(db, store_id, product_id)
        if not db_inventory:
            # 如果库存记录不存在，创建新的
            db_inventory = self.create_inventory(
                db, InventoryCreate(
                    store_id=store_id,
                    product_id=product_id,
                    quantity=0.0,
                    warning_threshold=10.0
                )
            )
            db.refresh(db_inventory)

        before_quantity = db_inventory.quantity
        after_quantity = before_quantity + quantity

        if after_quantity < 0:
            raise ValueError("库存不足，无法出库")

        # 更新库存
        db_inventory.quantity = after_quantity
        db.add(db_inventory)

        # 记录库存变动日志
        change_type = InventoryChangeType.IN if quantity > 0 else InventoryChangeType.OUT
        log = InventoryLog(
            store_id=store_id,
            product_id=product_id,
            change_type=change_type,
            quantity=abs(quantity),
            before_quantity=before_quantity,
            after_quantity=after_quantity,
            operation_type=operation_type,
            remark=remark,
            operator_id=operator_id
        )
        db.add(log)

        try:
            db.commit()
            db.refresh(db_inventory)
            return db_inventory
        except Exception:
            db.rollback()
            raise

    def get_low_stock_items(self, db: Session, store_id: Optional[int] = None) -> List[Inventory]:
        """获取库存预警商品"""
        query = db.query(Inventory).filter(
            Inventory.quantity <= Inventory.warning_threshold
        )
        if store_id:
            query = query.filter(Inventory.store_id == store_id)
        return query.order_by(Inventory.quantity).all()

    def get_inventory_logs(self, db: Session, skip: int = 0, limit: int = 100,
                          store_id: Optional[int] = None,
                          product_id: Optional[int] = None) -> List[InventoryLog]:
        """获取库存变动日志"""
        query = db.query(InventoryLog)
        if store_id:
            query = query.filter(InventoryLog.store_id == store_id)
        if product_id:
            query = query.filter(InventoryLog.product_id == product_id)
        return query.order_by(InventoryLog.created_at.desc()).offset(skip).limit(limit).all()

    def get_inventory_summary(self, db: Session, store_id: Optional[int] = None) -> dict:
        """获取库存汇总信息"""
        query = db.query(Inventory)
        if store_id:
            query = query.filter(Inventory.store_id == store_id)

        inventories = query.all()
        total_items = len(inventories)
        low_stock_count = sum(1 for inv in inventories if inv.quantity <= inv.warning_threshold)

        # 计算总库存价值（需要关联Product获取价格）
        from storage.database.shared.model import Product
        total_value = 0.0
        for inv in inventories:
            product = db.query(Product).filter(Product.id == inv.product_id).first()
            if product:
                total_value += inv.quantity * product.cost_price if product.cost_price else 0

        return {
            "total_items": total_items,
            "low_stock_count": low_stock_count,
            "total_value": total_value
        }

    def batch_adjust_inventory(self, db: Session, items: list,
                              operation_type: str,
                              operator_id: Optional[int] = None) -> dict:
        """
        批量调整库存
        items: [{"store_id": int, "product_id": int, "quantity": float, "remark": str}]
        """
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for item in items:
            try:
                self.adjust_inventory(
                    db=db,
                    store_id=item["store_id"],
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    operation_type=operation_type,
                    operator_id=operator_id,
                    remark=item.get("remark")
                )
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "store_id": item["store_id"],
                    "product_id": item["product_id"],
                    "error": str(e)
                })

        return results
