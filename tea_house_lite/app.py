import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.exc import IntegrityError
import enum
import os
import sys
import traceback

# 配置 Streamlit 页面
st.set_page_config(
    page_title="连锁茶楼管理系统",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 全局异常捕获
def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = f"应用发生错误:\n{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}"
    st.error(f"❌ {error_msg}")

sys.excepthook = handle_exception

# 数据库配置 - 使用工作目录以确保云环境兼容性
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "tea_house.db")

# 确保目录存在且可写
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
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

class TableStatus(str, enum.Enum):
    FREE = "free"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"

class SessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

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

class Table(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    name = Column(String(20), nullable=False)
    capacity = Column(Integer, default=4)
    status = Column(SQLEnum(TableStatus), default=TableStatus.FREE)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.IN_PROGRESS)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    total_amount = Column(Float, default=0.0)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
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

def init_database():
    """初始化和升级数据库"""
    try:
        # 创建所有表（如果不存在）
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"❌ 数据库初始化失败: {str(e)}")
        return False

# 初始化数据库
if not init_database():
    st.error("❌ 无法初始化数据库，应用将无法正常工作")
    st.stop()

# 自定义CSS：亮色主题 + 导航栏样式
st.markdown("""
<style>
/* 亮色主题 - 主背景 */
.stApp {
    background-color: #ffffff !important;
}

.main .block-container {
    background-color: #ffffff !important;
    color: #1f1f1f !important;
}

/* 亮色主题 - 侧边栏 */
[data-testid="stSidebar"] {
    background-color: #f8f9fa !important;
    color: #1f1f1f !important;
}

/* 侧边栏所有文字颜色 */
[data-testid="stSidebar"] * {
    color: #1f1f1f !important;
}

/* 亮色主题 - 标题 */
h1, h2, h3, h4, h5, h6 {
    color: #1f1f1f !important;
}

/* 导航栏 - 去掉默认选中样式 */
[data-testid="stSidebarNav"] li div {
    color: #1f1f1f !important;
    background-color: transparent !important;
}

/* 导航栏 - 选中项 */
[data-testid="stSidebarNav"] li:has([aria-selected="true"]) div {
    background-color: #e9ecef !important;
    color: #1f1f1f !important;
    font-weight: bold;
}

/* 导航栏 - 悬停效果 */
[data-testid="stSidebarNav"] li div:hover {
    background-color: #dee2e6 !important;
}

/* 主按钮样式 */
.stButton > button[kind="primary"] {
    background-color: #ff6b6b !important;
    color: #ffffff !important;
    border: none;
    font-weight: bold;
}

.stButton > button:not([kind="primary"]) {
    background-color: #6c757d !important;
    color: #ffffff !important;
    border: none;
}

/* 表单提交按钮 */
div[data-testid="stForm"] button[type="submit"] {
    background-color: #ff6b6b !important;
    color: #ffffff !important;
    border: none;
    font-weight: bold;
}

/* 数据表样式 */
[data-testid="stDataFrame"] {
    background-color: #ffffff !important;
}

/* Metric 卡片 */
[data-testid="stMetricValue"] {
    color: #1f1f1f !important;
}
</style>
""", unsafe_allow_html=True)

# 数据库操作辅助函数
def get_db():
    """获取数据库会话"""
    return SessionLocal()

def format_duration(minutes):
    """格式化时长显示"""
    if minutes < 60:
        return f"{minutes}分钟"
    else:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}小时{mins}分钟"

