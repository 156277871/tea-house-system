from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from storage.database.shared.model import Employee, EmployeePosition


class EmployeeCreate(BaseModel):
    name: str = Field(..., description="员工姓名")
    phone: str = Field(..., description="联系电话")
    email: Optional[str] = Field(None, description="邮箱")
    position: EmployeePosition = Field(..., description="职位")
    store_id: int = Field(..., description="所属门店ID")
    hire_date: Optional[datetime] = Field(None, description="入职日期")


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[EmployeePosition] = None
    status: Optional[bool] = None


class EmployeeManager:
    """员工管理 Manager"""

    def create_employee(self, db: Session, employee_in: EmployeeCreate) -> Employee:
        """创建员工"""
        employee_data = employee_in.model_dump()
        db_employee = Employee(**employee_data)
        db.add(db_employee)
        try:
            db.commit()
            db.refresh(db_employee)
            return db_employee
        except Exception:
            db.rollback()
            raise

    def get_employees(self, db: Session, skip: int = 0, limit: int = 100,
                      store_id: Optional[int] = None,
                      position: Optional[EmployeePosition] = None,
                      status: Optional[bool] = None) -> List[Employee]:
        """获取员工列表"""
        query = db.query(Employee)
        if store_id:
            query = query.filter(Employee.store_id == store_id)
        if position:
            query = query.filter(Employee.position == position)
        if status is not None:
            query = query.filter(Employee.status == status)
        return query.order_by(Employee.id).offset(skip).limit(limit).all()

    def get_employee_by_id(self, db: Session, employee_id: int) -> Optional[Employee]:
        """根据ID获取员工"""
        return db.query(Employee).filter(Employee.id == employee_id).first()

    def get_employees_by_store(self, db: Session, store_id: int) -> List[Employee]:
        """获取指定门店的所有员工"""
        return db.query(Employee).filter(
            Employee.store_id == store_id,
            Employee.status == True
        ).all()

    def update_employee(self, db: Session, employee_id: int,
                       employee_in: EmployeeUpdate) -> Optional[Employee]:
        """更新员工信息"""
        db_employee = self.get_employee_by_id(db, employee_id)
        if not db_employee:
            return None
        update_data = employee_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_employee, field):
                setattr(db_employee, field, value)
        db.add(db_employee)
        try:
            db.commit()
            db.refresh(db_employee)
            return db_employee
        except Exception:
            db.rollback()
            raise

    def delete_employee(self, db: Session, employee_id: int) -> bool:
        """删除员工（软删除）"""
        db_employee = self.get_employee_by_id(db, employee_id)
        if not db_employee:
            return False
        db_employee.status = False
        db.add(db_employee)
        try:
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise

    def count_employees(self, db: Session, store_id: Optional[int] = None) -> int:
        """统计员工数量"""
        query = db.query(Employee).filter(Employee.status == True)
        if store_id:
            query = query.filter(Employee.store_id == store_id)
        return query.count()

    def get_store_managers(self, db: Session, store_id: int) -> List[Employee]:
        """获取门店店长"""
        return db.query(Employee).filter(
            Employee.store_id == store_id,
            Employee.position == EmployeePosition.MANAGER,
            Employee.status == True
        ).all()
