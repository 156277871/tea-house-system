from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, JSON, func, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
import datetime
import enum

from coze_coding_dev_sdk.database import Base


class StoreStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    WECHAT = "wechat"
    ALIPAY = "alipay"
    CARD = "card"
    MEMBER_BALANCE = "member_balance"


class InventoryChangeType(str, enum.Enum):
    IN = "in"
    OUT = "out"
    ADJUST = "adjust"


class MemberLevel(str, enum.Enum):
    NORMAL = "normal"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class EmployeePosition(str, enum.Enum):
    MANAGER = "manager"
    CASHIER = "cashier"
    WAITER = "waiter"
    CHEF = "chef"


class Store(Base):
    """门店表"""
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, comment="门店ID")
    name = Column(String(100), nullable=False, comment="门店名称")
    code = Column(String(20), unique=True, nullable=False, comment="门店编码")
    address = Column(String(255), nullable=False, comment="门店地址")
    phone = Column(String(20), nullable=False, comment="联系电话")
    manager_name = Column(String(50), comment="店长姓名")
    manager_phone = Column(String(20), comment="店长电话")
    status = Column(SQLEnum(StoreStatus), default=StoreStatus.ACTIVE, nullable=False, comment="门店状态")
    open_time = Column(String(10), comment="营业开始时间")
    close_time = Column(String(10), comment="营业结束时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True, comment="更新时间")

    # 关系
    employees = relationship("Employee", back_populates="store")
    inventory = relationship("Inventory", back_populates="store")
    orders = relationship("Order", back_populates="store")
    financial_records = relationship("FinancialRecord", back_populates="store")

    __table_args__ = (
        Index("ix_stores_code", "code"),
        Index("ix_stores_status", "status"),
    )


class Employee(Base):
    """员工表"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, comment="员工ID")
    name = Column(String(50), nullable=False, comment="员工姓名")
    phone = Column(String(20), nullable=False, comment="联系电话")
    email = Column(String(100), comment="邮箱")
    position = Column(SQLEnum(EmployeePosition), nullable=False, comment="职位")
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, comment="所属门店")
    status = Column(Boolean, default=True, nullable=False, comment="状态")
    hire_date = Column(DateTime(timezone=True), comment="入职日期")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True, comment="更新时间")

    # 关系
    store = relationship("Store", back_populates="employees")

    __table_args__ = (
        Index("ix_employees_store", "store_id"),
        Index("ix_employees_phone", "phone"),
    )


class Member(Base):
    """会员表"""
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, comment="会员ID")
    member_no = Column(String(20), unique=True, nullable=False, comment="会员编号")
    name = Column(String(50), nullable=False, comment="会员姓名")
    phone = Column(String(20), unique=True, nullable=False, comment="手机号")
    email = Column(String(100), comment="邮箱")
    level = Column(SQLEnum(MemberLevel), default=MemberLevel.NORMAL, nullable=False, comment="会员等级")
    points = Column(Integer, default=0, nullable=False, comment="积分")
    balance = Column(Float, default=0.0, nullable=False, comment="储值余额")
    total_consumption = Column(Float, default=0.0, nullable=False, comment="累计消费")
    status = Column(Boolean, default=True, nullable=False, comment="状态")
    last_visit_time = Column(DateTime(timezone=True), comment="最后到店时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True, comment="更新时间")

    # 关系
    orders = relationship("Order", back_populates="member")
    transactions = relationship("MemberTransaction", back_populates="member")

    __table_args__ = (
        Index("ix_members_member_no", "member_no"),
        Index("ix_members_phone", "phone"),
        Index("ix_members_level", "level"),
    )


class Product(Base):
    """商品表"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, comment="商品ID")
    name = Column(String(100), nullable=False, comment="商品名称")
    code = Column(String(30), unique=True, nullable=False, comment="商品编码")
    category = Column(String(50), nullable=False, comment="商品分类")
    price = Column(Float, nullable=False, comment="单价")
    cost_price = Column(Float, comment="成本价")
    unit = Column(String(20), nullable=False, comment="单位")
    description = Column(Text, comment="商品描述")
    image_url = Column(String(255), comment="商品图片URL")
    status = Column(Boolean, default=True, nullable=False, comment="状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True, comment="更新时间")

    # 关系
    inventory = relationship("Inventory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    inventory_logs = relationship("InventoryLog", back_populates="product")

    __table_args__ = (
        Index("ix_products_code", "code"),
        Index("ix_products_category", "category"),
    )


class Inventory(Base):
    """库存表"""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, comment="库存ID")
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, comment="门店ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")
    quantity = Column(Float, default=0.0, nullable=False, comment="库存数量")
    warning_threshold = Column(Float, default=10.0, nullable=False, comment="预警阈值")
    last_updated = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True, comment="最后更新时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    # 关系
    store = relationship("Store", back_populates="inventory")
    product = relationship("Product", back_populates="inventory")

    __table_args__ = (
        Index("ix_inventory_store_product", "store_id", "product_id", unique=True),
        Index("ix_inventory_warning", "quantity"),
    )


class InventoryLog(Base):
    """库存变动日志表"""
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, comment="日志ID")
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, comment="门店ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")
    change_type = Column(SQLEnum(InventoryChangeType), nullable=False, comment="变动类型")
    quantity = Column(Float, nullable=False, comment="变动数量")
    before_quantity = Column(Float, nullable=False, comment="变动前数量")
    after_quantity = Column(Float, nullable=False, comment="变动后数量")
    operation_type = Column(String(50), nullable=False, comment="操作类型: purchase/sale/adjust/loss")
    remark = Column(String(255), comment="备注")
    operator_id = Column(Integer, comment="操作人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    # 关系
    product = relationship("Product", back_populates="inventory_logs")

    __table_args__ = (
        Index("ix_inventory_logs_store", "store_id"),
        Index("ix_inventory_logs_product", "product_id"),
        Index("ix_inventory_logs_created", "created_at"),
    )


class Order(Base):
    """订单表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, comment="订单ID")
    order_no = Column(String(30), unique=True, nullable=False, comment="订单编号")
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, comment="门店ID")
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True, comment="会员ID")
    total_amount = Column(Float, nullable=False, comment="订单总额")
    discount_amount = Column(Float, default=0.0, nullable=False, comment="优惠金额")
    paid_amount = Column(Float, nullable=False, comment="实付金额")
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False, comment="支付方式")
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, comment="订单状态")
    order_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="下单时间")
    paid_time = Column(DateTime(timezone=True), comment="支付时间")
    completed_time = Column(DateTime(timezone=True), comment="完成时间")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True, comment="更新时间")

    # 关系
    store = relationship("Store", back_populates="orders")
    member = relationship("Member", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_orders_order_no", "order_no"),
        Index("ix_orders_store", "store_id"),
        Index("ix_orders_member", "member_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_order_time", "order_time"),
    )


class OrderItem(Base):
    """订单明细表"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, comment="明细ID")
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, comment="订单ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")
    product_name = Column(String(100), nullable=False, comment="商品名称")
    quantity = Column(Float, nullable=False, comment="数量")
    unit_price = Column(Float, nullable=False, comment="单价")
    subtotal = Column(Float, nullable=False, comment="小计")
    remark = Column(String(255), comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    # 关系
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        Index("ix_order_items_order", "order_id"),
        Index("ix_order_items_product", "product_id"),
    )


