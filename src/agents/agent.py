import os
import json
from typing import Annotated, Optional
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import default_headers
from coze_coding_dev_sdk.database import get_session
from storage.memory.memory_saver import get_memory_saver

# 导入各个 Manager
from storage.database.store_manager import StoreManager, StoreCreate, StoreUpdate
from storage.database.employee_manager import EmployeeManager, EmployeeCreate, EmployeeUpdate
from storage.database.member_manager import MemberManager, MemberCreate, MemberUpdate
from storage.database.product_manager import ProductManager, ProductCreate, ProductUpdate
from storage.database.inventory_manager import InventoryManager, InventoryCreate, InventoryUpdate
from storage.database.order_manager import OrderManager, OrderCreate, OrderUpdate, OrderItemCreate
from storage.database.financial_manager import FinancialManager, FinancialRecordCreate

# 导入模型
from storage.database.shared.model import (
    StoreStatus, OrderStatus, PaymentMethod,
    InventoryChangeType, MemberLevel, EmployeePosition
)

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

# ============ 门店管理工具 ============

@tool
def create_store(name: str, code: str, address: str, phone: str,
                 manager_name: Optional[str] = None,
                 manager_phone: Optional[str] = None,
                 open_time: Optional[str] = None,
                 close_time: Optional[str] = None) -> str:
    """创建新门店\n\n参数:\n- name: 门店名称\n- code: 门店编码\n- address: 门店地址\n- phone: 联系电话\n- manager_name: 店长姓名(可选)\n- manager_phone: 店长电话(可选)\n- open_time: 营业开始时间(可选)\n- close_time: 营业结束时间(可选)"""
    db = get_session()
    try:
        mgr = StoreManager()
        store_in = StoreCreate(
            name=name, code=code, address=address, phone=phone,
            manager_name=manager_name, manager_phone=manager_phone,
            open_time=open_time, close_time=close_time
        )
        store = mgr.create_store(db, store_in)
        return f"✅ 门店创建成功！\n门店ID: {store.id}\n门店名称: {store.name}\n门店编码: {store.code}\n状态: {store.status.value}"
    except Exception as e:
        return f"❌ 创建门店失败: {str(e)}"
    finally:
        db.close()

@tool
def get_stores(status: Optional[str] = None, limit: int = 20) -> str:
    """获取门店列表\n\n参数:\n- status: 门店状态(active/inactive/closed, 可选)\n- limit: 返回数量限制, 默认20"""
    db = get_session()
    try:
        mgr = StoreManager()
        store_status = StoreStatus(status) if status else None
        stores = mgr.get_stores(db, skip=0, limit=limit, status=store_status)

        if not stores:
            return "暂无门店数据"

        result = "📋 门店列表:\n\n"
        for store in stores:
            result += f"【{store.id}】{store.name}\n"
            result += f"  编码: {store.code}\n"
            result += f"  地址: {store.address}\n"
            result += f"  电话: {store.phone}\n"
            result += f"  状态: {store.status.value}\n"
            if store.manager_name is not None:
                result += f"  店长: {store.manager_name}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"❌ 查询门店失败: {str(e)}"
    finally:
        db.close()

@tool
def update_store(store_id: int, name: Optional[str] = None,
                 address: Optional[str] = None, phone: Optional[str] = None,
                 status: Optional[str] = None) -> str:
    """更新门店信息\n\n参数:\n- store_id: 门店ID\n- name: 门店名称(可选)\n- address: 门店地址(可选)\n- phone: 联系电话(可选)\n- status: 门店状态(active/inactive/closed, 可选)"""
    db = get_session()
    try:
        mgr = StoreManager()
        update_data = {}
        if name: update_data['name'] = name
        if address: update_data['address'] = address
        if phone: update_data['phone'] = phone
        if status: update_data['status'] = StoreStatus(status)

        store_in = StoreUpdate(**update_data)
        store = mgr.update_store(db, store_id, store_in)

        if not store:
            return f"❌ 未找到ID为 {store_id} 的门店"

        return f"✅ 门店更新成功！\n门店ID: {store.id}\n门店名称: {store.name}\n状态: {store.status.value}"
    except Exception as e:
        return f"❌ 更新门店失败: {str(e)}"
    finally:
        db.close()

