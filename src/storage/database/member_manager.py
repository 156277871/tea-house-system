from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from storage.database.shared.model import Member, MemberLevel


class MemberCreate(BaseModel):
    name: str = Field(..., description="会员姓名")
    phone: str = Field(..., description="手机号")
    email: Optional[str] = Field(None, description="邮箱")
    level: MemberLevel = Field(default=MemberLevel.NORMAL, description="会员等级")


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    level: Optional[MemberLevel] = None
    status: Optional[bool] = None


class MemberManager:
    """会员管理 Manager"""

    def __init__(self):
        self.member_no_prefix = "M"

    def _generate_member_no(self, db: Session) -> str:
        """生成会员编号"""
        today = datetime.now().strftime("%Y%m%d")
        # 查询今天已有的会员数量
        count = db.query(Member).filter(
            Member.member_no.like(f"{self.member_no_prefix}{today}%")
        ).count()
        return f"{self.member_no_prefix}{today}{count + 1:04d}"

    def create_member(self, db: Session, member_in: MemberCreate) -> Member:
        """创建会员"""
        member_data = member_in.model_dump()
        member_data['member_no'] = self._generate_member_no(db)
        member_data['points'] = 0
        member_data['balance'] = 0.0
        member_data['total_consumption'] = 0.0
        member_data['status'] = True

        db_member = Member(**member_data)
        db.add(db_member)
        try:
            db.commit()
            db.refresh(db_member)
            return db_member
        except Exception:
            db.rollback()
            raise

    def get_members(self, db: Session, skip: int = 0, limit: int = 100,
                    level: Optional[MemberLevel] = None,
                    status: Optional[bool] = None,
                    keyword: Optional[str] = None) -> List[Member]:
        """获取会员列表"""
        query = db.query(Member)
        if level:
            query = query.filter(Member.level == level)
        if status is not None:
            query = query.filter(Member.status == status)
        if keyword:
            query = query.filter(
                (Member.name.like(f"%{keyword}%")) |
                (Member.phone.like(f"%{keyword}%")) |
                (Member.member_no.like(f"%{keyword}%"))
            )
        return query.order_by(Member.id.desc()).offset(skip).limit(limit).all()

    def get_member_by_id(self, db: Session, member_id: int) -> Optional[Member]:
        """根据ID获取会员"""
        return db.query(Member).filter(Member.id == member_id).first()

    def get_member_by_phone(self, db: Session, phone: str) -> Optional[Member]:
        """根据手机号获取会员"""
        return db.query(Member).filter(Member.phone == phone).first()

    def get_member_by_no(self, db: Session, member_no: str) -> Optional[Member]:
        """根据会员编号获取会员"""
        return db.query(Member).filter(Member.member_no == member_no).first()

    def update_member(self, db: Session, member_id: int,
                     member_in: MemberUpdate) -> Optional[Member]:
        """更新会员信息"""
        db_member = self.get_member_by_id(db, member_id)
        if not db_member:
            return None
        update_data = member_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_member, field):
                setattr(db_member, field, value)
        db.add(db_member)
        try:
            db.commit()
            db.refresh(db_member)
            return db_member
        except Exception:
            db.rollback()
            raise

    def update_balance(self, db: Session, member_id: int, amount: float) -> Optional[Member]:
        """更新会员余额"""
        db_member = self.get_member_by_id(db, member_id)
        if not db_member:
            return None
        db_member.balance += amount
        if db_member.balance < 0:
            raise ValueError("余额不足")
        db.add(db_member)
        try:
            db.commit()
            db.refresh(db_member)
            return db_member
        except Exception:
            db.rollback()
            raise

    def update_points(self, db: Session, member_id: int, points: int) -> Optional[Member]:
        """更新会员积分"""
        db_member = self.get_member_by_id(db, member_id)
        if not db_member:
            return None
        db_member.points += points
        if db_member.points < 0:
            raise ValueError("积分不足")
        # 更新会员等级
        self._update_member_level(db_member)
        db.add(db_member)
        try:
            db.commit()
            db.refresh(db_member)
            return db_member
        except Exception:
            db.rollback()
            raise

    def _update_member_level(self, member: Member):
        """根据消费总额和积分更新会员等级"""
        if member.total_consumption >= 50000 or member.points >= 50000:
            member.level = MemberLevel.PLATINUM
        elif member.total_consumption >= 20000 or member.points >= 20000:
            member.level = MemberLevel.GOLD
        elif member.total_consumption >= 10000 or member.points >= 10000:
            member.level = MemberLevel.SILVER
        elif member.total_consumption >= 5000 or member.points >= 5000:
            member.level = MemberLevel.BRONZE
        else:
            member.level = MemberLevel.NORMAL

    def update_consumption(self, db: Session, member_id: int, amount: float) -> Optional[Member]:
        """更新会员累计消费"""
        db_member = self.get_member_by_id(db, member_id)
        if not db_member:
            return None
        db_member.total_consumption += amount
        db_member.last_visit_time = datetime.now()
        self._update_member_level(db_member)
        db.add(db_member)
        try:
            db.commit()
            db.refresh(db_member)
            return db_member
        except Exception:
            db.rollback()
            raise

    def delete_member(self, db: Session, member_id: int) -> bool:
        """删除会员（软删除）"""
        db_member = self.get_member_by_id(db, member_id)
        if not db_member:
            return False
        db_member.status = False
        db.add(db_member)
        try:
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise

    def count_members(self, db: Session, level: Optional[MemberLevel] = None) -> int:
        """统计会员数量"""
        query = db.query(Member).filter(Member.status == True)
        if level:
            query = query.filter(Member.level == level)
        return query.count()

    def get_top_members(self, db: Session, limit: int = 10) -> List[Member]:
        """获取消费排行前N的会员"""
        return db.query(Member).filter(
            Member.status == True
        ).order_by(Member.total_consumption.desc()).limit(limit).all()
