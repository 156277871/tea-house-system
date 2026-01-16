from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime

from storage.database.shared.model import FinancialRecord, Store, MemberTransaction, Member, Order


class FinancialRecordCreate(BaseModel):
    store_id: int = Field(..., description="门店ID")
    record_type: str = Field(..., description="记录类型: income/expense/refund")
    amount: float = Field(..., description="金额")
    description: str = Field(..., description="描述")
    reference_id: Optional[str] = Field(None, description="关联单号")
    category: Optional[str] = Field(None, description="分类")


class FinancialManager:
    """财务管理 Manager"""

    def create_financial_record(self, db: Session, record_in: FinancialRecordCreate) -> FinancialRecord:
        """创建财务记录"""
        record_data = record_in.model_dump()
        db_record = FinancialRecord(**record_data)
        db.add(db_record)
        try:
            db.commit()
            db.refresh(db_record)
            return db_record
        except Exception:
            db.rollback()
            raise

    def get_financial_records(self, db: Session, skip: int = 0, limit: int = 100,
                             store_id: Optional[int] = None,
                             record_type: Optional[str] = None,
                             category: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[FinancialRecord]:
        """获取财务记录列表"""
        query = db.query(FinancialRecord)
        if store_id:
            query = query.filter(FinancialRecord.store_id == store_id)
        if record_type:
            query = query.filter(FinancialRecord.record_type == record_type)
        if category:
            query = query.filter(FinancialRecord.category == category)
        if start_date:
            query = query.filter(FinancialRecord.created_at >= start_date)
        if end_date:
            query = query.filter(FinancialRecord.created_at <= end_date)
        return query.order_by(FinancialRecord.created_at.desc()).offset(skip).limit(limit).all()

    def get_daily_summary(self, db: Session, store_id: Optional[int] = None,
                         date: Optional[datetime] = None) -> dict:
        """获取日报表"""
        if not date:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        start_date = date
        end_date = date.replace(hour=23, minute=59, second=59)

        # 查询当日订单
        order_query = db.query(Order)
        if store_id:
            order_query = order_query.filter(Order.store_id == store_id)
        orders = order_query.filter(
            and_(
                Order.order_time >= start_date,
                Order.order_time <= end_date
            )
        ).all()

        # 查询当日财务记录（排除订单记录，避免重复）
        financial_query = db.query(FinancialRecord).filter(
            and_(
                FinancialRecord.created_at >= start_date,
                FinancialRecord.created_at <= end_date
            )
        )
        if store_id:
            financial_query = financial_query.filter(FinancialRecord.store_id == store_id)
        financial_records = financial_query.filter(
            FinancialRecord.category != "order"
        ).all()

        # 统计数据
        order_count = len(orders)
        order_amount = sum(order.paid_amount for order in orders if order.status in ["paid", "completed"])
        refund_amount = sum(order.paid_amount for order in orders if order.status == "cancelled")

        income_amount = sum(r.amount for r in financial_records if r.record_type == "income")
        expense_amount = sum(r.amount for r in financial_records if r.record_type == "expense")
        refund_financial = sum(r.amount for r in financial_records if r.record_type == "refund")

        total_income = order_amount + income_amount + refund_financial
        total_expense = expense_amount + refund_amount
        net_profit = total_income - total_expense

        return {
            "date": date.strftime("%Y-%m-%d"),
            "store_id": store_id,
            "order_count": order_count,
            "order_amount": order_amount,
            "income_amount": income_amount,
            "expense_amount": expense_amount,
            "refund_amount": refund_amount + refund_financial,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": net_profit
        }

    def get_monthly_summary(self, db: Session, store_id: Optional[int] = None,
                           year: Optional[int] = None,
                           month: Optional[int] = None) -> dict:
        """获取月报表"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - datetime.resolution
        else:
            end_date = datetime(year, month + 1, 1) - datetime.resolution

        # 查询当月订单
        order_query = db.query(Order)
        if store_id:
            order_query = order_query.filter(Order.store_id == store_id)
        orders = order_query.filter(
            and_(
                Order.order_time >= start_date,
                Order.order_time <= end_date
            )
        ).all()

        # 查询当月财务记录
        financial_query = db.query(FinancialRecord).filter(
            and_(
                FinancialRecord.created_at >= start_date,
                FinancialRecord.created_at <= end_date
            )
        )
        if store_id:
            financial_query = financial_query.filter(FinancialRecord.store_id == store_id)
        financial_records = financial_query.filter(
            FinancialRecord.category != "order"
        ).all()

        # 统计数据
        order_count = len(orders)
        order_amount = sum(order.paid_amount for order in orders if order.status in ["paid", "completed"])
        refund_amount = sum(order.paid_amount for order in orders if order.status == "cancelled")

        income_amount = sum(r.amount for r in financial_records if r.record_type == "income")
        expense_amount = sum(r.amount for r in financial_records if r.record_type == "expense")
        refund_financial = sum(r.amount for r in financial_records if r.record_type == "refund")

        total_income = order_amount + income_amount + refund_financial
        total_expense = expense_amount + refund_amount
        net_profit = total_income - total_expense

        # 计算日均数据
        days_in_month = (end_date - start_date).days + 1
        avg_daily_orders = order_count / days_in_month if days_in_month > 0 else 0
        avg_daily_income = total_income / days_in_month if days_in_month > 0 else 0

        return {
            "year": year,
            "month": month,
            "store_id": store_id,
            "order_count": order_count,
            "order_amount": order_amount,
            "income_amount": income_amount,
            "expense_amount": expense_amount,
            "refund_amount": refund_amount + refund_financial,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": net_profit,
            "avg_daily_orders": round(avg_daily_orders, 2),
            "avg_daily_income": round(avg_daily_income, 2)
        }

    def get_store_comparison(self, db: Session, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List[dict]:
        """获取门店对比数据"""
        stores = db.query(Store).filter(Store.status == "active").all()

        results = []
        for store in stores:
            # 查询门店订单
            order_query = db.query(Order).filter(Order.store_id == store.id)
            if start_date:
                order_query = order_query.filter(Order.order_time >= start_date)
            if end_date:
                order_query = order_query.filter(Order.order_time <= end_date)
            orders = order_query.all()

            order_count = len(orders)
            order_amount = sum(order.paid_amount for order in orders if order.status in ["paid", "completed"])

            results.append({
                "store_id": store.id,
                "store_name": store.name,
                "order_count": order_count,
                "order_amount": order_amount,
                "avg_order_amount": order_amount / order_count if order_count > 0 else 0
            })

        # 按营业额排序
        results.sort(key=lambda x: x["order_amount"], reverse=True)
        return results

    def get_member_statistics(self, db: Session, store_id: Optional[int] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> dict:
        """获取会员统计"""
        query = db.query(Member)
        if store_id:
            # 查询在该门店消费过的会员
            member_ids = db.query(Order.member_id).filter(
                Order.store_id == store_id
            ).distinct().all()
            member_ids = [m[0] for m in member_ids if m[0]]
            query = query.filter(Member.id.in_(member_ids))

        members = query.all()

        total_members = len(members)
        total_balance = sum(m.balance for m in members)
        total_points = sum(m.points for m in members)
        total_consumption = sum(m.total_consumption for m in members)

        # 统计活跃会员（近期消费过的）
        active_days = 30
        active_date = datetime.now() - datetime.timedelta(days=active_days)
        active_members = sum(1 for m in members if m.last_visit_time and m.last_visit_time >= active_date)

        # 按等级统计
        level_stats = {}
        for m in members:
            level = m.level.value
            if level not in level_stats:
                level_stats[level] = 0
            level_stats[level] += 1

        return {
            "total_members": total_members,
            "active_members": active_members,
            "total_balance": total_balance,
            "total_points": total_points,
            "total_consumption": total_consumption,
            "average_consumption": total_consumption / total_members if total_members > 0 else 0,
            "level_distribution": level_stats
        }

    def get_revenue_trend(self, db: Session, store_id: Optional[int] = None,
                         days: int = 30) -> List[dict]:
        """获取收入趋势"""
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = end_date - datetime.timedelta(days=days-1)
        start_date = start_date.replace(hour=0, minute=0, second=0)

        results = []
        current_date = start_date

        while current_date <= end_date:
            day_end = current_date.replace(hour=23, minute=59, second=59)

            # 查询当天订单
            order_query = db.query(Order).filter(
                and_(
                    Order.order_time >= current_date,
                    Order.order_time <= day_end
                )
            )
            if store_id:
                order_query = order_query.filter(Order.store_id == store_id)
            orders = order_query.all()

            order_amount = sum(order.paid_amount for order in orders if order.status in ["paid", "completed"])
            order_count = len(orders)

            results.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "amount": order_amount,
                "count": order_count
            })

            current_date += datetime.timedelta(days=1)

        return results