# ============ 员工管理工具 ============

@tool
def create_employee(name: str, phone: str, position: str, store_id: int,
                    email: Optional[str] = None) -> str:
    """创建新员工\n\n参数:\n- name: 员工姓名\n- phone: 联系电话\n- position: 职位(manager/cashier/waiter/chef)\n- store_id: 所属门店ID\n- email: 邮箱(可选)"""
    db = get_session()
    try:
        mgr = EmployeeManager()
        employee_in = EmployeeCreate(
            name=name, phone=phone, position=EmployeePosition(position),
            store_id=store_id, email=email
        )
        employee = mgr.create_employee(db, employee_in)
        return f"✅ 员工创建成功！\n员工ID: {employee.id}\n姓名: {employee.name}\n职位: {employee.position.value}\n所属门店: {employee.store_id}"
    except Exception as e:
        return f"❌ 创建员工失败: {str(e)}"
    finally:
        db.close()

@tool
def get_employees(store_id: Optional[int] = None, position: Optional[str] = None,
                  limit: int = 20) -> str:
    """获取员工列表\n\n参数:\n- store_id: 门店ID(可选)\n- position: 职位(manager/cashier/waiter/chef, 可选)\n- limit: 返回数量限制, 默认20"""
    db = get_session()
    try:
        mgr = EmployeeManager()
        emp_position = EmployeePosition(position) if position else None
        employees = mgr.get_employees(db, skip=0, limit=limit,
                                      store_id=store_id, position=emp_position)

        if not employees:
            return "暂无员工数据"

        result = "📋 员工列表:\n\n"
        for emp in employees:
            result += f"【{emp.id}】{emp.name}\n"
            result += f"  职位: {emp.position.value}\n"
            result += f"  电话: {emp.phone}\n"
            result += f"  门店ID: {emp.store_id}\n"
            result += f"  状态: {'在职' if emp.status is not False else '离职'}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"❌ 查询员工失败: {str(e)}"
    finally:
        db.close()

# ============ 会员管理工具 ============

@tool
def create_member(name: str, phone: str, email: Optional[str] = None,
                  level: Optional[str] = None) -> str:
    """创建新会员\n\n参数:\n- name: 会员姓名\n- phone: 手机号\n- email: 邮箱(可选)\n- level: 会员等级(normal/bronze/silver/gold/platinum, 可选)"""
    db = get_session()
    try:
        mgr = MemberManager()
        member_level = MemberLevel(level) if level else MemberLevel.NORMAL
        member_in = MemberCreate(
            name=name, phone=phone, email=email, level=member_level
        )
        member = mgr.create_member(db, member_in)
        return f"✅ 会员创建成功！\n会员ID: {member.id}\n会员编号: {member.member_no}\n姓名: {member.name}\n等级: {member.level.value}\n积分: {member.points}"
    except Exception as e:
        return f"❌ 创建会员失败: {str(e)}"
    finally:
        db.close()

@tool
def get_members(level: Optional[str] = None, keyword: Optional[str] = None,
                limit: int = 20) -> str:
    """获取会员列表\n\n参数:\n- level: 会员等级(normal/bronze/silver/gold/platinum, 可选)\n- keyword: 搜索关键词(姓名/手机号/会员编号, 可选)\n- limit: 返回数量限制, 默认20"""
    db = get_session()
    try:
        mgr = MemberManager()
        member_level = MemberLevel(level) if level else None
        members = mgr.get_members(db, skip=0, limit=limit,
                                  level=member_level, keyword=keyword)

        if not members:
            return "暂无会员数据"

        result = "📋 会员列表:\n\n"
        for member in members:
            result += f"【{member.id}】{member.name}\n"
            result += f"  会员编号: {member.member_no}\n"
            result += f"  手机号: {member.phone}\n"
            result += f"  等级: {member.level.value}\n"
            result += f"  积分: {member.points}\n"
            result += f"  余额: ¥{member.balance:.2f}\n"
            result += f"  累计消费: ¥{member.total_consumption:.2f}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"❌ 查询会员失败: {str(e)}"
    finally:
        db.close()