class FinancialRecord(Base):
    """财务记录表"""
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, comment="记录ID")
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, comment="门店ID")
    record_type = Column(String(50), nullable=False, comment="记录类型: income/expense/refund")
    amount = Column(Float, nullable=False, comment="金额")
    description = Column(String(255), nullable=False, comment="描述")
    reference_id = Column(String(50), comment="关联单号(订单号等)")
    category = Column(String(50), comment="分类")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    # 关系
    store = relationship("Store", back_populates="financial_records")

    __table_args__ = (
        Index("ix_financial_records_store", "store_id"),
        Index("ix_financial_records_type", "record_type"),
        Index("ix_financial_records_created", "created_at"),
    )


class MemberTransaction(Base):
    """会员交易记录表"""
    __tablename__ = "member_transactions"

    id = Column(Integer, primary_key=True, comment="交易ID")
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, comment="会员ID")
    transaction_type = Column(String(50), nullable=False, comment="交易类型: recharge/consume/refund/points_add/points_deduct")
    amount = Column(Float, default=0.0, nullable=False, comment="金额变动")
    points_change = Column(Integer, default=0, nullable=False, comment="积分变动")
    balance_after = Column(Float, nullable=False, comment="交易后余额")
    points_after = Column(Integer, nullable=False, comment="交易后积分")
    remark = Column(String(255), comment="备注")
    reference_id = Column(String(50), comment="关联单号")
    store_id = Column(Integer, comment="操作门店ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    # 关系
    member = relationship("Member", back_populates="transactions")

    __table_args__ = (
        Index("ix_member_transactions_member", "member_id"),
        Index("ix_member_transactions_type", "transaction_type"),
        Index("ix_member_transactions_created", "created_at"),
    )
