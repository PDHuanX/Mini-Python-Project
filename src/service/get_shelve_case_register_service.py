from src.utils.dict_result import DictResult
from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
import datetime
import src.utils.paths_utils as paths_utils
from openpyxl import Workbook
from dateutil.relativedelta import relativedelta

def public_get_shelve_case_register_service():
    return _get_shelve_case_register_service()

def _get_shelve_case_register_service():
    result = QueryMysqlDatabase().get_shelve_case_register()

    # 获取文件路径
    data_sir = paths_utils.get_resource_path('resources/public_excel')

    # 创建新表
    new_workbook = Workbook()
    # 获取表格
    new_sheet = new_workbook['Sheet']

    # 设置表头
    new_sheet.append([
        "客户名称", "服务顾问", "法律顾问", "服务事项", "服务类型"
        , "交付状态", "分公司", "合同开始时间", "合同结束时间", "搁置时间", "搁置理由"
    ])

    # 设置数据
    data_list = [
        (
            row['company_name'],
            row['serve_name'],
            row['law_name'],
            row['service_name'],
            row['item_name'],
            row['delivery_status'],
            row['salesman_company'],
            row['contract_start_date'],
            row['contract_end_date'],
            row['shelve_date'],
            row['shelve_reason'],
        ) for row in result
    ]

    # 循环新增
    for data in data_list:
        new_sheet.append(data)

    today = datetime.datetime.today()
    year_month = today - relativedelta(months=1)

    # 保存表格
    new_workbook.save(
        f'{data_sir}/{year_month.strftime("%Y%m")}底搁置事项数（依据立案模块搁置数据）.xlsx')

    return DictResult.success_response(status_code=200,
                                       message=f"获取成功，共{len(result)}条数据，请前往【resources/public_excel】文件夹查看",
                                       types="get_shelve_case_register_service", data=None)