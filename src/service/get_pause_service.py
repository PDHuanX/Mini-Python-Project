from src.utils.dict_result import DictResult
from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
import datetime
import src.utils.paths_utils as paths_utils
from openpyxl import Workbook

def public_get_pause_service(view_data):
    return _get_pause_service(view_data)

def _get_pause_service(view_data):
    result = QueryMysqlDatabase().get_pause_service(view_data)

    # 获取文件路径
    data_sir = paths_utils.get_resource_path('resources/public_excel')

    # 创建新表
    new_workbook = Workbook()
    # 获取表格
    new_sheet = new_workbook['Sheet']

    # 设置表头
    new_sheet.append([
        "事项ID", "客户名称", "法律顾问", "事项名称", "事项类型"
        , "最新一次暂停时间", "暂停总次数", "审核通过次数", "审核不通过次数", "待审核"
    ])

    # 设置数据
    data_list = [
        (
            row['service_id'],
            row['company_name'],
            row['law_name'],
            row['service_name'],
            row['item_name'],
            row['new_pause_date'],
            row['pause_count'],
            row['pause_ok_count'],
            row['pause_not_count'],
            row['pause_wait_count']
        ) for row in result
    ]

    # 循环新增
    for data in data_list:
        new_sheet.append(data)

    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=int(view_data["pauseDate"]))

    # 保存表格
    new_workbook.save(
            f'{data_sir}/{yesterday.strftime("%Y%m%d")}暂停事项.xlsx')

    return DictResult.success_response(status_code=200,
                                       message=f"获取成功，共{len(result)}条数据，请前往【resources/public_excel】文件夹查看",
                                       types="get_pause_service", data=None)