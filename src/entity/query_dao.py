import dataclasses

@dataclasses.dataclass
class AwaitAuditPostpone:
    company_name: str
    service_name: str
    item_name: str
    first_time: str
    new_time: str
    delay_reason: str
    create_time: str
    delay_id: str
    service_id: str

@dataclasses.dataclass
class Contract:
    customerId: str
    yearStartTime: str
    nonStartTime: str
    yearEndTime: str
    nonEndTime: str
    itemMeal: str
    thaliId: str

@dataclasses.dataclass
class CounselorLog:
    counselor_log_id: str
    customer_id: str
    create_time: str

"""
客户表对象
"""
@dataclasses.dataclass
class Customer:
    customer_id: str
    company_name: str
    contact_phone: str
    room_id: str
    associated_person: str
    enterprise_name: str
    salesman_company: str
    steward_name: str
    steward_id: str
    serve_name: str
    lawers: str
    consultant_name: str
    performance_company: str
    code: str
    ok_num: int
    no_num: int
    payee_name: str
    industry_type: str
    contact: str
    receive_money: str

@dataclasses.dataclass
class SysUser:
    user_id: str
    user_name: str
    nick_name: str
    role_id: str

@dataclasses.dataclass
class ServiceRecord:
    service_id: str
    customer_id: str
    company_name: str
    service_name: str
    item_name: str
    serve_id: str
    lawers: str
    confirm_date: str

@dataclasses.dataclass
class SysDictData:
    dict_label: str
    dict_value: str