@tool
def member_recharge(member_id: int, amount: float) -> str:
    """会员充值\n\n参数:\n- member_id: 会员ID\n- amount: 充值金额"""
    db = get_session()
    try:
        mgr = MemberManager()
        member = mgr.update_balance(db, member_id, amount)
        return f"✅ 充值成功！\n会员ID: {member.id}\n当前余额: ¥{member.balance:.2f}"
    except Exception as e:
        return f"❌ 充值失败: {str(e)}"
    finally:
        db.close()

# ============ 商品管理工具 ============

@tool
def create_product(name: str, code: str, category: str, price: float, unit: str,
                   cost_price: Optional[float] = None,
                   description: Optional[str] = None) -> str:
    """创建新商品\n\n参数:\n- name: 商品名称\n- code: 商品编码\n- category: 商品分类\n- price: 单价\n- unit: 单位\n- cost_price: 成本价(可选)\n- description: 商品描述(可选)"""
    db = get_session()
    try:
        mgr = ProductManager()
        product_in = ProductCreate(
            name=name, code=code, category=category, price=price,
            unit=unit, cost_price=cost_price, description=description
        )
        product = mgr.create_product(db, product_in)
        return f"✅ 商品创建成功！\n商品ID: {product.id}\n商品名称: {product.name}\n商品编码: {product.code}\n分类: {product.category}\n单价: ¥{product.price:.2f}"
    except Exception as e:
        return f"❌ 创建商品失败: {str(e)}"
    finally:
        db.close()

@tool
def get_products(category: Optional[str] = None, keyword: Optional[str] = None,
                 limit: int = 20) -> str:
    """获取商品列表\n\n参数:\n- category: 商品分类(可选)\n- keyword: 搜索关键词(名称/编码, 可选)\n- limit: 返回数量限制, 默认20"""
    db = get_session()
    try:
        mgr = ProductManager()
        products = mgr.get_products(db, skip=0, limit=limit,
                                    category=category, keyword=keyword)

        if not products:
            return "暂无商品数据"

        result = "📋 商品列表:\n\n"
        for prod in products:
            result += f"【{prod.id}】{prod.name}\n"
            result += f"  编码: {prod.code}\n"
            result += f"  分类: {prod.category}\n"
            result += f"  单价: ¥{prod.price:.2f}\n"
            result += f"  单位: {prod.unit}\n"
            if prod.cost_price:
                result += f"  成本价: ¥{prod.cost_price:.2f}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"❌ 查询商品失败: {str(e)}"
    finally:
        db.close()

# ============ 库存管理工具 ============

@tool
def inventory_in(store_id: int, product_id: int, quantity: float,
                 operator_id: Optional[int] = None,
                 remark: Optional[str] = None) -> str:
    """库存入库\n\n参数:\n- store_id: 门店ID\n- product_id: 商品ID\n- quantity: 入库数量\n- operator_id: 操作人ID(可选)\n- remark: 备注(可选)"""
    db = get_session()
    try:
        mgr = InventoryManager()
        inventory = mgr.adjust_inventory(
            db, store_id, product_id, quantity, "purchase", operator_id, remark
        )
        return f"✅ 入库成功！\n门店ID: {store_id}\n商品ID: {product_id}\n入库数量: {quantity}\n当前库存: {inventory.quantity}"
    except Exception as e:
        return f"❌ 入库失败: {str(e)}"
    finally:
        db.close()

@tool
def get_inventory(store_id: int, low_stock_only: bool = False) -> str:
    """获取门店库存\n\n参数:\n- store_id: 门店ID\n- low_stock_only: 是否只显示库存预警商品, 默认false"""
    db = get_session()
    try:
        mgr = InventoryManager()
        inventories = mgr.get_inventories(db, skip=0, limit=100,
                                          store_id=store_id,
                                          low_stock_only=low_stock_only)

        if not inventories:
            return "暂无库存数据"

        result = f"📋 门店{store_id}库存列表:\n\n"
        for inv in inventories:
            result += f"商品ID: {inv.product_id}\n"
            result += f"  库存数量: {inv.quantity}\n"
            result += f"  预警阈值: {inv.warning_threshold}\n"
            if inv.quantity <= inv.warning_threshold:
                result += f"  ⚠️ 库存预警\n"
            result += "\n"
        return result
    except Exception as e:
        return f"❌ 查询库存失败: {str(e)}"
    finally:
        db.close()

