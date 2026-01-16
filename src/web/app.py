import streamlit as st
import pandas as pd
from datetime import datetime, date
from coze_coding_dev_sdk.database import get_session

# 导入各个Manager
from storage.database.store_manager import StoreManager, StoreCreate, StoreUpdate
from storage.database.employee_manager import EmployeeManager, EmployeeCreate, EmployeeUpdate
from storage.database.member_manager import MemberManager, MemberCreate, MemberUpdate
from storage.database.product_manager import ProductManager, ProductCreate, ProductUpdate
from storage.database.inventory_manager import InventoryManager
from storage.database.order_manager import OrderManager
from storage.database.financial_manager import FinancialManager

# 导入模型枚举
from storage.database.shared.model import (
    StoreStatus, EmployeePosition, MemberLevel,
    OrderStatus, PaymentMethod
)

# 页面配置
st.set_page_config(
    page_title="连锁茶楼管理系统",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; padding: 15px; border-radius: 10px;}
    .main-header {font-size: 32px; font-weight: bold; color: #1f77b4; margin-bottom: 20px;}
    .success-box {background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 5px solid #28a745;}
    .warning-box {background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 5px solid #ffc107;}
    .danger-box {background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 5px solid #dc3545;}
</style>
""", unsafe_allow_html=True)


def get_db():
    """获取数据库会话"""
    return get_session()


# ============ 控制台页面 ============
def show_dashboard():
    st.markdown('<div class="main-header">📊 控制台</div>', unsafe_allow_html=True)

    db = get_db()

    # 获取今日数据
    from storage.database.financial_manager import FinancialManager
    fin_mgr = FinancialManager()
    today_report = fin_mgr.get_daily_summary(db)

    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("今日订单数", today_report['order_count'])
    with col2:
        st.metric("今日营业额", f"¥{today_report['order_amount']:,.2f}")
    with col3:
        st.metric("净利润", f"¥{today_report['net_profit']:,.2f}")
    with col4:
        from storage.database.store_manager import StoreManager
        store_mgr = StoreManager()
        st.metric("活跃门店数", store_mgr.count_stores(db, status=StoreStatus.ACTIVE))

    st.markdown("---")

    # 门店营业额排名
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏪 门店营业额排名")
        store_comparison = fin_mgr.get_store_comparison(db)
        if store_comparison:
            df_store = pd.DataFrame(store_comparison)
            st.dataframe(df_store, use_container_width=True, hide_index=True)
        else:
            st.info("暂无门店数据")

    with col2:
        st.subheader("👥 会员统计")
        member_stats = fin_mgr.get_member_statistics(db)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("会员总数", member_stats['total_members'])
        with col2:
            st.metric("活跃会员", member_stats['active_members'])
        with col3:
            st.metric("总储值", f"¥{member_stats['total_balance']:,.2f}")

    st.markdown("---")

    # 最近订单
    st.subheader("📝 最近订单")
    from storage.database.order_manager import OrderManager
    order_mgr = OrderManager()
    recent_orders = order_mgr.get_orders(db, skip=0, limit=10)
    if recent_orders:
        orders_data = []
        for order in recent_orders:
            orders_data.append({
                "订单号": order.order_no,
                "门店ID": order.store_id,
                "会员ID": order.member_id if order.member_id else "-",
                "金额": f"¥{order.paid_amount:,.2f}",
                "状态": order.status.value,
                "时间": order.order_time.strftime("%Y-%m-%d %H:%M")
            })
        df_orders = pd.DataFrame(orders_data)
        st.dataframe(df_orders, use_container_width=True, hide_index=True)
    else:
        st.info("暂无订单数据")

    db.close()


# ============ 门店管理页面 ============
def show_store_management():
    st.markdown('<div class="main-header">🏪 门店管理</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["门店列表", "新增门店"])

    db = get_db()
    mgr = StoreManager()

    # 门店列表
    with tab1:
        stores = mgr.get_stores(db, skip=0, limit=100)

        if stores:
            stores_data = []
            for store in stores:
                stores_data.append({
                    "ID": store.id,
                    "门店名称": store.name,
                    "编码": store.code,
                    "地址": store.address,
                    "电话": store.phone,
                    "店长": store.manager_name or "-",
                    "状态": store.status.value,
                    "营业时间": f"{store.open_time or '-'}-{store.close_time or '-'}"
                })
            df = pd.DataFrame(stores_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无门店数据")

    # 新增门店
    with tab2:
        with st.form("create_store_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("门店名称 *", placeholder="如：西湖茶楼")
                code = st.text_input("门店编码 *", placeholder="如：ST001")
                address = st.text_input("门店地址 *", placeholder="如：杭州市西湖区")
            with col2:
                phone = st.text_input("联系电话 *", placeholder="如：0571-12345678")
                manager_name = st.text_input("店长姓名", placeholder="选填")
                manager_phone = st.text_input("店长电话", placeholder="选填")

            col3, col4 = st.columns(2)
            with col3:
                open_time = st.text_input("营业开始时间", placeholder="如：09:00")
            with col4:
                close_time = st.text_input("营业结束时间", placeholder="如：22:00")

            submitted = st.form_submit_button("创建门店", type="primary")

            if submitted:
                if not name or not code or not address or not phone:
                    st.error("请填写必填项（标有*的字段）")
                else:
                    try:
                        store_in = StoreCreate(
                            name=name, code=code, address=address, phone=phone,
                            manager_name=manager_name if manager_name else None,
                            manager_phone=manager_phone if manager_phone else None,
                            open_time=open_time if open_time else None,
                            close_time=close_time if close_time else None
                        )
                        store = mgr.create_store(db, store_in)
                        st.success(f"✅ 门店创建成功！ID: {store.id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 创建失败: {str(e)}")

    db.close()


# ============ 员工管理页面 ============
def show_employee_management():
    st.markdown('<div class="main-header">👥 员工管理</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["员工列表", "新增员工"])

    db = get_db()
    mgr = EmployeeManager()

    # 获取门店列表供选择
    from storage.database.store_manager import StoreManager
    store_mgr = StoreManager()
    stores = store_mgr.get_stores(db, skip=0, limit=100)
    store_options = {f"{s.id} - {s.name}": s.id for s in stores}

    # 员工列表
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            filter_store = st.selectbox("筛选门店", ["全部"] + list(store_options.keys()))
        with col2:
            filter_position = st.selectbox("筛选职位", ["全部", "manager", "cashier", "waiter", "chef"])

        store_id = store_options[filter_store] if filter_store != "全部" else None
        position = filter_position if filter_position != "全部" else None

        employees = mgr.get_employees(db, skip=0, limit=100, store_id=store_id, position=position)

        if employees:
            employees_data = []
            for emp in employees:
                employees_data.append({
                    "ID": emp.id,
                    "姓名": emp.name,
                    "电话": emp.phone,
                    "职位": emp.position.value,
                    "门店ID": emp.store_id,
                    "状态": "在职" if emp.status else "离职"
                })
            df = pd.DataFrame(employees_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无员工数据")

    # 新增员工
    with tab2:
        with st.form("create_employee_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("员工姓名 *", placeholder="如：张三")
                phone = st.text_input("联系电话 *", placeholder="如：13800138000")
            with col2:
                position = st.selectbox("职位 *", ["manager", "cashier", "waiter", "chef"],
                                      format_func=lambda x: {"manager": "店长", "cashier": "收银员", "waiter": "服务员", "chef": "厨师"}[x])
                store_id = st.selectbox("所属门店 *", list(store_options.keys()),
                                      format_func=lambda x: x.split(" - ")[1])

            email = st.text_input("邮箱", placeholder="选填")

            submitted = st.form_submit_button("创建员工", type="primary")

            if submitted:
                if not name or not phone or not store_id:
                    st.error("请填写必填项")
                else:
                    try:
                        emp_in = EmployeeCreate(
                            name=name, phone=phone, position=EmployeePosition(position),
                            store_id=store_options[store_id], email=email if email else None
                        )
                        emp = mgr.create_employee(db, emp_in)
                        st.success(f"✅ 员工创建成功！ID: {emp.id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 创建失败: {str(e)}")

    db.close()


# ============ 会员管理页面 ============
def show_member_management():
    st.markdown('<div class="main-header">💎 会员管理</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["会员列表", "新增会员", "会员充值"])

    db = get_db()
    mgr = MemberManager()

    # 会员列表
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            filter_level = st.selectbox("筛选等级", ["全部", "normal", "bronze", "silver", "gold", "platinum"])
        with col2:
            keyword = st.text_input("搜索", placeholder="姓名/手机号/会员编号")

        member_level = filter_level if filter_level != "全部" else None
        members = mgr.get_members(db, skip=0, limit=100, level=member_level, keyword=keyword)

        if members:
            members_data = []
            for member in members:
                members_data.append({
                    "ID": member.id,
                    "会员编号": member.member_no,
                    "姓名": member.name,
                    "手机号": member.phone,
                    "等级": member.level.value,
                    "积分": member.points,
                    "余额": f"¥{member.balance:,.2f}",
                    "累计消费": f"¥{member.total_consumption:,.2f}",
                    "状态": "正常" if member.status else "禁用"
                })
            df = pd.DataFrame(members_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无会员数据")

    # 新增会员
    with tab2:
        with st.form("create_member_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("会员姓名 *", placeholder="如：李四")
                phone = st.text_input("手机号 *", placeholder="如：13900139000")
            with col2:
                level = st.selectbox("会员等级", ["normal", "bronze", "silver", "gold", "platinum"],
                                   format_func=lambda x: {"normal": "普通", "bronze": "青铜", "silver": "白银",
                                                         "gold": "黄金", "platinum": "铂金"}[x])
                email = st.text_input("邮箱", placeholder="选填")

            submitted = st.form_submit_button("创建会员", type="primary")

            if submitted:
                if not name or not phone:
                    st.error("请填写必填项")
                else:
                    try:
                        member_in = MemberCreate(
                            name=name, phone=phone, email=email if email else None,
                            level=MemberLevel(level)
                        )
                        member = mgr.create_member(db, member_in)
                        st.success(f"✅ 会员创建成功！编号: {member.member_no}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 创建失败: {str(e)}")

    # 会员充值
    with tab3:
        members = mgr.get_members(db, skip=0, limit=100)
        member_options = {f"{m.id} - {m.name} ({m.member_no})": m.id for m in members}

        with st.form("recharge_form"):
            member_id = st.selectbox("选择会员", list(member_options.keys()))
            amount = st.number_input("充值金额", min_value=0.01, value=100.0, step=10.0)

            submitted = st.form_submit_button("确认充值", type="primary")

            if submitted:
                try:
                    member = mgr.update_balance(db, member_options[member_id], amount)
                    st.success(f"✅ 充值成功！当前余额: ¥{member.balance:,.2f}")
                except Exception as e:
                    st.error(f"❌ 充值失败: {str(e)}")

    db.close()


# ============ 商品管理页面 ============
def show_product_management():
    st.markdown('<div class="main-header">🛍️ 商品管理</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["商品列表", "新增商品"])

    db = get_db()
    mgr = ProductManager()

    # 商品列表
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            filter_category = st.text_input("筛选分类", placeholder="如：茶叶")
        with col2:
            keyword = st.text_input("搜索", placeholder="商品名称/编码")

        products = mgr.get_products(db, skip=0, limit=100, category=filter_category, keyword=keyword)

        if products:
            products_data = []
            for prod in products:
                products_data.append({
                    "ID": prod.id,
                    "商品名称": prod.name,
                    "编码": prod.code,
                    "分类": prod.category,
                    "单价": f"¥{prod.price:.2f}",
                    "成本价": f"¥{prod.cost_price:.2f}" if prod.cost_price else "-",
                    "单位": prod.unit,
                    "状态": "上架" if prod.status else "下架"
                })
            df = pd.DataFrame(products_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无商品数据")

    # 新增商品
    with tab2:
        with st.form("create_product_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("商品名称 *", placeholder="如：龙井茶")
                code = st.text_input("商品编码 *", placeholder="如：P001")
                category = st.text_input("商品分类 *", placeholder="如：茶叶")
            with col2:
                price = st.number_input("单价 *", min_value=0.01, value=50.0, step=1.0)
                cost_price = st.number_input("成本价", min_value=0.0, value=0.0, step=1.0)
                unit = st.text_input("单位 *", placeholder="如：克")

            description = st.text_area("商品描述", placeholder="选填")

            submitted = st.form_submit_button("创建商品", type="primary")

            if submitted:
                if not name or not code or not category or not unit:
                    st.error("请填写必填项")
                else:
                    try:
                        prod_in = ProductCreate(
                            name=name, code=code, category=category, price=price,
                            cost_price=cost_price if cost_price > 0 else None,
                            unit=unit, description=description if description else None
                        )
                        prod = mgr.create_product(db, prod_in)
                        st.success(f"✅ 商品创建成功！ID: {prod.id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 创建失败: {str(e)}")

    db.close()


# ============ 库存管理页面 ============
def show_inventory_management():
    st.markdown('<div class="main-header">📦 库存管理</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["库存查询", "库存入库"])

    db = get_db()
    mgr = InventoryManager()

    # 获取门店和商品列表
    from storage.database.store_manager import StoreManager
    from storage.database.product_manager import ProductManager
    store_mgr = StoreManager()
    product_mgr = ProductManager()

    stores = store_mgr.get_stores(db, skip=0, limit=100)
    products = product_mgr.get_products(db, skip=0, limit=100)

    store_options = {f"{s.id} - {s.name}": s.id for s in stores}
    product_options = {f"{p.id} - {p.name}": p.id for p in products}

    # 库存查询
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            selected_store = st.selectbox("选择门店", list(store_options.keys()))
        with col2:
            show_warning_only = st.checkbox("仅显示预警商品")

        inventories = mgr.get_inventories(
            db, skip=0, limit=100,
            store_id=store_options[selected_store],
            low_stock_only=show_warning_only
        )

        if inventories:
            inv_data = []
            for inv in inventories:
                inv_data.append({
                    "商品ID": inv.product_id,
                    "库存数量": inv.quantity,
                    "预警阈值": inv.warning_threshold,
                    "状态": "⚠️ 库存不足" if inv.quantity <= inv.warning_threshold else "✅ 正常"
                })
            df = pd.DataFrame(inv_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无库存数据")

    # 库存入库
    with tab2:
        with st.form("inventory_in_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                store_id = st.selectbox("门店", list(store_options.keys()))
            with col2:
                product_id = st.selectbox("商品", list(product_options.keys()))
            with col3:
                quantity = st.number_input("入库数量", min_value=0.01, value=100.0, step=10.0)

            remark = st.text_input("备注", placeholder="如：采购入库")

            submitted = st.form_submit_button("确认入库", type="primary")

            if submitted:
                try:
                    inventory = mgr.adjust_inventory(
                        db, store_options[store_id], product_options[product_id],
                        quantity, "purchase", remark=remark if remark else None
                    )
                    st.success(f"✅ 入库成功！当前库存: {inventory.quantity}")
                except Exception as e:
                    st.error(f"❌ 入库失败: {str(e)}")

    db.close()


# ============ 订单管理页面 ============
def show_order_management():
    st.markdown('<div class="main-header">📝 订单管理</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["订单列表", "创建订单"])

    db = get_db()
    mgr = OrderManager()

    # 获取门店、商品、会员列表
    from storage.database.store_manager import StoreManager
    from storage.database.product_manager import ProductManager
    from storage.database.member_manager import MemberManager

    store_mgr = StoreManager()
    product_mgr = ProductManager()
    member_mgr = MemberManager()

    stores = store_mgr.get_stores(db, skip=0, limit=100)
    products = product_mgr.get_products(db, skip=0, limit=100)
    members = member_mgr.get_members(db, skip=0, limit=100)

    store_options = {f"{s.id} - {s.name}": s.id for s in stores}
    product_options = {f"{p.id} - {p.name} (¥{p.price:.2f}/{p.unit})": p.id for p in products}
    member_options = {f"{m.id} - {m.name}": m.id for m in members}

    # 订单列表
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            filter_store = st.selectbox("筛选门店", ["全部"] + list(store_options.keys()))
        with col2:
            filter_status = st.selectbox("筛选状态", ["全部", "pending", "paid", "completed", "cancelled", "refunded"])

        store_id = store_options[filter_store] if filter_store != "全部" else None
        status = filter_status if filter_status != "全部" else None

        orders = mgr.get_orders(db, skip=0, limit=100, store_id=store_id, status=status)

        if orders:
            orders_data = []
            for order in orders:
                orders_data.append({
                    "订单号": order.order_no,
                    "门店ID": order.store_id,
                    "会员ID": order.member_id if order.member_id else "-",
                    "金额": f"¥{order.paid_amount:,.2f}",
                    "支付方式": order.payment_method.value,
                    "状态": order.status.value,
                    "时间": order.order_time.strftime("%Y-%m-%d %H:%M")
                })
            df = pd.DataFrame(orders_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无订单数据")

    # 创建订单
    with tab2:
        st.info("💡 提示：创建订单后需要支付，系统会自动扣减库存")

        with st.form("create_order_form"):
            col1, col2 = st.columns(2)
            with col1:
                store_id = st.selectbox("门店 *", list(store_options.keys()))
                member_id = st.selectbox("会员（可选）", ["无会员"] + list(member_options.keys()))
            with col2:
                payment_method = st.selectbox("支付方式 *",
                    ["wechat", "alipay", "cash", "card", "member_balance"],
                    format_func=lambda x: {"wechat": "微信支付", "alipay": "支付宝", "cash": "现金",
                                          "card": "刷卡", "member_balance": "会员余额"}[x])

            st.subheader("商品明细")
            products_count = st.number_input("商品种类数量", min_value=1, max_value=10, value=1)

            order_items = []
            for i in range(products_count):
                st.markdown(f"**商品 {i+1}**")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    p_id = st.selectbox(f"选择商品 {i+1}", list(product_options.keys()), key=f"product_{i}")
                with col_b:
                    p_quantity = st.number_input(f"数量 {i+1}", min_value=0.01, value=1.0, key=f"quantity_{i}")
                with col_c:
                    p_price = products[product_options[p_id] - 1].price if product_options else 0.0
                    st.info(f"单价: ¥{p_price:.2f}")

                order_items.append({
                    "product_id": product_options[p_id],
                    "quantity": p_quantity,
                    "price": p_price
                })

            remark = st.text_input("备注", placeholder="选填")

            submitted = st.form_submit_button("创建订单", type="primary")

            if submitted:
                try:
                    from storage.database.order_manager import OrderItemCreate

                    items_data = []
                    for item in order_items:
                        # 获取商品名称
                        product = product_mgr.get_product_by_id(db, item['product_id'])
                        items_data.append(OrderItemCreate(
                            product_id=item['product_id'],
                            product_name=product.name if product else f"商品{item['product_id']}",
                            quantity=item['quantity'],
                            unit_price=item['price']
                        ))

                    from storage.database.order_manager import OrderCreate
                    order_in = OrderCreate(
                        store_id=store_options[store_id],
                        member_id=member_options[member_id] if member_id != "无会员" else None,
                        items=items_data,
                        payment_method=PaymentMethod(payment_method),
                        remark=remark if remark else None
                    )
                    order = mgr.create_order(db, order_in)

                    # 自动支付
                    order = mgr.pay_order(db, order.id, PaymentMethod(payment_method))

                    st.success(f"✅ 订单创建并支付成功！订单号: {order.order_no}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 创建失败: {str(e)}")

    db.close()


# ============ 财务报表页面 ============
def show_financial_reports():
    st.markdown('<div class="main-header">💰 财务报表</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["日报表", "月报表", "门店对比"])

    db = get_db()
    mgr = FinancialManager()

    # 获取门店列表
    from storage.database.store_manager import StoreManager
    store_mgr = StoreManager()
    stores = store_mgr.get_stores(db, skip=0, limit=100)
    store_options = {f"{s.id} - {s.name}": s.id for s in stores}

    # 日报表
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_date = st.date_input("选择日期", date.today())
        with col2:
            selected_store = st.selectbox("选择门店", ["全部"] + list(store_options.keys()))
        with col3:
            st.write("")
            st.write("")
            st.write("")
            view_btn = st.button("查询", type="primary")

        if view_btn or 'daily_report_shown' in st.session_state:
            st.session_state.daily_report_shown = True
            store_id = store_options[selected_store] if selected_store != "全部" else None
            report = mgr.get_daily_summary(db, store_id, datetime.combine(selected_date, datetime.min.time()))

            # 显示报表
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("订单数量", report['order_count'])
                st.metric("订单金额", f"¥{report['order_amount']:,.2f}")
            with col2:
                st.metric("收入金额", f"¥{report['income_amount']:,.2f}")
                st.metric("支出金额", f"¥{report['expense_amount']:,.2f}")
            with col3:
                st.metric("退款金额", f"¥{report['refund_amount']:,.2f}")
                st.metric("净利润", f"¥{report['net_profit']:,.2f}")

    # 月报表
    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_month = st.date_input("选择月份", date.today(), value=date.today().replace(day=1))
        with col2:
            selected_store = st.selectbox("选择门店（月报）", ["全部"] + list(store_options.keys()), key="monthly_store")
        with col3:
            st.write("")
            st.write("")
            st.write("")
            view_btn_monthly = st.button("查询", type="primary", key="monthly_query")

        if view_btn_monthly or 'monthly_report_shown' in st.session_state:
            st.session_state.monthly_report_shown = True
            store_id = store_options[selected_store] if selected_store != "全部" else None
            report = mgr.get_monthly_summary(db, store_id, selected_month.year, selected_month.month)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("订单数量", report['order_count'])
                st.metric("订单金额", f"¥{report['order_amount']:,.2f}")
            with col2:
                st.metric("日均订单", f"{report['avg_daily_orders']:.2f}")
                st.metric("日均收入", f"¥{report['avg_daily_income']:,.2f}")
            with col3:
                st.metric("净利润", f"¥{report['net_profit']:,.2f}")
                st.metric("总营收", f"¥{report['total_income']:,.2f}")

    # 门店对比
    with tab3:
        if st.button("生成门店对比", type="primary"):
            results = mgr.get_store_comparison(db)
            if results:
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无门店数据")

    db.close()


# ============ 主程序 ============
def main():
    # 侧边栏
    with st.sidebar:
        st.title("🏪 连锁茶楼管理系统")
        st.markdown("---")

        page = st.radio(
            "导航菜单",
            [
                "📊 控制台",
                "🏪 门店管理",
                "👥 员工管理",
                "💎 会员管理",
                "🛍️ 商品管理",
                "📦 库存管理",
                "📝 订单管理",
                "💰 财务报表"
            ]
        )

        st.markdown("---")
        st.markdown("### 📞 联系支持")
        st.info("如有问题请联系系统管理员")

    # 页面路由
    if page == "📊 控制台":
        show_dashboard()
    elif page == "🏪 门店管理":
        show_store_management()
    elif page == "👥 员工管理":
        show_employee_management()
    elif page == "💎 会员管理":
        show_member_management()
    elif page == "🛍️ 商品管理":
        show_product_management()
    elif page == "📦 库存管理":
        show_inventory_management()
    elif page == "📝 订单管理":
        show_order_management()
    elif page == "💰 财务报表":
        show_financial_reports()


if __name__ == "__main__":
    main()
