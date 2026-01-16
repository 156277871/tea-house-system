import streamlit as st
import pandas as pd
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.exc import IntegrityError
import enum

# ============ 数据库配置 ============
DATABASE_URL = "sqlite:///tea_house.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============ 枚举定义 ============
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

# ============ 数据模型 ============
class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    address = Column(String(200))
    phone = Column(String(20))
    status = Column(SQLEnum(StoreStatus), default=StoreStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    position = Column(SQLEnum(EmployeePosition), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    level = Column(SQLEnum(MemberLevel), default=MemberLevel.NORMAL)
    balance = Column(Float, default=0.0)
    total_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)
    unit_price = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"))
    total_amount = Column(Float, default=0.0, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
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
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise

# ============ Streamlit配置 ============
st.set_page_config(
    page_title="连锁茶楼管理系统",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; padding: 15px; border-radius: 10px;}
    .main-header {font-size: 32px; font-weight: bold; color: #1f77b4; margin-bottom: 20px;}
    .success-box {background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 5px solid #28a745;}
    .warning-box {background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 5px solid #ffc107;}
    .danger-box {background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 5px solid #dc3545;}
</style>
""", unsafe_allow_html=True)

# ============ 侧边栏 ============
st.sidebar.title("🏪 连锁茶楼管理系统")
page = st.sidebar.radio(
    "选择功能",
    ["📊 控制台", "🏪 门店管理", "👥 员工管理", "💎 会员管理", "🛍️ 商品管理", "📦 库存管理", "📝 订单管理", "💰 财务报表"]
)

# ============ 控制台 ============
if page == "📊 控制台":
    st.markdown('<div class="main-header">📊 控制台</div>', unsafe_allow_html=True)

    db = get_db()
    try:
        # 今日数据
        today = date.today()
        orders_today = db.query(Order).filter(
            Order.created_at >= today,
            Order.status != OrderStatus.CANCELLED
        ).all()
        
        order_count = len(orders_today)
        total_amount = sum(o.total_amount for o in orders_today)
        net_profit = total_amount * 0.7  # 假设70%利润率
        active_stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).count()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("今日订单数", order_count)
        with col2:
            st.metric("今日营业额", f"¥{total_amount:,.2f}")
        with col3:
            st.metric("净利润", f"¥{net_profit:,.2f}")
        with col4:
            st.metric("活跃门店数", active_stores)
        
        st.markdown("---")
        
        # 门店排名
        st.subheader("🏪 门店营业额排名")
        stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
        store_data = []
        for store in stores:
            store_orders = db.query(Order).filter(
                Order.store_id == store.id,
                Order.created_at >= today,
                Order.status != OrderStatus.CANCELLED
            ).all()
            amount = sum(o.total_amount for o in store_orders)
            store_data.append({"门店名称": store.name, "今日营业额": amount})
        
        if store_data:
            df = pd.DataFrame(store_data).sort_values("今日营业额", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无门店数据")
        
        st.markdown("---")
        
        # 会员统计
        st.subheader("👥 会员统计")
        total_members = db.query(Member).count()
        active_members = db.query(Member).filter(Member.balance > 0).count()
        total_balance = sum(m.balance for m in db.query(Member).all())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("会员总数", total_members)
        with col2:
            st.metric("活跃会员", active_members)
        with col3:
            st.metric("总储值", f"¥{total_balance:,.2f}")
        
        st.markdown("---")
        
        # 最近订单
        st.subheader("📝 最近订单")
        recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
        if recent_orders:
            order_data = []
            for o in recent_orders:
                store = db.query(Store).get(o.store_id)
                order_data.append({
                    "订单号": o.order_no,
                    "门店": store.name if store else "未知",
                    "金额": f"¥{o.total_amount:,.2f}",
                    "状态": o.status.value,
                    "创建时间": o.created_at.strftime("%Y-%m-%d %H:%M")
                })
            df = pd.DataFrame(order_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无订单")
    finally:
        db.close()

# ============ 门店管理 ============
elif page == "🏪 门店管理":
    st.markdown('<div class="main-header">🏪 门店管理</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["门店列表", "新增门店"])
    
    db = get_db()
    try:
        with tab1:
            st.subheader("门店列表")
            stores = db.query(Store).all()
            if stores:
                store_data = []
                for s in stores:
                    store_data.append({
                        "ID": s.id,
                        "名称": s.name,
                        "编码": s.code,
                        "地址": s.address or "-",
                        "电话": s.phone or "-",
                        "状态": "营业中" if s.status == StoreStatus.ACTIVE else "已停业"
                    })
                df = pd.DataFrame(store_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无门店，请先创建")
        
        with tab2:
            st.subheader("新增门店")
            with st.form("create_store"):
                name = st.text_input("门店名称*", max_chars=100)
                code = st.text_input("门店编码*", max_chars=20, help="唯一编码，如：ST001")
                address = st.text_input("门店地址", max_chars=200)
                phone = st.text_input("联系电话", max_chars=20)
                status = st.selectbox("状态", [StoreStatus.ACTIVE, StoreStatus.INACTIVE], 
                                    format_func=lambda x: "营业中" if x == StoreStatus.ACTIVE else "已停业")
                
                submitted = st.form_submit_button("创建门店")
                if submitted:
                    if not name or not code:
                        st.error("门店名称和编码为必填项")
                    else:
                        try:
                            store = Store(name=name, code=code, address=address, phone=phone, status=status)
                            db.add(store)
                            db.commit()
                            st.success("✅ 门店创建成功！")
                            st.rerun()
                        except IntegrityError:
                            db.rollback()
                            st.error("❌ 门店编码已存在，请使用其他编码")
    finally:
        db.close()

# ============ 员工管理 ============
elif page == "👥 员工管理":
    st.markdown('<div class="main-header">👥 员工管理</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["员工列表", "新增员工"])
    
    db = get_db()
    try:
        with tab1:
            st.subheader("员工列表")
            employees = db.query(Employee).all()
            if employees:
                emp_data = []
                for e in employees:
                    store = db.query(Store).get(e.store_id)
                    emp_data.append({
                        "ID": e.id,
                        "姓名": e.name,
                        "电话": e.phone,
                        "职位": e.position.value,
                        "所属门店": store.name if store else "未分配"
                    })
                df = pd.DataFrame(emp_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无员工，请先创建")
        
        with tab2:
            st.subheader("新增员工")
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            if not stores:
                st.warning("请先创建门店")
            else:
                with st.form("create_employee"):
                    name = st.text_input("员工姓名*", max_chars=50)
                    phone = st.text_input("联系电话*", max_chars=20)
                    position = st.selectbox("职位", [
                        EmployeePosition.MANAGER, 
                        EmployeePosition.STAFF, 
                        EmployeePosition.CASHIER
                    ], format_func=lambda x: {"manager": "店长", "staff": "店员", "cashier": "收银员"}[x.value])
                    store_id = st.selectbox("所属门店*", [(s.id, s.name) for s in stores], 
                                           format_func=lambda x: x[1])
                    store_id = store_id[0] if store_id else None
                    
                    submitted = st.form_submit_button("创建员工")
                    if submitted:
                        if not name or not phone or not store_id:
                            st.error("请填写所有必填项")
                        else:
                            try:
                                emp = Employee(name=name, phone=phone, position=position, store_id=store_id)
                                db.add(emp)
                                db.commit()
                                st.success("✅ 员工创建成功！")
                                st.rerun()
                            except IntegrityError:
                                db.rollback()
                                st.error("❌ 电话号码已存在")
    finally:
        db.close()

# ============ 会员管理 ============
elif page == "💎 会员管理":
    st.markdown('<div class="main-header">💎 会员管理</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["会员列表", "新增会员", "会员充值"])
    
    db = get_db()
    try:
        with tab1:
            st.subheader("会员列表")
            members = db.query(Member).all()
            if members:
                member_data = []
                for m in members:
                    member_data.append({
                        "ID": m.id,
                        "姓名": m.name,
                        "电话": m.phone,
                        "等级": m.level.value,
                        "余额": f"¥{m.balance:,.2f}",
                        "积分": m.total_points
                    })
                df = pd.DataFrame(member_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无会员，请先创建")
        
        with tab2:
            st.subheader("新增会员")
            with st.form("create_member"):
                name = st.text_input("会员姓名*", max_chars=50)
                phone = st.text_input("手机号*", max_chars=20)
                level = st.selectbox("会员等级", [
                    MemberLevel.NORMAL, MemberLevel.SILVER, MemberLevel.GOLD, MemberLevel.DIAMOND
                ], format_func=lambda x: {"normal": "普通", "silver": "银卡", "gold": "金卡", "diamond": "钻石"}[x.value])
                
                submitted = st.form_submit_button("创建会员")
                if submitted:
                    if not name or not phone:
                        st.error("请填写所有必填项")
                    else:
                        try:
                            member = Member(name=name, phone=phone, level=level)
                            db.add(member)
                            db.commit()
                            st.success("✅ 会员创建成功！")
                            st.rerun()
                        except IntegrityError:
                            db.rollback()
                            st.error("❌ 手机号已存在")
        
        with tab3:
            st.subheader("会员充值")
            members = db.query(Member).all()
            if not members:
                st.warning("请先创建会员")
            else:
                member_options = [(m.id, f"{m.name} ({m.phone})") for m in members]
                selected_member = st.selectbox("选择会员", member_options, format_func=lambda x: x[1])
                member_id = selected_member[0] if selected_member else None
                recharge_amount = st.number_input("充值金额", min_value=0.0, step=10.0)
                
                if st.button("确认充值"):
                    if member_id and recharge_amount > 0:
                        member = db.query(Member).get(member_id)
                        if member:
                            member.balance += recharge_amount
                            db.commit()
                            st.success(f"✅ 充值成功！{member.name} 余额为 ¥{member.balance:,.2f}")
                            st.rerun()
                    else:
                        st.error("请选择会员并输入充值金额")
    finally:
        db.close()

# ============ 商品管理 ============
elif page == "🛍️ 商品管理":
    st.markdown('<div class="main-header">🛍️ 商品管理</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["商品列表", "新增商品"])
    
    db = get_db()
    try:
        with tab1:
            st.subheader("商品列表")
            products = db.query(Product).all()
            if products:
                product_data = []
                for p in products:
                    product_data.append({
                        "ID": p.id,
                        "名称": p.name,
                        "编码": p.code,
                        "分类": p.category,
                        "单价": f"¥{p.unit_price:,.2f}",
                        "单位": p.unit
                    })
                df = pd.DataFrame(product_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无商品，请先创建")
        
        with tab2:
            st.subheader("新增商品")
            with st.form("create_product"):
                name = st.text_input("商品名称*", max_chars=100)
                code = st.text_input("商品编码*", max_chars=20, help="唯一编码，如：P001")
                category = st.selectbox("商品分类", ["茶叶", "茶具", "点心", "饮品", "其他"])
                unit_price = st.number_input("单价*", min_value=0.0, step=1.0)
                unit = st.text_input("单位*", max_chars=20, help="如：克、个、包")
                description = st.text_area("商品描述", max_chars=500)
                
                submitted = st.form_submit_button("创建商品")
                if submitted:
                    if not name or not code or not unit:
                        st.error("请填写所有必填项")
                    else:
                        try:
                            product = Product(name=name, code=code, category=category, 
                                           unit_price=unit_price, unit=unit, description=description)
                            db.add(product)
                            db.commit()
                            st.success("✅ 商品创建成功！")
                            st.rerun()
                        except IntegrityError:
                            db.rollback()
                            st.error("❌ 商品编码已存在")
    finally:
        db.close()

# ============ 库存管理 ============
elif page == "📦 库存管理":
    st.markdown('<div class="main-header">📦 库存管理</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["库存查询", "库存入库"])
    
    db = get_db()
    try:
        with tab1:
            st.subheader("库存查询")
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            if stores:
                store_options = [(s.id, s.name) for s in stores]
                selected_store = st.selectbox("选择门店", store_options, format_func=lambda x: x[1])
                store_id = selected_store[0] if selected_store else None
                
                if store_id:
                    inventories = db.query(Inventory).filter(Inventory.store_id == store_id).all()
                    if inventories:
                        inv_data = []
                        for inv in inventories:
                            product = db.query(Product).get(inv.product_id)
                            if product:
                                inv_data.append({
                                    "商品名称": product.name,
                                    "商品编码": product.code,
                                    "库存数量": inv.quantity,
                                    "单位": product.unit,
                                    "更新时间": inv.updated_at.strftime("%Y-%m-%d %H:%M")
                                })
                        df = pd.DataFrame(inv_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("该门店暂无库存")
            else:
                st.warning("请先创建门店")
        
        with tab2:
            st.subheader("库存入库")
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            products = db.query(Product).all()
            
            if not stores or not products:
                st.warning("请先创建门店和商品")
            else:
                with st.form("inventory_in"):
                    store_id = st.selectbox("选择门店*", [(s.id, s.name) for s in stores], 
                                           format_func=lambda x: x[1])
                    store_id = store_id[0] if store_id else None
                    product_id = st.selectbox("选择商品*", [(p.id, f"{p.name} ({p.code})") for p in products],
                                            format_func=lambda x: x[1])
                    product_id = product_id[0] if product_id else None
                    quantity = st.number_input("入库数量*", min_value=1, step=1)
                    
                    submitted = st.form_submit_button("确认入库")
                    if submitted:
                        if not store_id or not product_id:
                            st.error("请选择门店和商品")
                        else:
                            # 检查库存是否已存在
                            inventory = db.query(Inventory).filter(
                                Inventory.store_id == store_id,
                                Inventory.product_id == product_id
                            ).first()
                            
                            if inventory:
                                inventory.quantity += quantity
                            else:
                                inventory = Inventory(store_id=store_id, product_id=product_id, quantity=quantity)
                                db.add(inventory)
                            
                            db.commit()
                            st.success("✅ 入库成功！")
                            st.rerun()
    finally:
        db.close()

# ============ 订单管理 ============
elif page == "📝 订单管理":
    st.markdown('<div class="main-header">📝 订单管理</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["订单列表", "创建订单"])
    
    db = get_db()
    try:
        with tab1:
            st.subheader("订单列表")
            orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
            if orders:
                order_data = []
                for o in orders:
                    store = db.query(Store).get(o.store_id)
                    member = db.query(Member).get(o.member_id)
                    order_data.append({
                        "订单号": o.order_no,
                        "门店": store.name if store else "未知",
                        "会员": member.name if member else "散客",
                        "金额": f"¥{o.total_amount:,.2f}",
                        "支付方式": o.payment_method.value,
                        "状态": o.status.value,
                        "创建时间": o.created_at.strftime("%Y-%m-%d %H:%M")
                    })
                df = pd.DataFrame(order_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无订单")
        
        with tab2:
            st.subheader("创建订单")
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            members = db.query(Member).all()
            products = db.query(Product).all()
            
            if not stores or not products:
                st.warning("请先创建门店和商品")
            else:
                with st.form("create_order"):
                    store_id = st.selectbox("选择门店*", [(s.id, s.name) for s in stores], 
                                           format_func=lambda x: x[1])
                    store_id = store_id[0] if store_id else None
                    
                    member_options = [(None, "散客")] + [(m.id, f"{m.name} ({m.phone})") for m in members]
                    member_id = st.selectbox("选择会员（可选）", member_options, format_func=lambda x: x[1])
                    member_id = member_id[0] if member_id else None
                    
                    payment_method = st.selectbox("支付方式", [
                        PaymentMethod.WECHAT, PaymentMethod.ALIPAY, PaymentMethod.CASH, PaymentMethod.CARD
                    ], format_func=lambda x: {"wechat": "微信", "alipay": "支付宝", "cash": "现金", "card": "刷卡"}[x.value])
                    
                    st.subheader("选择商品")
                    product_items = []
                    product_options = [(p.id, f"{p.name} (¥{p.unit_price:.2f}/{p.unit})") for p in products]
                    
                    # 动态添加商品
                    if "order_products" not in st.session_state:
                        st.session_state.order_products = [{}]
                    
                    for i in range(len(st.session_state.order_products)):
                        cols = st.columns([3, 2, 2])
                        with cols[0]:
                            pid = st.selectbox("商品", product_options, key=f"prod_{i}",
                                             format_func=lambda x: x[1], index=None)
                        with cols[1]:
                            qty = st.number_input("数量", min_value=1, step=1, key=f"qty_{i}")
                        with cols[2]:
                            if st.button("删除", key=f"del_{i}"):
                                st.session_state.order_products.pop(i)
                                st.rerun()
                        
                        if pid and qty > 0:
                            product = db.query(Product).get(pid[0] if isinstance(pid, tuple) else pid)
                            if product:
                                st.session_state.order_products[i] = {
                                    "product_id": product.id,
                                    "quantity": qty,
                                    "unit_price": product.unit_price,
                                    "subtotal": product.unit_price * qty
                                }
                    
                    if st.button("添加商品"):
                        st.session_state.order_products.append({})
                        st.rerun()
                    
                    # 显示已选商品
                    valid_products = [p for p in st.session_state.order_products if p]
                    if valid_products:
                        st.subheader("订单明细")
                        total = 0
                        for p in valid_products:
                            product = db.query(Product).get(p["product_id"])
                            st.write(f"{product.name} x {p['quantity']} = ¥{p['subtotal']:.2f}")
                            total += p["subtotal"]
                        st.metric("订单总额", f"¥{total:.2f}")
                    
                    submitted = st.form_submit_button("创建订单")
                    if submitted:
                        if not store_id or not valid_products:
                            st.error("请选择门店和至少一个商品")
                        else:
                            try:
                                # 生成订单号
                                order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                order = Order(order_no=order_no, store_id=store_id, member_id=member_id,
                                            total_amount=total, payment_method=payment_method,
                                            status=OrderStatus.PAID)
                                db.add(order)
                                db.flush()  # 获取order ID
                                
                                # 添加订单项
                                for p in valid_products:
                                    item = OrderItem(order_id=order.id, product_id=p["product_id"],
                                                   quantity=p["quantity"], unit_price=p["unit_price"],
                                                   subtotal=p["subtotal"])
                                    db.add(item)
                                
                                db.commit()
                                st.success(f"✅ 订单创建成功！订单号：{order_no}")
                                st.session_state.order_products = [{}]
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"❌ 创建订单失败：{str(e)}")
    finally:
        db.close()

# ============ 财务报表 ============
elif page == "💰 财务报表":
    st.markdown('<div class="main-header">💰 财务报表</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["日报表", "月报表", "门店对比"])
    
    db = get_db()
    try:
        with tab1:
            st.subheader("日报表")
            selected_date = st.date_input("选择日期", date.today())
            
            orders = db.query(Order).filter(
                Order.created_at >= selected_date,
                Order.created_at < selected_date.replace(day=selected_date.day+1) if selected_date.day < 28 else selected_date,
                Order.status != OrderStatus.CANCELLED
            ).all()
            
            if orders:
                total_amount = sum(o.total_amount for o in orders)
                total_orders = len(orders)
                avg_amount = total_amount / total_orders if total_orders > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("订单数", total_orders)
                with col2:
                    st.metric("营业额", f"¥{total_amount:,.2f}")
                with col3:
                    st.metric("客单价", f"¥{avg_amount:.2f}")
                
                st.subheader("订单明细")
                order_data = []
                for o in orders:
                    store = db.query(Store).get(o.store_id)
                    order_data.append({
                        "订单号": o.order_no,
                        "门店": store.name if store else "未知",
                        "金额": f"¥{o.total_amount:,.2f}",
                        "支付方式": o.payment_method.value,
                        "创建时间": o.created_at.strftime("%H:%M")
                    })
                df = pd.DataFrame(order_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("该日期无订单记录")
        
        with tab2:
            st.subheader("月报表")
            year = st.selectbox("选择年份", range(2023, date.today().year + 2))
            month = st.selectbox("选择月份", range(1, 13))
            
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            orders = db.query(Order).filter(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status != OrderStatus.CANCELLED
            ).all()
            
            if orders:
                total_amount = sum(o.total_amount for o in orders)
                total_orders = len(orders)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("月订单数", total_orders)
                with col2:
                    st.metric("月营业额", f"¥{total_amount:,.2f}")
                
                # 按门店统计
                st.subheader("各门店业绩")
                stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
                store_data = []
                for store in stores:
                    store_orders = db.query(Order).filter(
                        Order.store_id == store.id,
                        Order.created_at >= start_date,
                        Order.created_at < end_date,
                        Order.status != OrderStatus.CANCELLED
                    ).all()
                    if store_orders:
                        amount = sum(o.total_amount for o in store_orders)
                        store_data.append({
                            "门店名称": store.name,
                            "订单数": len(store_orders),
                            "营业额": f"¥{amount:,.2f}"
                        })
                if store_data:
                    df = pd.DataFrame(store_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("该月份无订单记录")
        
        with tab3:
            st.subheader("门店对比")
            start_date = st.date_input("开始日期", date.today().replace(day=1))
            end_date = st.date_input("结束日期", date.today())
            
            stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
            comparison_data = []
            
            for store in stores:
                orders = db.query(Order).filter(
                    Order.store_id == store.id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date,
                    Order.status != OrderStatus.CANCELLED
                ).all()
                
                total_amount = sum(o.total_amount for o in orders)
                comparison_data.append({
                    "门店名称": store.name,
                    "订单数": len(orders),
                    "营业额": total_amount,
                    "占比": f"{total_amount / sum([o.total_amount for o in db.query(Order).filter(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Order.status != OrderStatus.CANCELLED
                    ).all()]) * 100:.1f}%" if orders else "0%"
                })
            
            if comparison_data:
                df = pd.DataFrame(comparison_data).sort_values("营业额", ascending=False)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # 简单的柱状图
                import plotly.express as px
                fig = px.bar(df, x="门店名称", y="营业额", title="门店营业额对比")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("该时间段无数据")
    finally:
        db.close()