# ============ 订单管理工具 ============

@tool
def create_order(store_id: int, items: str, payment_method: str,
                 member_id: Optional[int] = None,
                 remark: Optional[str] = None) -> str:
    """创建订单\n\n参数:\n- store_id: 门店ID\n- items: 商品明细, 格式: 商品ID,数量,单价;商品ID,数量,单价\n- payment_method: 支付方式(cash/wechat/alipay/card/member_balance)\n- member_id: 会员ID(可选)\n- remark: 备注(可选)\n\n示例:\nitems='1,2,50;2,1,30' 表示:\n  商品1数量2单价50元\n  商品2数量1单价30元"""
    db = get_session()
    try:
        mgr = OrderManager()

        # 解析商品明细
        order_items = []
        total_amount = 0.0
        for item_str in items.split(';'):
            if not item_str:
                continue
            parts = item_str.split(',')
            if len(parts) != 3:
                continue
            product_id, quantity, price = int(parts[0]), float(parts[1]), float(parts[2])
            order_items.append(OrderItemCreate(
                product_id=product_id,
                product_name=f"商品{product_id}",  # 实际应该从商品表获取
                quantity=quantity,
                unit_price=price,
                remark=None
            ))
            total_amount += quantity * price

        order_in = OrderCreate(
            store_id=store_id,
            member_id=member_id,
            items=order_items,
            payment_method=PaymentMethod(payment_method),
            remark=remark
        )
        order = mgr.create_order(db, order_in)
        return f"✅ 订单创建成功！\n订单号: {order.order_no}\n订单ID: {order.id}\n订单总额: ¥{order.total_amount:.2f}\n实付金额: ¥{order.paid_amount:.2f}\n状态: {order.status.value}"
    except Exception as e:
        return f"❌ 创建订单失败: {str(e)}"
    finally:
        db.close()

@tool
def pay_order(order_id: int, payment_method: str) -> str:
    """支付订单\n\n参数:\n- order_id: 订单ID\n- payment_method: 支付方式(cash/wechat/alipay/card/member_balance)"""
    db = get_session()
    try:
        mgr = OrderManager()
        order = mgr.pay_order(db, order_id, PaymentMethod(payment_method))
        return f"✅ 订单支付成功！\n订单号: {order.order_no}\n实付金额: ¥{order.paid_amount:.2f}\n支付方式: {order.payment_method.value}"
    except Exception as e:
        return f"❌ 支付订单失败: {str(e)}"
    finally:
        db.close()

@tool
def get_orders(store_id: Optional[int] = None, status: Optional[str] = None,
               limit: int = 20) -> str:
    """获取订单列表\n\n参数:\n- store_id: 门店ID(可选)\n- status: 订单状态(pending/paid/completed/cancelled/refunded, 可选)\n- limit: 返回数量限制, 默认20"""
    db = get_session()
    try:
        mgr = OrderManager()
        order_status = OrderStatus(status) if status else None
        orders = mgr.get_orders(db, skip=0, limit=limit,
                               store_id=store_id, status=order_status)

        if not orders:
            return "暂无订单数据"

        result = "📋 订单列表:\n\n"
        for order in orders:
            result += f"【{order.id}】订单号: {order.order_no}\n"
            result += f"  门店ID: {order.store_id}\n"
            if order.member_id is not None:
                result += f"  会员ID: {order.member_id}\n"
            result += f"  订单总额: ¥{order.total_amount:.2f}\n"
            result += f"  实付金额: ¥{order.paid_amount:.2f}\n"
            result += f"  支付方式: {order.payment_method.value}\n"
            result += f"  状态: {order.status.value}\n"
            result += f"  下单时间: {order.order_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"❌ 查询订单失败: {str(e)}"
    finally:
        db.close()

# ============ 财务报表工具 ============

