from src.utils.dict_result import DictResult
from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
import datetime
import src.utils.paths_utils as paths_utils
from openpyxl import Workbook

def public_get_warning_service():
    return _get_warning_service()

def _get_warning_service():
    result = QueryMysqlDatabase().get_warning_service()

    # 获取文件路径
    data_sir = paths_utils.get_resource_path('resources/public_excel')

    # 创建新表
    new_workbook = Workbook()
    # 获取表格
    new_sheet = new_workbook['Sheet']

    # 设置表头
    new_sheet.append([
        "事项ID", "客户名称", "服务名称", "服务类型", "计划完成时间", "法律顾问"
    ])

    # 设置数据
    data_list = [
        (
            row['service_id'],
            row['company_name'],
            row['service_name'],
            row['item_name'],
            row['plan_time'],
            row['law_name']
        ) for row in result
    ]

    # 循环新增
    for data in data_list:
        new_sheet.append(data)

    # 保存表格
    new_workbook.save(
        f'{data_sir}/{datetime.datetime.today().strftime("%Y%m%d")}预警事项.xlsx')

    return DictResult.success_response(status_code=200,
                                       message=f"获取成功，共{len(result)}条数据，请前往【resources/public_excel】文件夹查看",
                                       types="get_warning_service", data=None)