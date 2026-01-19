import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.exc import IntegrityError
import enum
import os

# 数据库配置
DATABASE_URL = "sqlite:///tea_house.db"
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
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    capacity = Column(Integer, default=4)
    status = Column(SQLEnum(TableStatus), default=TableStatus.FREE)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"))
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.IN_PROGRESS)
    total_amount = Column(Float, default=0.0)
    duration_minutes = Column(Integer, default=0)

class SessionItem(Base):
    __tablename__ = "session_items"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    order_time = Column(DateTime, default=datetime.utcnow)

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

# 数据库初始化和升级
def init_database():
    """初始化和升级数据库"""
    # 创建所有表（如果不存在）
    Base.metadata.create_all(bind=engine)

# 初始化数据库
init_database()

# Streamlit配置
st.set_page_config(page_title="连锁茶楼管理系统", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")

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
[data-testid="stSidebar"] [role="radiogroup"] label {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 8px 12px;
    color: #1f1f1f !important;
}

/* 导航栏 - 当前页面深灰色 */
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] {
    background-color: #6c757d !important;
    color: #ffffff !important;
    border-radius: 4px;
    margin: 4px 0;
}

/* 导航栏 - 当前页面文字颜色 */
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] * {
    color: #ffffff !important;
}

/* 按钮样式 - 确保文字可见 */
button[kind="primary"] {
    background-color: #ff6b6b !important;
    color: #ffffff !important;
    border: none !important;
}

button[kind="secondary"] {
    background-color: #6c757d !important;
    color: #ffffff !important;
    border: none !important;
}

