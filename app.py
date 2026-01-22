import streamlit as st
import pandas as pd
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.exc import IntegrityError
import enum

# 数据库配置
DATABASE_URL = "sqlite:///tea_house.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 枚举定义
class StoreStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class EmployeePosition(str, enum.Enum):
    MANAGER = "manager"
    STAFF = "staff"
    CASHIER = "cashier"

class MemberLevel(str, enum.Enum):
    NORMAL = "normal"
    SILVER = "silver"
    GOLD = "gold"
    DIAMOND = "diamond"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    WECHAT = "wechat"
    ALIPAY = "alipay"
    CASH = "cash"
    CARD = "card"

# 数据模型
class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    address = Column(String(200))
    phone = Column(String(20))
    status = Column(SQLEnum(StoreStatus), default=StoreStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    position = Column(SQLEnum(EmployeePosition), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"))

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    level = Column(SQLEnum(MemberLevel), default=MemberLevel.NORMAL)
    balance = Column(Float, default=0.0)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)
    unit_price = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"))
    total_amount = Column(Float, default=0.0, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PAID)
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

# 创建数据库表
Base.metadata.create_all(bind=engine)

def get_db():
    return SessionLocal()

# Streamlit配置
st.set_page_config(page_title="连锁茶楼管理系统", page_icon="🏪", layout="wide")

st.sidebar.title("🏪 连锁茶楼管理系统")
page = st.sidebar.radio("选择功能", ["📊 控制台", "🏪 门店管理", "👥 员工管理", "💎 会员管理", "🛍️ 商品管理", "📦 库存管理", "📝 订单管理", "💰 财务报表"])

# 控制台
if page == "📊 控制台":
    st.header("📊 控制台")
    db = get_db()
    try:
        today = date.today()
        orders_today = db.query(Order).filter(Order.created_at >= today).all()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("今日订单", len(orders_today))
        with col2: st.metric("今日营业额", f"¥{sum(o.total_amount for o in orders_today):,.2f}")
        with col3: st.metric("净利润", f"¥{sum(o.total_amount for o in orders_today) * 0.7:,.2f}")
        with col4: st.metric("活跃门店", db.query(Store).filter(Store.status == StoreStatus.ACTIVE).count())
        
        st.subheader("最近订单")
        recent = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
        if recent:
            df = pd.DataFrame([{"订单号": o.order_no, "金额": f"¥{o.total_amount:.2f}", "时间": o.created_at.strftime("%H:%M")} for o in recent])
            st.dataframe(df)
    finally: db.close()

# 门店管理
elif page == "🏪 门店管理":
    st.header("🏪 门店管理")
    tab1, tab2 = st.tabs(["门店列表", "新增门店"])
    db = get_db()
    try:
        with tab1:
            stores = db.query(Store).all()
            if stores:
                st.dataframe(pd.DataFrame([{"名称": s.name, "编码": s.code, "地址": s.address or "-", "电话": s.phone or "-"} for s in stores]))
            else: st.info("暂无门店")
        with tab2:
            with st.form("create_store"):
                name = st.text_input("门店名称*")
                code = st.text_input("门店编码*")
                address = st.text_input("地址")
                phone = st.text_input("电话")
                if st.form_submit_button("创建"):
                    try:
                        db.add(Store(name=name, code=code, address=address, phone=phone))
                        db.commit()
                        st.success("✅ 创建成功")
                    except IntegrityError:
                        db.rollback()
                        st.error("编码已存在")
    finally: db.close()

# 商品管理
elif page == "🛍️ 商品管理":
    st.header("🛍️ 商品管理")
    tab1, tab2 = st.tabs(["商品列表", "新增商品"])
    db = get_db()
    try:
        with tab1:
            products = db.query(Product).all()
            if products:
                st.dataframe(pd.DataFrame([{"名称": p.name, "编码": p.code, "分类": p.category, "单价": p.unit_price} for p in products]))
            else: st.info("暂无商品")
        with tab2:
            with st.form("create_product"):
                name = st.text_input("商品名称*")
                code = st.text_input("商品编码*")
                category = st.selectbox("分类", ["茶叶", "茶具", "点心", "饮品"])
                price = st.number_input("单价*", min_value=0.0, step=1.0)
                unit = st.text_input("单位*")
                if st.form_submit_button("创建"):
                    try:
                        db.add(Product(name=name, code=code, category=category, unit_price=price, unit=unit))
                        db.commit()
                        st.success("✅ 创建成功")
                    except IntegrityError:
                        db.rollback()
                        st.error("编码已存在")
    finally: db.close()

# 员工管理
elif page == "👥 员工管理":
    st.header("👥 员工管理")
    tab1, tab2 = st.tabs(["员工列表", "新增员工"])
    db = get_db()
    try:
        with tab1:
            emps = db.query(Employee).all()
            if emps:
                st.dataframe(pd.DataFrame([{"姓名": e.name, "电话": e.phone, "职位": e.position.value} for e in emps]))
            else: st.info("暂无员工")
        with tab2:
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            if not stores:
                st.warning("请先创建门店")
            else:
                with st.form("create_emp"):
                    name = st.text_input("姓名*")
                    phone = st.text_input("电话*")
                    pos = st.selectbox("职位", [EmployeePosition.MANAGER, EmployeePosition.STAFF, EmployeePosition.CASHIER], format_func=lambda x: {"manager": "店长", "staff": "店员", "cashier": "收银员"}[x.value])
                    store_id = st.selectbox("所属门店*", [(s.id, s.name) for s in stores], format_func=lambda x: x[1])
                    if st.form_submit_button("创建"):
                        try:
                            db.add(Employee(name=name, phone=phone, position=pos, store_id=store_id[0]))
                            db.commit()
                            st.success("✅ 创建成功")
                        except IntegrityError:
                            db.rollback()
                            st.error("电话已存在")
    finally: db.close()

# 会员管理
elif page == "💎 会员管理":
    st.header("💎 会员管理")
    tab1, tab2 = st.tabs(["会员列表", "新增会员"])
    db = get_db()
    try:
        with tab1:
            members = db.query(Member).all()
            if members:
                st.dataframe(pd.DataFrame([{"姓名": m.name, "电话": m.phone, "等级": m.level.value, "余额": m.balance} for m in members]))
            else: st.info("暂无会员")
        with tab2:
            with st.form("create_member"):
                name = st.text_input("姓名*")
                phone = st.text_input("电话*")
                if st.form_submit_button("创建"):
                    try:
                        db.add(Member(name=name, phone=phone))
                        db.commit()
                        st.success("✅ 创建成功")
                    except IntegrityError:
                        db.rollback()
                        st.error("电话已存在")
    finally: db.close()

# 库存管理
elif page == "📦 库存管理":
    st.header("📦 库存管理")
    tab1, tab2 = st.tabs(["库存查询", "库存入库"])
    db = get_db()
    try:
        with tab1:
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            if stores:
                store_id = st.selectbox("选择门店", [(s.id, s.name) for s in stores], format_func=lambda x: x[1])
                invs = db.query(Inventory).filter(Inventory.store_id == store_id[0]).all()
                if invs:
                    data = []
                    for inv in invs:
                        p = db.query(Product).get(inv.product_id)
                        data.append({"商品": p.name, "数量": inv.quantity})
                    st.dataframe(pd.DataFrame(data))
                else: st.info("暂无库存")
        with tab2:
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            products = db.query(Product).all()
            if stores and products:
                with st.form("add_stock"):
                    sid = st.selectbox("门店", [(s.id, s.name) for s in stores], format_func=lambda x: x[1])
                    pid = st.selectbox("商品", [(p.id, p.name) for p in products], format_func=lambda x: x[1])
                    qty = st.number_input("数量*", min_value=1)
                    if st.form_submit_button("入库"):
                        inv = db.query(Inventory).filter(Inventory.store_id == sid[0], Inventory.product_id == pid[0]).first()
                        if inv:
                            inv.quantity += qty
                        else:
                            db.add(Inventory(store_id=sid[0], product_id=pid[0], quantity=qty))
                        db.commit()
                        st.success("✅ 入库成功")
    finally: db.close()

# 订单管理
elif page == "📝 订单管理":
    st.header("📝 订单管理")
    tab1, tab2 = st.tabs(["订单列表", "创建订单"])
    db = get_db()
    try:
        with tab1:
            orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
            if orders:
                st.dataframe(pd.DataFrame([{"订单号": o.order_no, "金额": f"¥{o.total_amount:.2f}", "状态": o.status.value} for o in orders]))
            else: st.info("暂无订单")
        with tab2:
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            products = db.query(Product).all()
            if stores and products:
                with st.form("create_order"):
                    sid = st.selectbox("门店*", [(s.id, s.name) for s in stores], format_func=lambda x: x[1])
                    pay = st.selectbox("支付方式", [PaymentMethod.WECHAT, PaymentMethod.ALIPAY, PaymentMethod.CASH], format_func=lambda x: {"wechat": "微信", "alipay": "支付宝", "cash": "现金"}[x.value])
                    pid = st.selectbox("商品*", [(p.id, p.name) for p in products], format_func=lambda x: x[1])
                    qty = st.number_input("数量*", min_value=1)
                    if st.form_submit_button("创建"):
                        p = db.query(Product).get(pid[0])
                        total = p.unit_price * qty
                        order = Order(order_no=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}", store_id=sid[0], total_amount=total, payment_method=pay)
                        db.add(order)
                        db.flush()
                        db.add(OrderItem(order_id=order.id, product_id=pid[0], quantity=qty, unit_price=p.unit_price, subtotal=total))
                        db.commit()
                        st.success("✅ 订单创建成功")
    finally: db.close()

# 财务报表
elif page == "💰 财务报表":
    st.header("💰 财务报表")
    st.info("报表功能开发中...")
