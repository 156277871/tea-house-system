"""初始化示例数据"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import (
    Base, Store, StoreStatus, Employee, EmployeePosition,
    Member, MemberLevel, Product, Inventory, InventoryLog,
    InventoryLogType, Table, TableStatus, Session, SessionStatus,
    SessionItem, Order, OrderStatus, PaymentMethod, OrderItem
)

# 数据库配置 - 使用绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'tea_house.db')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_sample_data():
    """初始化示例数据"""
    db = SessionLocal()
    
    try:
        print("开始初始化示例数据...")
        
        # 1. 创建门店（6家）
        print("创建门店...")
        store_data = [
            {"name": "茶楼总店", "code": "ST001", "address": "市中心商业街1号", "phone": "010-88888888"},
            {"name": "茶楼东城店", "code": "ST002", "address": "东城区朝阳路88号", "phone": "010-66666666"},
            {"name": "茶楼西城店", "code": "ST003", "address": "西城区复兴路123号", "phone": "010-77777777"},
            {"name": "茶楼南山店", "code": "ST004", "address": "南山区科技大道66号", "phone": "0755-99999999"},
            {"name": "茶楼北湖店", "code": "ST005", "address": "北湖区环湖路88号", "phone": "027-55555555"},
            {"name": "茶楼新城店", "code": "ST006", "address": "新城开发区金桥路66号", "phone": "020-44444444"},
        ]
        
        stores = []
        for data in store_data:
            # 检查是否已存在
            existing = db.query(Store).filter(Store.code == data["code"]).first()
            if not existing:
                store = Store(
                    name=data["name"],
                    code=data["code"],
                    address=data["address"],
                    phone=data["phone"],
                    status=StoreStatus.ACTIVE
                )
                db.add(store)
                db.flush()
                stores.append(store)
            else:
                stores.append(existing)
        
        db.commit()
        print(f"已创建/获取 {len(stores)} 家门店")
        
        # 2. 创建员工
        print("创建员工...")
        employee_data = [
            {"name": "张经理", "phone": "13800138001", "position": EmployeePosition.MANAGER, "store_id": stores[0].id},
            {"name": "李店长", "phone": "13800138002", "position": EmployeePosition.MANAGER, "store_id": stores[1].id},
            {"name": "王员工", "phone": "13800138003", "position": EmployeePosition.STAFF, "store_id": stores[0].id},
            {"name": "赵员工", "phone": "13800138004", "position": EmployeePosition.STAFF, "store_id": stores[1].id},
            {"name": "孙员工", "phone": "13800138005", "position": EmployeePosition.STAFF, "store_id": stores[2].id},
            {"name": "周员工", "phone": "13800138006", "position": EmployeePosition.CASHIER, "store_id": stores[0].id},
            {"name": "吴店长", "phone": "13800138007", "position": EmployeePosition.MANAGER, "store_id": stores[3].id},
            {"name": "郑员工", "phone": "13800138008", "position": EmployeePosition.STAFF, "store_id": stores[4].id},
        ]
        
        for data in employee_data:
            existing = db.query(Employee).filter(Employee.phone == data["phone"]).first()
            if not existing:
                employee = Employee(**data)
                db.add(employee)
        
        db.commit()
        print("已创建员工数据")
        
        # 3. 创建商品
        print("创建商品...")
        product_data = [
            {"name": "龙井绿茶", "code": "P001", "category": "茶叶", "unit_price": 68.00, "unit": "壶"},
            {"name": "普洱熟茶", "code": "P002", "category": "茶叶", "unit_price": 88.00, "unit": "壶"},
            {"name": "铁观音", "code": "P003", "category": "茶叶", "unit_price": 78.00, "unit": "壶"},
            {"name": "大红袍", "code": "P004", "category": "茶叶", "unit_price": 128.00, "unit": "壶"},
            {"name": "茉莉花茶", "code": "P005", "category": "茶叶", "unit_price": 58.00, "unit": "壶"},
            {"name": "菊花茶", "code": "P006", "category": "花茶", "unit_price": 48.00, "unit": "杯"},
            {"name": "玫瑰花茶", "code": "P007", "category": "花茶", "unit_price": 58.00, "unit": "杯"},
            {"name": "柠檬茶", "code": "P008", "category": "花茶", "unit_price": 38.00, "unit": "杯"},
            {"name": "瓜子", "code": "S001", "category": "零食", "unit_price": 18.00, "unit": "份"},
            {"name": "花生", "code": "S002", "category": "零食", "unit_price": 18.00, "unit": "份"},
            {"name": "开心果", "code": "S003", "category": "零食", "unit_price": 38.00, "unit": "份"},
            {"name": "腰果", "code": "S004", "category": "零食", "unit_price": 32.00, "unit": "份"},
            {"name": "话梅", "code": "S005", "category": "零食", "unit_price": 15.00, "unit": "份"},
            {"name": "薯片", "code": "S006", "category": "零食", "unit_price": 12.00, "unit": "份"},
            {"name": "水煮鱼", "code": "D001", "category": "菜品", "unit_price": 88.00, "unit": "份"},
            {"name": "宫保鸡丁", "code": "D002", "category": "菜品", "unit_price": 58.00, "unit": "份"},
            {"name": "麻婆豆腐", "code": "D003", "category": "菜品", "unit_price": 38.00, "unit": "份"},
            {"name": "鱼香肉丝", "code": "D004", "category": "菜品", "unit_price": 48.00, "unit": "份"},
        ]
        
        products = []
        for data in product_data:
            existing = db.query(Product).filter(Product.code == data["code"]).first()
            if not existing:
                product = Product(**data)
                db.add(product)
                db.flush()
                products.append(product)
            else:
                products.append(existing)
        
        db.commit()
        print(f"已创建 {len(products)} 种商品")
        
        # 4. 创建桌台
        print("创建桌台...")
        for i, store in enumerate(stores):
            for j in range(8):  # 每个店8个桌台
                existing = db.query(Table).filter(
                    Table.code == f"T{i+1:02d}{j+1:02d}"
                ).first()
                if not existing:
                    table = Table(
                        name=f"{store.name}桌台{j+1}号",
                        code=f"T{i+1:02d}{j+1:02d}",
                        store_id=store.id,
                        capacity=[2, 4, 6, 8][j % 4],
                        status=TableStatus.FREE
                    )
                    db.add(table)
        
        db.commit()
        print("已创建桌台数据")
        
        # 5. 创建库存和库存流水
        print("创建库存和库存流水...")
        inventory_logs = []
        for store in stores:
            for i, product in enumerate(products):
                # 随机生成初始库存
                quantity = 20 + (i * 5) % 80  # 20-95之间
                
                # 检查是否已存在
                existing = db.query(Inventory).filter(
                    Inventory.store_id == store.id,
                    Inventory.product_id == product.id
                ).first()
                
                if not existing:
                    inv = Inventory(
                        store_id=store.id,
                        product_id=product.id,
                        quantity=quantity
                    )
                    db.add(inv)
                    db.flush()
                    
                    # 创建入库流水
                    log = InventoryLog(
                        store_id=store.id,
                        product_id=product.id,
                        log_type=InventoryLogType.IN,
                        quantity=quantity,
                        before_quantity=0,
                        after_quantity=quantity,
                        remark=f"初始入库 {quantity} 件"
                    )
                    db.add(log)
                    
                    # 模拟一些流水记录
                    if i < 5:  # 为前5个商品模拟流水
                        for k in range(3):  # 3条流水
                            days_ago = (k + 1) * 5 + i
                            change = -5 if k % 2 == 0 else 10
                            before = quantity + change
                            after = quantity
                            
                            log = InventoryLog(
                                store_id=store.id,
                                product_id=product.id,
                                log_type=InventoryLogType.OUT if change < 0 else InventoryLogType.IN,
                                quantity=change,
                                before_quantity=before,
                                after_quantity=after,
                                remark="模拟出库" if change < 0 else "模拟入库",
                                created_at=datetime.now() - timedelta(days=days_ago)
                            )
                            db.add(log)
        
        db.commit()
        print("已创建库存和库存流水")
        
        # 6. 创建会员
        print("创建会员...")
        member_data = [
            {"name": "王先生", "phone": "13900139001", "level": MemberLevel.GOLD, "balance": 500.00},
            {"name": "李女士", "phone": "13900139002", "level": MemberLevel.DIAMOND, "balance": 1000.00},
            {"name": "张先生", "phone": "13900139003", "level": MemberLevel.SILVER, "balance": 300.00},
            {"name": "赵女士", "phone": "13900139004", "level": MemberLevel.NORMAL, "balance": 100.00},
            {"name": "陈先生", "phone": "13900139005", "level": MemberLevel.GOLD, "balance": 800.00},
            {"name": "刘女士", "phone": "13900139006", "level": MemberLevel.SILVER, "balance": 250.00},
            {"name": "黄先生", "phone": "13900139007", "level": MemberLevel.NORMAL, "balance": 0.00},
            {"name": "周女士", "phone": "13900139008", "level": MemberLevel.DIAMOND, "balance": 2000.00},
        ]
        
        members = []
        for data in member_data:
            existing = db.query(Member).filter(Member.phone == data["phone"]).first()
            if not existing:
                member = Member(**data)
                db.add(member)
                db.flush()
                members.append(member)
            else:
                members.append(existing)
        
        db.commit()
        print(f"已创建 {len(members)} 名会员")
        
        # 7. 创建订单和会话
        print("创建订单和会话...")
        orders = []
        for i in range(20):  # 生成20条订单
            store = stores[i % len(stores)]
            member = members[i % len(members)]
            
            # 创建订单
            order_no = f"ORD{datetime.now() - timedelta(days=i):%Y%m%d%H%M%S}{i:02d}"
            order = Order(
                order_no=order_no,
                store_id=store.id,
                member_id=member.id,
                total_amount=150.0 + (i * 10),
                payment_method=[PaymentMethod.WECHAT, PaymentMethod.ALIPAY, PaymentMethod.CASH][i % 3],
                status=OrderStatus.COMPLETED,
                created_at=datetime.now() - timedelta(days=i)
            )
            db.add(order)
            db.flush()
            
            # 创建订单明细
            for j in range(3):
                product = products[(i + j) % len(products)]
                quantity = 1 + j % 2
                subtotal = product.unit_price * quantity
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.unit_price,
                    subtotal=subtotal
                )
                db.add(order_item)
            
            orders.append(order)
        
        db.commit()
        print(f"已创建 {len(orders)} 条订单")
        
        # 8. 创建会话
        print("创建会话...")
        tables = db.query(Table).all()
        for i in range(10):
            table = tables[i % len(tables)]
            store = db.query(Store).get(table.store_id)
            member = members[i % len(members)]
            
            # 创建已完成的会话
            duration = 60 + i * 15
            start_time = datetime.now() - timedelta(days=i, hours=duration // 60)
            end_time = start_time + timedelta(minutes=duration)
            
            session = Session(
                table_id=table.id,
                store_id=store.id,
                member_id=member.id,
                start_time=start_time,
                end_time=end_time,
                status=SessionStatus.COMPLETED,
                duration_minutes=duration,
                total_amount=100.0 + i * 20
            )
            db.add(session)
            db.flush()
            
            # 创建会话明细
            for j in range(2):
                product = products[(i + j) % len(products)]
                quantity = 1
                subtotal = product.unit_price * quantity
                
                session_item = SessionItem(
                    session_id=session.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.unit_price,
                    subtotal=subtotal,
                    order_time=start_time + timedelta(minutes=j * 10)
                )
                db.add(session_item)
        
        db.commit()
        print("已创建会话数据")
        
        print("\n✅ 示例数据初始化完成！")
        print(f"门店数: {len(stores)}")
        print(f"商品数: {len(products)}")
        print(f"会员数: {len(members)}")
        print(f"订单数: {len(orders)}")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_sample_data()
