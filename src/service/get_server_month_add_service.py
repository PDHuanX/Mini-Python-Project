from src.utils.dict_result import DictResult
from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
import src.utils.paths_utils as paths_utils
from openpyxl import Workbook

def public_get_server_month_add_service(view_data):
    return _get_server_month_add_service(view_data)

def _get_server_month_add_service(view_data):
    result = QueryMysqlDatabase().get_server_month_add_service(view_data)

    # 获取文件路径
    data_sir = paths_utils.get_resource_path('resources/public_excel')

    # 创建新表
    new_workbook = Workbook()
    # 获取表格
    new_sheet = new_workbook['Sheet']

    # 设置表头
    new_sheet.append([
        "事项名称", "事项类别", "审核通过时间", "审核人", "服务顾问"
    ])

    # 设置数据
    data_list = [
        (
            row['service_name'],
            row['item_name'],
            row['create_time'],
            row['create_by'],
            row['nick_name'],
        ) for row in result
    ]

    # 循环新增
    for data in data_list:
        new_sheet.append(data)

    # 保存表格
    new_workbook.save(
        f'{data_sir}/{view_data["monthRange"]}服务顾问新增事项.xlsx')

    return DictResult.success_response(status_code=200,
                                       message=f"获取成功，共{len(result)}条数据，请前往【resources/public_excel】文件夹查看",
                                       types="get_server_month_add_service", data=None)