/* 表单提交按钮样式 */
.stForm button {
    background-color: #ff6b6b !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🏪 连锁茶楼管理系统")

page = st.sidebar.radio(
    "选择功能",
    [
        "📊 控制台",
        "🎯 经营",
        "⚙️ 设置",
        "💎 会员管理",
        "📝 订单管理",
        "💰 财务报表"
    ],
    label_visibility="collapsed"
)

# 辅助函数
def format_duration(minutes):
    """格式化时长"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}小时{mins}分钟"
    return f"{mins}分钟"

def calculate_duration(start_time, end_time=None):
    """计算时长"""
    end = end_time or datetime.utcnow()
    delta = end - start_time
    return int(delta.total_seconds() // 60)

def get_status_color(status):
    """获取状态颜色"""
    color_map = {
        TableStatus.FREE: "🟢",
        TableStatus.OCCUPIED: "🔴",
        TableStatus.RESERVED: "🔵",
        TableStatus.CLEANING: "⚪"
    }
    return color_map.get(status, "⚪")

def get_status_text(status):
    """获取状态文本"""
    text_map = {
        TableStatus.FREE: "空闲",
        TableStatus.OCCUPIED: "使用中",
        TableStatus.RESERVED: "已预约",
        TableStatus.CLEANING: "清洁中"
    }
    return text_map.get(status, "未知")

# 控制台
if page == "📊 控制台":
    st.header("📊 控制台")
    db = get_db()
    try:
        today = date.today()
        
        # 今日订单
        orders_today = db.query(Order).filter(Order.created_at >= today).all()
        today_revenue = sum(o.total_amount for o in orders_today)
        
        # 今日开台
        sessions_today = db.query(Session).filter(Session.start_time >= today).all()
        today_sessions_count = len(sessions_today)
        
        # 进行中台位
        active_sessions = db.query(Session).filter(Session.status == SessionStatus.IN_PROGRESS).all()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("今日营业额", f"¥{today_revenue:,.2f}")
        with col2:
            st.metric("今日开台数", today_sessions_count)
        with col3:
            st.metric("进行中台位", len(active_sessions))
        with col4:
            st.metric("活跃门店", db.query(Store).filter(Store.status == StoreStatus.ACTIVE).count())
        
        # 进行中台位列表
        st.subheader("🎯 进行中的台位")
        if active_sessions:
            session_data = []
            for session in active_sessions:
                table = db.query(Table).get(session.table_id)
                duration = calculate_duration(session.start_time)
                member = db.query(Member).get(session.member_id) if session.member_id else None
                
                session_data.append({
                    "台位": table.name if table else "未知",
                    "会员": member.name if member else "散客",
                    "开始时间": session.start_time.strftime("%H:%M"),
                    "时长": format_duration(duration),
                    "消费金额": f"¥{session.total_amount:.2f}"
                })
            
            df = pd.DataFrame(session_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无进行中的台位")
        
        # 最近订单
        st.subheader("📝 最近订单")
        recent = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
        if recent:
            df = pd.DataFrame([{
                "订单号": o.order_no,
                "金额": f"¥{o.total_amount:.2f}",
                "时间": o.created_at.strftime("%H:%M")
            } for o in recent])
            st.dataframe(df, use_container_width=True)
    finally: 
        db.close()

# 经营（桌台管理）
elif page == "🎯 经营":
    st.header("🎯 经营管理")
    db = get_db()
    try:
        # 获取所有门店
        stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
        
        if not stores:
            st.warning("请先创建门店")
        else:
            # 选择门店
            store_options = [(s.id, s.name) for s in stores]
            store_id = st.selectbox("选择门店", store_options, format_func=lambda x: x[1])
            
            # 获取该门店所有桌台
            tables = db.query(Table).filter(Table.store_id == store_id[0]).all()
            
            if not tables:
                st.warning("该门店暂无桌台，请先添加桌台")
                st.info("提示：在门店管理中添加桌台")
            else:
                # 统计各状态数量
                status_counts = {status: 0 for status in TableStatus}
                for table in tables:
                    status_counts[table.status] += 1
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("空闲", status_counts[TableStatus.FREE])
                with col2:
                    st.metric("使用中", status_counts[TableStatus.OCCUPIED])
                with col3:
                    st.metric("已预约", status_counts[TableStatus.RESERVED])
                with col4:
                    st.metric("清洁中", status_counts[TableStatus.CLEANING])
                
                # 显示桌台列表
                st.subheader("🪑 桌台列表")
                
                # 按状态分组显示（不折叠）
                for status in [TableStatus.FREE, TableStatus.OCCUPIED, TableStatus.RESERVED, TableStatus.CLEANING]:
                    status_tables = [t for t in tables if t.status == status]
                    if status_tables:
                        # 状态标题
                        st.markdown(f"### {get_status_color(status)} {get_status_text(status)} ({len(status_tables)}个)")
                        
                        # 桌台卡片网格
                        cols = st.columns(4)
                        for idx, table in enumerate(status_tables):
                            col = cols[idx % 4]
                            with col:
                                # 获取该桌台的会话信息
                                session = db.query(Session).filter(
                                    Session.table_id == table.id,
                                    Session.status == SessionStatus.IN_PROGRESS
                                ).first()
                                
                                # 桌台卡片
                                if session:
                                    duration = calculate_duration(session.start_time)
                                    member = db.query(Member).get(session.member_id) if session.member_id else None
                                    button_text = f"{table.name}\n{get_status_color(status)} {format_duration(duration)}\n💰 ¥{session.total_amount:.2f}"
                                else:
                                    button_text = f"{table.name}\n{get_status_color(status)} {get_status_text(status)}\n👥 {table.capacity}人"
                                
                                if st.button(button_text, key=f"table_{table.id}", use_container_width=True, type="primary" if status == TableStatus.FREE else "secondary"):
                                    st.session_state['selected_table_id'] = table.id
                                    st.session_state['selected_table_name'] = table.name
                                    st.rerun()
                        
                        # 状态之间添加分隔线
                        st.divider()
                
                # 显示选中桌台的详情和操作面板
                if 'selected_table_id' in st.session_state:
                    st.divider()
                    st.subheader(f"🪑 {st.session_state['selected_table_name']} - 操作面板")
                    
                    table = db.query(Table).get(st.session_state['selected_table_id'])
                    
                    # 获取该桌台的会话
                    session = db.query(Session).filter(
                        Session.table_id == table.id,
                        Session.status == SessionStatus.IN_PROGRESS
                    ).first()
                    
                    if not session:
                        # 桌台空闲 - 显示开台界面
                        st.info("当前桌台空闲，可以进行开台")
                        
                        with st.form("open_table"):
                            members = db.query(Member).all()
                            member_options = [(0, "散客")] + [(m.id, f"{m.name} ({m.phone})") for m in members]
                            member_id = st.selectbox("选择会员（可选）", member_options, format_func=lambda x: x[1])
                            
                            if st.form_submit_button("🎯 开台", type="primary"):
                                # 创建会话
                                new_session = Session(
                                    table_id=table.id,
                                    store_id=table.store_id,
                                    member_id=member_id[0] if member_id[0] != 0 else None
                                )
                                db.add(new_session)
                                
                                # 更新桌台状态
                                table.status = TableStatus.OCCUPIED
                                
                                db.commit()
                                st.success(f"✅ {table.name} 开台成功！")
                                st.session_state.pop('selected_table_id', None)
                                st.session_state.pop('selected_table_name', None)
                                st.rerun()
                    else:
                        # 桌台使用中 - 显示操作选项
                        member = db.query(Member).get(session.member_id) if session.member_id else None
                        duration = calculate_duration(session.start_time)
                        
                        # 显示会话信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.info(f"👤 会员: {member.name if member else '散客'}")
                        with col2:
                            st.info(f"⏱️ 时长: {format_duration(duration)}")
                        with col3:
                            st.info(f"💰 消费: ¥{session.total_amount:.2f}")
                        
                        # 操作选项卡
                        tab1, tab2, tab3 = st.tabs(["📝 点单", "📋 消费明细", "💰 结账"])
                        
                        # 点单
                        with tab1:
                            products = db.query(Product).all()
                            if not products:
                                st.warning("暂无商品，请先创建商品")
                            else:
                                with st.form("add_order"):
                                    product_options = [(p.id, f"{p.name} - ¥{p.unit_price:.2f}/{p.unit}") for p in products]
                                    product_id = st.selectbox("选择商品", product_options, format_func=lambda x: x[1])
                                    quantity = st.number_input("数量", min_value=1, value=1)
                                    
                                    if st.form_submit_button("📝 点单", type="primary"):
                                        product = db.query(Product).get(product_id[0])
                                        if not product:
                                            st.error("商品不存在，请刷新页面重试")
                                            db.rollback()
                                            st.rerun()
                                        
                                        # 先保存商品信息，避免session问题
                                        product_name = product.name
                                        product_id_val = product.id
                                        unit_price = product.unit_price
                                        subtotal = unit_price * quantity
                                        
                                        # 创建会话点单
                                        session_item = SessionItem(
                                            session_id=session.id,
                                            product_id=product_id_val,
                                            quantity=quantity,
                                            unit_price=unit_price,
                                            subtotal=subtotal
                                        )
                                        db.add(session_item)
                                        
                                        # 更新会话总金额
                                        session.total_amount += subtotal
                                        
                                        # 扣减库存
                                        inv = db.query(Inventory).filter(
                                            Inventory.store_id == session.store_id,
                                            Inventory.product_id == product_id_val
                                        ).first()
                                        
                                        current_stock = inv.quantity if inv else 0
                                        
                                        if inv:
                                            if inv.quantity >= quantity:
                                                inv.quantity -= quantity
                                                message = f"✅ 点单成功！{product_name} x{quantity}，库存已扣减"
                                                message_type = "success"
                                            else:
                                                message = f"⚠️ 点单成功！但库存不足（当前库存: {inv.quantity}）"
                                                message_type = "warning"
                                        else:
                                            message = f"⚠️ 点单成功！但该商品暂无库存记录"
                                            message_type = "warning"
                                        
                                        db.commit()
                                        
                                        if message_type == "success":
                                            st.success(message)
                                        else:
                                            st.warning(message)
                                        st.rerun()
                        
                        # 消费明细
                        with tab2:
                            session_items = db.query(SessionItem).filter(SessionItem.session_id == session.id).all()
                            if session_items:
                                st.subheader("📋 已点商品明细")
                                for item in session_items:
                                    product = db.query(Product).get(item.product_id)
                                    if not product:
                                        continue
                                    
                                    product_name = product.name
                                    with st.container():
                                        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                                        with col1:
                                            st.text(f"🛍️ {product_name}")
                                        with col2:
                                            st.text(f"数量: {item.quantity}")
                                        with col3:
                                            st.text(f"单价: ¥{item.unit_price:.2f}")
                                        with col4:
                                            st.text(f"小计: ¥{item.subtotal:.2f}")
                                        with col5:
                                            if st.button("取消", key=f"cancel_{item.id}", type="secondary"):
                                                # 删除点单
                                                # 先保存需要的信息
                                                item_subtotal = item.subtotal
                                                item_quantity = item.quantity
                                                item_product_id = item.product_id
                                                
                                                # 恢复库存
                                                inv = db.query(Inventory).filter(
                                                    Inventory.store_id == session.store_id,
                                                    Inventory.product_id == item_product_id
                                                ).first()
                                                if inv:
                                                    inv.quantity += item_quantity

                                                # 扣减会话总金额
                                                session.total_amount -= item_subtotal

                                                # 删除点单记录
                                                db.delete(item)
                                                db.commit()
                                                st.success(f"✅ 已取消 {product_name}")
                                                st.rerun()

                                        st.caption(f"下单时间: {item.order_time.strftime('%Y-%m-%d %H:%M:%S')}")
                                        st.divider()
                            else:
                                st.info("暂未点单")
                        
                        # 结账
                        with tab3:
                            session_items = db.query(SessionItem).filter(SessionItem.session_id == session.id).all()

                            # 显示消费明细
                            if session_items:
                                st.subheader("📋 消费明细")
                                item_data = []
                                for item in session_items:
                                    product = db.query(Product).get(item.product_id)
                                    item_data.append({
                                        "商品": product.name,
                                        "数量": item.quantity,
                                        "小计": f"¥{item.subtotal:.2f}"
                                    })
                                df = pd.DataFrame(item_data)
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("暂未点单")

                            # 显示应付金额
                            st.divider()
                            st.warning(f"💰 应付金额: ¥{session.total_amount:.2f}")

                            # 如果没有开始结账流程
                            if 'checkout_table_id' not in st.session_state or st.session_state['checkout_table_id'] != table.id:
                                if st.button("💰 开始结账", type="primary", key="start_checkout"):
                                    st.session_state['checkout_table_id'] = table.id
                                    st.rerun()
                            else:
                                # 结账确认流程
                                st.subheader("💳 结账确认")

                                # 选择支付方式
                                payment_method = st.selectbox(
                                    "支付方式",
                                    [PaymentMethod.WECHAT, PaymentMethod.ALIPAY, PaymentMethod.CASH],
                                    format_func=lambda x: {"wechat": "微信", "alipay": "支付宝", "cash": "现金"}[x.value],
                                    key="payment_method"
                                )

                                # 输入实收金额
                                received_amount = st.number_input(
                                    "实收金额",
                                    min_value=0.0,
                                    step=0.01,
                                    value=float(session.total_amount),
                                    format="%.2f",
                                    key="received_amount"
                                )

                                # 显示校验结果
                                if abs(received_amount - session.total_amount) < 0.01:
                                    st.success("✅ 金额核对正确")
                                    confirm_enabled = True
                                else:
                                    st.error(f"❌ 金额不符，应付 ¥{session.total_amount:.2f}，实收 ¥{received_amount:.2f}")
                                    confirm_enabled = False

                                # 取消和确认按钮
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("❌ 取消", key="cancel_checkout"):
                                        st.session_state.pop('checkout_table_id', None)
                                        st.rerun()
                                with col2:
                                    if st.button("✅ 确认结账", key="confirm_checkout", disabled=not confirm_enabled, type="primary"):
                                        # 停止计时
                                        session.end_time = datetime.utcnow()
                                        session.duration_minutes = duration
                                        session.status = SessionStatus.COMPLETED

                                        # 更新桌台状态为空闲
                                        table.status = TableStatus.FREE

                                        # 创建订单
                                        order = Order(
                                            order_no=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                            store_id=session.store_id,
                                            member_id=session.member_id,
                                            total_amount=session.total_amount,
                                            payment_method=payment_method,
                                            status=OrderStatus.COMPLETED
                                        )
                                        db.add(order)
                                        db.flush()

                                        # 创建订单明细
                                        for item in session_items:
                                            order_item = OrderItem(
                                                order_id=order.id,
                                                product_id=item.product_id,
                                                quantity=item.quantity,
                                                unit_price=item.unit_price,
                                                subtotal=item.subtotal
                                            )
                                            db.add(order_item)

                                        db.commit()
                                        st.success(f"✅ 结账成功！订单号: {order.order_no}")
                                        st.session_state.pop('selected_table_id', None)
                                        st.session_state.pop('selected_table_name', None)
                                        st.session_state.pop('checkout_table_id', None)
                                        st.rerun()

                    # 关闭选中状态
                    if st.button("✖️ 关闭"):
                        st.session_state.pop('selected_table_id', None)
                        st.session_state.pop('selected_table_name', None)
                        st.rerun()
    finally:
        db.close()

# 设置页面
elif page == "⚙️ 设置":
    st.header("⚙️ 系统设置")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏪 门店管理",
        "🪑 桌台管理",
        "👥 员工管理",
        "🛍️ 商品管理",
        "📦 库存管理"
    ])
    
    db = get_db()
    try:
        # 门店管理
        with tab1:
            st.subheader("门店管理")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                stores = db.query(Store).all()
                if stores:
                    st.dataframe(pd.DataFrame([{
                        "名称": s.name,
                        "编码": s.code,
                        "地址": s.address or "-",
                        "电话": s.phone or "-",
                        "状态": "启用" if s.status == StoreStatus.ACTIVE else "停用"
                    } for s in stores]), use_container_width=True)
                else: 
                    st.info("暂无门店")
            
            with col2:
                st.write("### 新增门店")
                with st.form("create_store"):
                    name = st.text_input("门店名称*")
                    code = st.text_input("门店编码*")
                    address = st.text_input("地址")
                    phone = st.text_input("电话")
                    if st.form_submit_button("创建", type="primary"):
                        try:
                            db.add(Store(name=name, code=code, address=address, phone=phone))
                            db.commit()
                            st.success("✅ 创建成功")
                            st.rerun()
                        except IntegrityError:
                            db.rollback()
                            st.error("编码已存在")
        
        # 桌台管理
        with tab2:
            st.subheader("桌台管理")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
                if stores:
                    selected_store_id = st.selectbox(
                        "选择门店查看桌台",
                        [(s.id, s.name) for s in stores],
                        format_func=lambda x: x[1]
                    )
                    
                    tables = db.query(Table).filter(Table.store_id == selected_store_id[0]).all()
                    if tables:
                        st.dataframe(pd.DataFrame([{
                            "名称": t.name,
                            "编码": t.code,
                            "容量": f"{t.capacity}人",
                            "状态": get_status_text(t.status)
                        } for t in tables]), use_container_width=True)
                    else:
                        st.info("该门店暂无桌台")
                else:
                    st.warning("请先创建门店")
            
            with col2:
                st.write("### 新增桌台")
                if stores:
                    with st.form("create_table"):
                        name = st.text_input("桌台名称*")
                        code = st.text_input("桌台编码*")
                        capacity = st.number_input("容量（人数）*", min_value=1, value=4)
                        store_id = st.selectbox(
                            "所属门店*",
                            [(s.id, s.name) for s in stores],
                            format_func=lambda x: x[1]
                        )
                        if st.form_submit_button("创建", type="primary"):
                            try:
                                db.add(Table(
                                    name=name,
                                    code=code,
                                    capacity=capacity,
                                    store_id=store_id[0]
                                ))
                                db.commit()
                                st.success("✅ 创建成功")
                                st.rerun()
                            except IntegrityError:
                                db.rollback()
                                st.error("编码已存在")
                else:
                    st.warning("请先创建门店")
        
        # 员工管理
        with tab3:
            st.subheader("员工管理")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                emps = db.query(Employee).all()
                if emps:
                    emp_data = []
                    for e in emps:
                        store = db.query(Store).get(e.store_id)
                        emp_data.append({
                            "姓名": e.name,
                            "电话": e.phone,
                            "职位": e.position.value,
                            "所属门店": store.name if store else "未分配"
                        })
                    st.dataframe(pd.DataFrame(emp_data), use_container_width=True)
                else: 
                    st.info("暂无员工")
            
            with col2:
                st.write("### 新增员工")
                stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
                if stores:
                    with st.form("create_emp"):
                        name = st.text_input("姓名*")
                        phone = st.text_input("电话*")
                        pos = st.selectbox("职位", [EmployeePosition.MANAGER, EmployeePosition.STAFF, EmployeePosition.CASHIER], 
                                         format_func=lambda x: {"manager": "店长", "staff": "店员", "cashier": "收银员"}[x.value])
                        store_id = st.selectbox("所属门店*", [(s.id, s.name) for s in stores], format_func=lambda x: x[1])
                        if st.form_submit_button("创建", type="primary"):
                            try:
                                db.add(Employee(name=name, phone=phone, position=pos, store_id=store_id[0]))
                                db.commit()
                                st.success("✅ 创建成功")
                                st.rerun()
                            except IntegrityError:
                                db.rollback()
                                st.error("电话已存在")
                else:
                    st.warning("请先创建门店")
        
        # 商品管理
        with tab4:
            st.subheader("商品管理")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                products = db.query(Product).all()
                if products:
                    st.dataframe(pd.DataFrame([{
                        "名称": p.name,
                        "编码": p.code,
                        "分类": p.category,
                        "单价": f"¥{p.unit_price:.2f}",
                        "单位": p.unit
                    } for p in products]), use_container_width=True)
                else: 
                    st.info("暂无商品")
            
            with col2:
                st.write("### 新增商品")
                with st.form("create_product"):
                    name = st.text_input("商品名称*")
                    code = st.text_input("商品编码*")
                    category = st.selectbox("分类", ["茶叶", "茶具", "点心", "饮品"])
                    price = st.number_input("单价*", min_value=0.0, step=1.0)
                    unit = st.text_input("单位*")
                    if st.form_submit_button("创建", type="primary"):
                        try:
                            db.add(Product(name=name, code=code, category=category, unit_price=price, unit=unit))
                            db.commit()
                            st.success("✅ 创建成功")
                            st.rerun()
                        except IntegrityError:
                            db.rollback()
                            st.error("编码已存在")
        
        # 库存管理
        with tab5:
            st.subheader("库存管理")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
                if stores:
                    store_id = st.selectbox("选择门店", [(s.id, s.name) for s in stores], format_func=lambda x: x[1])
                    invs = db.query(Inventory).filter(Inventory.store_id == store_id[0]).all()
                    if invs:
                        data = []
                        for inv in invs:
                            p = db.query(Product).get(inv.product_id)
                            data.append({"商品": p.name, "数量": inv.quantity})
                        st.dataframe(pd.DataFrame(data), use_container_width=True)
                    else: 
                        st.info("暂无库存")
                else:
                    st.warning("请先创建门店")
            
            with col2:
                st.write("### 库存入库")
                stores = db.query(Store).filter(Store.status == StoreStatus.ACTIVE).all()
                products = db.query(Product).all()
                if stores and products:
                    with st.form("add_stock"):
                        sid = st.selectbox("门店", [(s.id, s.name) for s in stores], format_func=lambda x: x[1])
                        pid = st.selectbox("商品", [(p.id, p.name) for p in products], format_func=lambda x: x[1])
                        qty = st.number_input("数量*", min_value=1)
                        if st.form_submit_button("入库", type="primary"):
                            inv = db.query(Inventory).filter(Inventory.store_id == sid[0], Inventory.product_id == pid[0]).first()
                            if inv:
                                inv.quantity += qty
                            else:
                                db.add(Inventory(store_id=sid[0], product_id=pid[0], quantity=qty))
                            db.commit()
                            st.success("✅ 入库成功")
                            st.rerun()
                else:
                    st.warning("请先创建门店和商品")
    
    finally:
        db.close()

# 会员管理
elif page == "💎 会员管理":
    st.header("💎 会员管理")
    tab1, tab2 = st.tabs(["会员列表", "新增会员"])
    db = get_db()
    try:
        with tab1:
            members = db.query(Member).all()
            if members:
                st.dataframe(pd.DataFrame([{
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
