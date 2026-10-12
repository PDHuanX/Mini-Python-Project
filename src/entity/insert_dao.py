import dataclasses
import datetime

"""导入客户数据实体"""
@dataclasses.dataclass
class Customer:
    accounting_date: datetime.date
    salesman_company: str
    salesman_name: str
    receive_money: float
    company_name: str
    industry_type: str
    code: str
    contact: str
    contact_phone: str
    associated_person: str
    is_group: int
    steward_id: int
    steward_name: str
    lawers: list
    serve_id: int
    serve_name: str
    remark: str
    start_time: datetime.date
    end_time: datetime.date
    finance_audit: str
    quality_audit: str
    item_name: str
    is_item: str
    is_renewal: int
    performance_company: str
    audit_pass_time: datetime.datetime
    fill_time: datetime.datetime
    consultant_id: int
    consultant_name: str