# 主应用
def main():
    try:
        # 侧边栏导航
        with st.sidebar:
            st.title("🏪 茶楼管理系统")
            st.markdown("---")
            page = st.radio(
                "选择功能",
                ["📊 控制台", "⚙️ 设置", "🪑 开台管理", "🛒 点单管理", "💳 结账管理", "👥 会员管理", "📝 订单管理", "💰 财务报表"],
                label_visibility="collapsed"
            )
            st.markdown("---")
            st.caption(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # 控制台
        if page == "📊 控制台":
            st.header("📊 控制台")
            db = get_db()
            try:
                # 基础数据统计
                store_count = db.query(Store).count()
                employee_count = db.query(Employee).count()
                member_count = db.query(Member).count()
                product_count = db.query(Product).count()
                table_count = db.query(Table).count()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("门店数", store_count)
                with col2:
                    st.metric("员工数", employee_count)
                with col3:
                    st.metric("会员数", member_count)

                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric("商品数", product_count)
                with col5:
                    st.metric("台位数", table_count)

                # 今日营业统计
                today = date.today()
                today_orders = db.query(Order).filter(
                    Order.created_at >= datetime.combine(today, datetime.min.time()),
                    Order.created_at <= datetime.combine(today, datetime.max.time())
                ).all()

                today_revenue = sum(o.total_amount for o in today_orders if o.status == OrderStatus.PAID)
                today_order_count = len(today_orders)

                st.markdown("---")
                st.subheader("📈 今日营业")
                col7, col8 = st.columns(2)
                with col7:
                    st.metric("今日订单", today_order_count)
                with col8:
                    st.metric("今日营业额", f"¥{today_revenue:,.2f}")

                # 快速操作
                st.markdown("---")
                st.subheader("🚀 快速操作")
                col9, col10, col11 = st.columns(3)
                with col9:
                    if st.button("开台", use_container_width=True, type="primary"):
                        st.switch_page("⚙️ 设置")
                with col10:
                    if st.button("点单", use_container_width=True):
                        st.switch_page("🛒 点单管理")
                with col11:
                    if st.button("结账", use_container_width=True):
                        st.switch_page("💳 结账管理")
            finally:
                db.close()

        # 设置页面
        elif page == "⚙️ 设置":
            st.header("⚙️ 系统设置")
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏪 门店管理", "🪑 桌台管理", "👤 员工管理", "🛍️ 商品管理", "📦 库存管理"])

            with tab1:
                st.subheader("门店列表")
                db = get_db()
                try:
                    stores = db.query(Store).all()
                    if stores:
                        st.dataframe(pd.DataFrame([{
                            "ID": s.id,
                            "名称": s.name,
                            "编码": s.code,
                            "地址": s.address,
                            "电话": s.phone,
                            "状态": s.status.value
                        } for s in stores]), use_container_width=True)
                    else:
                        st.info("暂无门店，请先创建门店")

                    st.subheader("创建门店")
                    with st.form("create_store"):
                        name = st.text_input("门店名称*", max_chars=100)
                        code = st.text_input("门店编码*", max_chars=20)
                        address = st.text_input("地址", max_chars=200)
                        phone = st.text_input("电话", max_chars=20)
                        if st.form_submit_button("创建门店", type="primary"):
                            try:
                                db.add(Store(name=name, code=code, address=address, phone=phone))
                                db.commit()
                                st.success("✅ 创建成功")
                                st.rerun()
                            except IntegrityError:
                                db.rollback()
                                st.error("❌ 门店编码已存在")
                finally:
                    db.close()

            with tab2:
                st.subheader("桌台列表")
                db = get_db()
                try:
                    tables = db.query(Table).all()
                    if tables:
                        st.dataframe(pd.DataFrame([{
                            "ID": t.id,
                            "台位名称": t.name,
                            "门店ID": t.store_id,
                            "容量": t.capacity,
                            "状态": t.status.value
                        } for t in tables]), use_container_width=True)
                    else:
                        st.info("暂无桌台")

                    st.subheader("添加桌台")
                    with st.form("create_table"):
                        stores = db.query(Store).all()
                        if stores:
                            store_options = {f"{s.name} (ID:{s.id})": s.id for s in stores}
                            store_id = st.selectbox("选择门店*", options=list(store_options.keys()), format_func=lambda x: x.split('(')[0].strip())
                            name = st.text_input("台位名称*", max_chars=20)
                            capacity = st.number_input("容量", min_value=1, max_value=20, value=4)
                            if st.form_submit_button("添加桌台", type="primary"):
                                try:
                                    actual_store_id = store_options[store_id]
                                    db.add(Table(store_id=actual_store_id, name=name, capacity=capacity))
                                    db.commit()
                                    st.success("✅ 添加成功")
                                    st.rerun()
                                except Exception as e:
                                    db.rollback()
                                    st.error(f"❌ 添加失败: {str(e)}")
                        else:
                            st.warning("请先创建门店")
                finally:
                    db.close()

            with tab3:
                st.subheader("员工列表")
                db = get_db()
                try:
                    employees = db.query(Employee).all()
                    if employees:
                        st.dataframe(pd.DataFrame([{
                            "ID": e.id,
                            "姓名": e.name,
                            "电话": e.phone,
                            "职位": e.position.value,
                            "门店ID": e.store_id
                        } for e in employees]), use_container_width=True)
                    else:
                        st.info("暂无员工")

                    st.subheader("创建员工")
                    with st.form("create_employee"):
                        stores = db.query(Store).all()
                        name = st.text_input("姓名*", max_chars=50)
                        phone = st.text_input("电话*", max_chars=20)
                        position = st.selectbox("职位*", options=["manager", "staff", "cashier"])
                        if stores:
                            store_options = {f"{s.name} (ID:{s.id})": s.id for s in stores}
                            store_id = st.selectbox("分配门店", options=list(store_options.keys()), format_func=lambda x: x.split('(')[0].strip())
                        else:
                            store_id = None
                            st.warning("请先创建门店")
                        if st.form_submit_button("创建员工", type="primary"):
                            try:
                                actual_store_id = store_options[store_id] if store_id else None
                                db.add(Employee(name=name, phone=phone, position=EmployeePosition(position), store_id=actual_store_id))
                                db.commit()
                                st.success("✅ 创建成功")
                                st.rerun()
                            except IntegrityError:
                                db.rollback()
                                st.error("❌ 电话号码已存在")
                finally:
                    db.close()

            with tab4:
                st.subheader("商品列表")
                db = get_db()
                try:
                    products = db.query(Product).all()
                    if products:
                        st.dataframe(pd.DataFrame([{
                            "ID": p.id,
                            "名称": p.name,
                            "编码": p.code,
                            "分类": p.category,
                            "单价": f"¥{p.unit_price:.2f}",
                            "单位": p.unit
                        } for p in products]), use_container_width=True)
                    else:
                        st.info("暂无商品")

                    st.subheader("创建商品")
                    with st.form("create_product"):
                        name = st.text_input("商品名称*", max_chars=100)
                        code = st.text_input("商品编码*", max_chars=20)
                        category = st.text_input("分类*", max_chars=50)
                        unit_price = st.number_input("单价*", min_value=0.0, step=0.01, format="%.2f")
                        unit = st.text_input("单位*", max_chars=20)
                        if st.form_submit_button("创建商品", type="primary"):
                            try:
                                db.add(Product(name=name, code=code, category=category, unit_price=unit_price, unit=unit))
                                db.commit()
                                st.success("✅ 创建成功")
                                st.rerun()
                            except IntegrityError:
                                db.rollback()
                                st.error("❌ 商品编码已存在")
                finally:
                    db.close()

            with tab5:
                st.subheader("库存列表")
                db = get_db()
                try:
                    inventories = db.query(Inventory).all()
                    if inventories:
                        st.dataframe(pd.DataFrame([{
                            "ID": i.id,
                            "门店ID": i.store_id,
                            "商品ID": i.product_id,
                            "数量": i.quantity
                        } for i in inventories]), use_container_width=True)
                    else:
                        st.info("暂无库存数据")

                    st.subheader("库存入库")
                    with st.form("inventory_in"):
                        stores = db.query(Store).all()
                        products = db.query(Product).all()

                        if stores and products:
                            store_options = {f"{s.name} (ID:{s.id})": s.id for s in stores}
                            product_options = {f"{p.name} (¥{p.unit_price:.2f}/{p.unit})": p.id for p in products}

                            store_id = st.selectbox("选择门店*", options=list(store_options.keys()), format_func=lambda x: x.split('(')[0].strip())
                            product_id = st.selectbox("选择商品*", options=list(product_options.keys()), format_func=lambda x: x.split('(')[0].strip())
                            quantity = st.number_input("数量*", min_value=1)

                            if st.form_submit_button("入库", type="primary"):
                                try:
                                    actual_store_id = store_options[store_id]
                                    actual_product_id = product_options[product_id]

                                    # 检查是否已存在该库存记录
                                    existing = db.query(Inventory).filter(
                                        Inventory.store_id == actual_store_id,
                                        Inventory.product_id == actual_product_id
                                    ).first()

                                    if existing:
                                        existing.quantity += quantity
                                    else:
                                        db.add(Inventory(store_id=actual_store_id, product_id=actual_product_id, quantity=quantity))

                                    db.commit()
                                    st.success("✅ 入库成功")
                                    st.rerun()
                                except Exception as e:
                                    db.rollback()
                                    st.error(f"❌ 入库失败: {str(e)}")
                        else:
                            st.warning("请先创建门店和商品")
                finally:
                    db.close()

        # 开台管理
        elif page == "🪑 开台管理":
            st.header("🪑 开台管理")
            db = get_db()
            try:
                tables = db.query(Table).all()
                if tables:
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.subheader("所有台位")
                        for table in tables:
                            store = db.query(Store).filter(Store.id == table.store_id).first()
                            store_name = store.name if store else "未知"

                            if table.status == TableStatus.FREE:
                                st.info(f"🪑 **{table.name}** ({store_name}) - 容量: {table.capacity}人 - 状态: 空闲")
                            elif table.status == TableStatus.OCCUPIED:
                                st.warning(f"🪑 **{table.name}** ({store_name}) - 容量: {table.capacity}人 - 状态: 使用中")
                            elif table.status == TableStatus.RESERVED:
                                st.error(f"🪑 **{table.name}** ({store_name}) - 容量: {table.capacity}人 - 状态: 已预约")
                            else:
                                st.info(f"🪑 **{table.name}** ({store_name}) - 容量: {table.capacity}人 - 状态: 清理中")

                    with col2:
                        st.subheader("开台")
                        with st.form("open_table"):
                            free_tables = [t for t in tables if t.status == TableStatus.FREE]
                            if free_tables:
                                table_options = {f"{t.name} (容量:{t.capacity})": t.id for t in free_tables}
                                table_id = st.selectbox("选择台位", options=list(table_options.keys()))
                                member_phone = st.text_input("会员电话（可选）")
                                if st.form_submit_button("开台", type="primary"):
                                    try:
                                        actual_table_id = table_options[table_id]

                                        # 查找会员
                                        member = None
                                        if member_phone:
                                            member = db.query(Member).filter(Member.phone == member_phone).first()

                                        # 创建会话
                                        session = Session(table_id=actual_table_id, member_id=member.id if member else None)
                                        db.add(session)
                                        db.commit()

                                        # 更新台位状态
                                        table = db.query(Table).filter(Table.id == actual_table_id).first()
                                        table.status = TableStatus.OCCUPIED
                                        db.commit()

                                        st.success("✅ 开台成功")
                                        st.rerun()
                                    except Exception as e:
                                        db.rollback()
                                        st.error(f"❌ 开台失败: {str(e)}")
                            else:
                                st.info("没有可用台位")
                else:
                    st.warning("请先在「设置」中添加桌台")
            finally:
                db.close()

        # 点单管理
        elif page == "🛒 点单管理":
            st.header("🛒 点单管理")
            db = get_db()
            try:
                # 获取所有使用中的会话
                active_sessions = db.query(Session).filter(Session.status == SessionStatus.IN_PROGRESS).all()
                if active_sessions:
                    st.subheader("选择台位")
                    session_options = {f"台位 {db.query(Table).filter(Table.id == s.table_id).first().name}": s.id for s in active_sessions}
                    session_id = st.selectbox("选择台位", options=list(session_options.keys()))

                    if session_id:
                        actual_session_id = session_options[session_id]
                        session = db.query(Session).filter(Session.id == actual_session_id).first()

                        # 创建订单
                        st.subheader("选择商品")
                        products = db.query(Product).all()
                        product_options = {f"{p.name} (¥{p.unit_price:.2f}/{p.unit})": p.id for p in products}
                        selected_products = st.multiselect("选择商品", options=list(product_options.keys()))

                        quantities = {}
                        for product in selected_products:
                            quantities[product] = st.number_input(product, min_value=1, value=1, key=f"qty_{product}")

                        if st.button("确认点单", type="primary"):
                            try:
                                # 创建订单
                                order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                order = Order(
                                    order_no=order_no,
                                    table_id=session.table_id,
                                    member_id=session.member_id,
                                    status=OrderStatus.PENDING
                                )
                                db.add(order)
                                db.commit()

                                # 添加订单项
                                total_amount = 0.0
                                for product in selected_products:
                                    product_id = product_options[product]
                                    product_obj = db.query(Product).filter(Product.id == product_id).first()
                                    qty = quantities[product]
                                    subtotal = product_obj.unit_price * qty

                                    order_item = OrderItem(
                                        order_id=order.id,
                                        product_id=product_id,
                                        quantity=qty,
                                        unit_price=product_obj.unit_price,
                                        subtotal=subtotal
                                    )
                                    db.add(order_item)
                                    total_amount += subtotal

                                order.total_amount = total_amount
                                session.order_id = order.id
                                db.commit()

                                st.success(f"✅ 点单成功，订单号: {order_no}，总金额: ¥{total_amount:.2f}")
                                st.rerun()
                            except Exception as e:
                                db.rollback()
                                st.error(f"❌ 点单失败: {str(e)}")

                        # 显示当前订单
                        if session.order_id:
                            order = db.query(Order).filter(Order.id == session.order_id).first()
                            if order:
                                st.subheader("当前订单")
                                order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                                if order_items:
                                    st.dataframe(pd.DataFrame([{
                                        "商品": db.query(Product).filter(Product.id == oi.product_id).first().name,
                                        "数量": oi.quantity,
                                        "单价": f"¥{oi.unit_price:.2f}",
                                        "小计": f"¥{oi.subtotal:.2f}"
                                    } for oi in order_items]), use_container_width=True)
                                    st.metric("订单总额", f"¥{order.total_amount:.2f}")
                else:
                    st.info("暂无使用中的台位，请先开台")
            finally:
                db.close()

        # 结账管理
        elif page == "💳 结账管理":
            st.header("💳 结账管理")
            db = get_db()
            try:
                # 获取待结账的订单
                pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).all()
                if pending_orders:
                    st.subheader("待结账订单")
                    for order in pending_orders:
                        table = db.query(Table).filter(Table.id == order.table_id).first()
                        member = db.query(Member).filter(Member.id == order.member_id).first()

                        st.markdown(f"**订单号**: {order.order_no}")
                        st.markdown(f"**台位**: {table.name if table else '未知'}")
                        st.markdown(f"**会员**: {member.name if member else '散客'}")
                        st.markdown(f"**金额**: ¥{order.total_amount:.2f}")

                        col1, col2 = st.columns(2)
                        with col1:
                            payment_method = st.selectbox("支付方式", options=["wechat", "alipay", "cash", "card"], key=f"pay_{order.id}")
                        with col2:
                            if st.button("结账", type="primary", key=f"checkout_{order.id}"):
                                try:
                                    order.payment_method = PaymentMethod(payment_method)
                                    order.status = OrderStatus.PAID

                                    # 更新会话状态
                                    session = db.query(Session).filter(Session.order_id == order.id).first()
                                    if session:
                                        session.status = SessionStatus.PAID
                                        session.end_time = datetime.utcnow()
                                        if session.start_time:
                                            duration = (session.end_time - session.start_time).total_seconds() / 60
                                            session.duration_minutes = int(duration)

                                    # 更新台位状态
                                    if table:
                                        table.status = TableStatus.FREE

                                    db.commit()
                                    st.success("✅ 结账成功")
                                    st.rerun()
                                except Exception as e:
                                    db.rollback()
                                    st.error(f"❌ 结账失败: {str(e)}")

                        st.markdown("---")
                else:
                    st.info("暂无待结账订单")
            finally:
                db.close()

        # 会员管理
        elif page == "👥 会员管理":
            st.header("👥 会员管理")
            db = get_db()
            try:
                tab1, tab2 = st.tabs(["会员列表", "创建会员"])

                with tab1:
                    members = db.query(Member).all()
                    if members:
                        st.dataframe(pd.DataFrame([{
                            "ID": m.id,
                            "姓名": m.name,
                            "电话": m.phone,
                            "等级": m.level.value,
                            "余额": f"¥{m.balance:.2f}"
                        } for m in members]), use_container_width=True)
                    else:
                        st.info("暂无会员")
                with tab2:
                    with st.form("create_member"):
                        name = st.text_input("姓名*")
                        phone = st.text_input("电话*")
                        if st.form_submit_button("创建", type="primary"):
                            try:
                                db.add(Member(name=name, phone=phone))
                                db.commit()
                                st.success("✅ 创建成功")
                                st.rerun()
                            except IntegrityError:
                                db.rollback()
                                st.error("电话已存在")
            finally:
                db.close()

        # 订单管理
        elif page == "📝 订单管理":
            st.header("📝 订单管理")
            db = get_db()
            try:
                orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
                if orders:
                    st.dataframe(pd.DataFrame([{
                        "订单号": o.order_no,
                        "金额": f"¥{o.total_amount:.2f}",
                        "状态": o.status.value,
                        "时间": o.created_at.strftime("%Y-%m-%d %H:%M")
                    } for o in orders]), use_container_width=True)
                else:
                    st.info("暂无订单")
            finally:
                db.close()

        # 财务报表
        elif page == "💰 财务报表":
            st.header("💰 财务报表")
            db = get_db()
            try:
                tab1, tab2 = st.tabs(["营业额统计", "台位统计"])

                with tab1:
                    st.subheader("📊 营业额统计")
                    start_date = st.date_input("开始日期", value=date.today() - timedelta(days=7))
                    end_date = st.date_input("结束日期", value=date.today())

                    orders = db.query(Order).filter(
                        Order.created_at >= datetime.combine(start_date, datetime.min.time()),
                        Order.created_at <= datetime.combine(end_date, datetime.max.time())
                    ).all()

                    total_revenue = sum(o.total_amount for o in orders)
                    total_orders = len(orders)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("总营业额", f"¥{total_revenue:,.2f}")
                    with col2:
                        st.metric("总订单数", total_orders)

                    if orders:
                        # 按日期统计
                        df = pd.DataFrame([{
                            "日期": o.created_at.strftime("%Y-%m-%d"),
                            "金额": o.total_amount
                        } for o in orders])

                        df_grouped = df.groupby("日期").sum().reset_index()
                        st.dataframe(df_grouped, use_container_width=True)

                with tab2:
                    st.subheader("🪑 台位统计")
                    sessions = db.query(Session).all()

                    if sessions:
                        total_sessions = len(sessions)
                        completed_sessions = len([s for s in sessions if s.status == SessionStatus.COMPLETED])
                        avg_duration = sum(s.duration_minutes for s in sessions if s.duration_minutes) / completed_sessions if completed_sessions > 0 else 0

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("总开台数", total_sessions)
                        with col2:
                            st.metric("已结账台数", completed_sessions)
                        with col3:
                            st.metric("平均时长", format_duration(int(avg_duration)))

                        # 台位使用率统计
                        st.subheader("台位使用情况")
                        tables = db.query(Table).all()
                        table_stats = []
                        for t in tables:
                            session_count = db.query(Session).filter(Session.table_id == t.id).count()
                            table_stats.append({
                                "台位": t.name,
                                "开台次数": session_count
                            })
                        df = pd.DataFrame(table_stats)
                        st.dataframe(df, use_container_width=True)
            finally:
                db.close()

    except Exception as e:
        st.error(f"❌ 应用发生错误: {str(e)}")
        st.error("请检查日志或联系管理员")

if __name__ == "__main__":
    main()