@tool
def get_daily_report(store_id: Optional[int] = None, date: Optional[str] = None) -> str:
    """获取日报表\n\n参数:\n- store_id: 门店ID(可选, 不填则查询所有门店)\n- date: 日期(YYYY-MM-DD格式, 可选, 不填则查询今天)"""
    db = get_session()
    try:
        mgr = FinancialManager()
        from datetime import datetime
        target_date = datetime.strptime(date, "%Y-%m-%d") if date else None
        report = mgr.get_daily_summary(db, store_id, target_date)

        result = f"📊 {report['date']} 日报表\n"
        if store_id:
            result += f"门店ID: {store_id}\n"
        result += "\n"
        result += f"订单数量: {report['order_count']}\n"
        result += f"订单金额: ¥{report['order_amount']:.2f}\n"
        result += f"收入金额: ¥{report['income_amount']:.2f}\n"
        result += f"支出金额: ¥{report['expense_amount']:.2f}\n"
        result += f"退款金额: ¥{report['refund_amount']:.2f}\n"
        result += f"总营收: ¥{report['total_income']:.2f}\n"
        result += f"总支出: ¥{report['total_expense']:.2f}\n"
        result += f"净利润: ¥{report['net_profit']:.2f}\n"

        return result
    except Exception as e:
        return f"❌ 查询日报表失败: {str(e)}"
    finally:
        db.close()

@tool
def get_monthly_report(store_id: Optional[int] = None, year: Optional[int] = None,
                      month: Optional[int] = None) -> str:
    """获取月报表\n\n参数:\n- store_id: 门店ID(可选, 不填则查询所有门店)\n- year: 年份(可选, 不填则查询当前年)\n- month: 月份(可选, 不填则查询当前月)"""
    db = get_session()
    try:
        mgr = FinancialManager()
        report = mgr.get_monthly_summary(db, store_id, year, month)

        result = f"📊 {report['year']}年{report['month']}月 月报表\n"
        if store_id:
            result += f"门店ID: {store_id}\n"
        result += "\n"
        result += f"订单数量: {report['order_count']}\n"
        result += f"订单金额: ¥{report['order_amount']:.2f}\n"
        result += f"收入金额: ¥{report['income_amount']:.2f}\n"
        result += f"支出金额: ¥{report['expense_amount']:.2f}\n"
        result += f"退款金额: ¥{report['refund_amount']:.2f}\n"
        result += f"总营收: ¥{report['total_income']:.2f}\n"
        result += f"总支出: ¥{report['total_expense']:.2f}\n"
        result += f"净利润: ¥{report['net_profit']:.2f}\n"
        result += f"日均订单: {report['avg_daily_orders']:.2f}\n"
        result += f"日均收入: ¥{report['avg_daily_income']:.2f}\n"

        return result
    except Exception as e:
        return f"❌ 查询月报表失败: {str(e)}"
    finally:
        db.close()

@tool
def get_store_comparison() -> str:
    """获取门店对比数据"""
    db = get_session()
    try:
        mgr = FinancialManager()
        results = mgr.get_store_comparison(db)

        if not results:
            return "暂无门店对比数据"

        result = "📊 门店营业额对比:\n\n"
        for store in results:
            result += f"【{store['store_id']}】{store['store_name']}\n"
            result += f"  订单数量: {store['order_count']}\n"
            result += f"  营业额: ¥{store['order_amount']:.2f}\n"
            result += f"  平均客单价: ¥{store['avg_order_amount']:.2f}\n"
            result += "\n"
        return result
    except Exception as e:
        return f"❌ 查询门店对比失败: {str(e)}"
    finally:
        db.close()

# ============ 构建Agent ============

def build_agent(ctx=None):
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    # 所有工具列表
    tools = [
        # 门店管理
        create_store, get_stores, update_store,
        # 员工管理
        create_employee, get_employees,
        # 会员管理
        create_member, get_members, member_recharge,
        # 商品管理
        create_product, get_products,
        # 库存管理
        inventory_in, get_inventory,
        # 订单管理
        create_order, pay_order, get_orders,
        # 财务报表
        get_daily_report, get_monthly_report, get_store_comparison
    ]

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
