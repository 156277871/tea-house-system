from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from storage.database.shared.model import Order, OrderItem, OrderStatus, PaymentMethod


class OrderItemCreate(BaseModel):
    product_id: int = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    quantity: float = Field(..., description="数量")
    unit_price: float = Field(..., description="单价")
    remark: Optional[str] = Field(None, description="备注")


class OrderCreate(BaseModel):
    store_id: int = Field(..., description="门店ID")
    member_id: Optional[int] = Field(None, description="会员ID")
    items: List[OrderItemCreate] = Field(..., description="订单明细")
    payment_method: PaymentMethod = Field(..., description="支付方式")
    remark: Optional[str] = Field(None, description="备注")


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    remark: Optional[str] = None


class OrderManager:
    """订单管理 Manager"""

    def __init__(self):
        self.order_no_prefix = "ORD"

    def _generate_order_no(self, db: Session) -> str:
        """生成订单编号"""
        today = datetime.now().strftime("%Y%m%d")
        count = db.query(Order).filter(
            Order.order_no.like(f"{self.order_no_prefix}{today}%")
        ).count()
        return f"{self.order_no_prefix}{today}{count + 1:06d}"

    def create_order(self, db: Session, order_in: OrderCreate) -> Order:
        """创建订单"""
        order_data = order_in.model_dump(exclude={'items'})

        # 计算订单金额
        items_data = order_in.items
        total_amount = sum(item.unit_price * item.quantity for item in items_data)
        discount_amount = 0.0
        paid_amount = total_amount - discount_amount

        order_data.update({
            'order_no': self._generate_order_no(db),
            'total_amount': total_amount,
            'discount_amount': discount_amount,
            'paid_amount': paid_amount,
            'status': OrderStatus.PENDING
        })

        db_order = Order(**order_data)
        db.add(db_order)
        db.flush()  # 获取订单ID

        # 创建订单明细
        for item_data in items_data:
            item_dict = item_data.model_dump()
            item_dict['order_id'] = db_order.id
            item_dict['subtotal'] = item_dict['quantity'] * item_dict['unit_price']
            db_order_item = OrderItem(**item_dict)
            db.add(db_order_item)

        try:
            db.commit()
            db.refresh(db_order)
            return db_order
        except Exception:
            db.rollback()
            raise

    def get_orders(self, db: Session, skip: int = 0, limit: int = 100,
                   store_id: Optional[int] = None,
                   member_id: Optional[int] = None,
                   status: Optional[OrderStatus] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Order]:
        """获取订单列表"""
        query = db.query(Order)
        if store_id:
            query = query.filter(Order.store_id == store_id)
        if member_id:
            query = query.filter(Order.member_id == member_id)
        if status:
            query = query.filter(Order.status == status)
        if start_date:
            query = query.filter(Order.order_time >= start_date)
        if end_date:
            query = query.filter(Order.order_time <= end_date)
        return query.order_by(Order.order_time.desc()).offset(skip).limit(limit).all()

    def get_order_by_id(self, db: Session, order_id: int) -> Optional[Order]:
        """根据ID获取订单"""
        return db.query(Order).filter(Order.id == order_id).first()

    def get_order_by_no(self, db: Session, order_no: str) -> Optional[Order]:
        """根据订单号获取订单"""
        return db.query(Order).filter(Order.order_no == order_no).first()

    def update_order(self, db: Session, order_id: int,
                    order_in: OrderUpdate) -> Optional[Order]:
        """更新订单信息"""
        db_order = self.get_order_by_id(db, order_id)
        if not db_order:
            return None
        update_data = order_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_order, field):
                setattr(db_order, field, value)

        # 如果订单状态变为已完成或已支付，记录完成时间
        if order_in.status == OrderStatus.COMPLETED and not db_order.completed_time:
            db_order.completed_time = datetime.now()
        if order_in.status == OrderStatus.PAID and not db_order.paid_time:
            db_order.paid_time = datetime.now()

        db.add(db_order)
        try:
            db.commit()
            db.refresh(db_order)
            return db_order
        except Exception:
            db.rollback()
            raise

    def pay_order(self, db: Session, order_id: int,
                  payment_method: PaymentMethod) -> Optional[Order]:
        """支付订单"""
        db_order = self.get_order_by_id(db, order_id)
        if not db_order:
            raise ValueError("订单不存在")

        if db_order.status != OrderStatus.PENDING:
            raise ValueError("订单状态不允许支付")

        # 如果是会员余额支付，检查会员余额
        if payment_method == PaymentMethod.MEMBER_BALANCE:
            from storage.database.member_manager import MemberManager
            member_mgr = MemberManager()
            member = member_mgr.get_member_by_id(db, db_order.member_id)
            if not member:
                raise ValueError("会员不存在")
            if member.balance < db_order.paid_amount:
                raise ValueError("会员余额不足")

            # 扣除会员余额
            member_mgr.update_balance(db, member.id, -db_order.paid_amount)

        db_order.payment_method = payment_method
        db_order.status = OrderStatus.PAID
        db_order.paid_time = datetime.now()

        db.add(db_order)
        try:
            db.commit()
            db.refresh(db_order)

            # 支付成功后，自动完成订单并扣减库存
            self.complete_order(db, order_id)

            # 记录财务记录
            self._create_financial_record(db, db_order)

            # 如果是会员订单，更新会员消费和积分
            if db_order.member_id:
                from storage.database.member_manager import MemberManager
                member_mgr = MemberManager()
                member_mgr.update_consumption(db, db_order.member_id, db_order.paid_amount)
                # 增加积分（1元=1积分）
                member_mgr.update_points(db, db_order.member_id, int(db_order.paid_amount))

            return db_order
        except Exception:
            db.rollback()
            raise

    def complete_order(self, db: Session, order_id: int) -> Optional[Order]:
        """完成订单并扣减库存"""
        db_order = self.get_order_by_id(db, order_id)
        if not db_order:
            raise ValueError("订单不存在")

        if db_order.status != OrderStatus.PAID:
            raise ValueError("订单状态不允许完成")

        # 扣减库存
        from storage.database.inventory_manager import InventoryManager
        inventory_mgr = InventoryManager()

        for item in db_order.order_items:
            try:
                inventory_mgr.adjust_inventory(
                    db=db,
                    store_id=db_order.store_id,
                    product_id=item.product_id,
                    quantity=-item.quantity,  # 负数表示出库
                    operation_type="sale",
                    remark=f"订单{db_order.order_no}"
                )
            except Exception as e:
                raise ValueError(f"扣减库存失败: {str(e)}")

        db_order.status = OrderStatus.COMPLETED
        db_order.completed_time = datetime.now()
        db.add(db_order)

        try:
            db.commit()
            db.refresh(db_order)
            return db_order
        except Exception:
            db.rollback()
            raise

    def cancel_order(self, db: Session, order_id: int, reason: str = "") -> Optional[Order]:
        """取消订单"""
        db_order = self.get_order_by_id(db, order_id)
        if not db_order:
            raise ValueError("订单不存在")

        if db_order.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            raise ValueError("订单状态不允许取消")

        # 如果已支付，需要退款
        if db_order.status == OrderStatus.PAID:
            # 如果是会员余额支付，退还余额
            if db_order.payment_method == PaymentMethod.MEMBER_BALANCE and db_order.member_id:
                from storage.database.member_manager import MemberManager
                member_mgr = MemberManager()
                member_mgr.update_balance(db, db_order.member_id, db_order.paid_amount)

            # 扣除积分（如果已加）
            if db_order.member_id:
                from storage.database.member_manager import MemberManager
                member_mgr = MemberManager()
                member_mgr.update_points(db, db_order.member_id, -int(db_order.paid_amount))

            # 记录退款财务记录
            self._create_financial_record(db, db_order, is_refund=True)

        db_order.status = OrderStatus.CANCELLED
        db_order.remark = f"{db_order.remark or ''} [取消原因: {reason}]".strip()
        db.add(db_order)

        try:
            db.commit()
            db.refresh(db_order)
            return db_order
        except Exception:
            db.rollback()
            raise

    def _create_financial_record(self, db: Session, order: Order, is_refund: bool = False):
        """创建财务记录"""
        from storage.database.shared.model import FinancialRecord
        record_type = "income" if not is_refund else "refund"
        financial_record = FinancialRecord(
            store_id=order.store_id,
            record_type=record_type,
            amount=order.paid_amount if not is_refund else -order.paid_amount,
            description=f"订单收入" if not is_refund else f"订单退款",
            reference_id=order.order_no,
            category="order"
        )
        db.add(financial_record)

    def get_order_statistics(self, db: Session, store_id: Optional[int] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> dict:
        """获取订单统计"""
        query = db.query(Order)
        if store_id:
            query = query.filter(Order.store_id == store_id)
        if start_date:
            query = query.filter(Order.order_time >= start_date)
        if end_date:
            query = query.filter(Order.order_time <= end_date)

        orders = query.all()

        total_orders = len(orders)
        total_amount = sum(order.total_amount for order in orders)
        paid_amount = sum(order.paid_amount for order in orders)
        completed_orders = sum(1 for order in orders if order.status == OrderStatus.COMPLETED)
        cancelled_orders = sum(1 for order in orders if order.status == OrderStatus.CANCELLED)

        return {
            "total_orders": total_orders,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "average_order_amount": total_amount / total_orders if total_orders > 0 else 0
        }

    def count_orders(self, db: Session, store_id: Optional[int] = None,
                    status: Optional[OrderStatus] = None) -> int:
        """统计订单数量"""
        query = db.query(Order)
        if store_id:
            query = query.filter(Order.store_id == store_id)
        if status:
            query = query.filter(Order.status == status)
        return query.count()
