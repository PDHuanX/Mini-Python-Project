import json
import requests
import src.utils.paths_utils as paths_utils
from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
from src.utils.dict_result import DictResult
from openpyxl import Workbook

def public_get_delivery_url_data(view_data):
    # 项目登陆api，主要为了获取token，保证文件能正常访问
    java_login_url = "https://fawu.gxfywzx.com/prod-api/admin/login"
    credentials = {
        "username": "",
        "password": ""
    }
    response = requests.post(java_login_url, json=credentials)
    token = "Bearer" + response.json().get("token")

    view_data['authorization'] = token

    return _get_delivery_url_data(view_data)

def _get_delivery_url_data(view_data):
    # 需要获取的法律顾问名单
    delivery_law = view_data['deliveryLaw'].split(',')
    # 交付时间区间
    delivery_time_section = view_data['deliveryTimeSection'].split('~')
    # 需要获取的交付类型
    delivery_type = view_data['deliveryType']
    # authorization
    authorization = view_data['authorization']
    # 选择级别
    level = view_data['level']

    # 获取指定法律顾问在指定时间区间内交付的文件URL
    delivery_result = QueryMysqlDatabase().get_law_delivery_list(delivery_law,
                                                                 delivery_type,
                                                                 delivery_time_section[0],
                                                                 delivery_time_section[1],
                                                                 level
                                                                 )
    # 处理基础数据
    delivery_urls_result = []
    for row in delivery_result:
        row_json = {
            'service_id': row['service_id'],
            'customer_id': row['customer_id'],
            'company_name': row['company_name'],
            'service_name': row['service_name'],
            'delivery_time': row['delivery_time'],
            'lawers': row['lawers']
        }

        # 获取文件集合
        delivery_files = json.loads(row['file_url'])
        for index, delivery_file in enumerate(delivery_files):
            row_json.update({
                f'file{index + 1}':
                    "https://fawu.gxfywzx.com/prod-api" +
                    delivery_file['fileUrl'] +
                    "?Authorization=" +
                    authorization,
                f'fileName{index + 1}': delivery_file['fileName']
            })
        # 最终集合
        delivery_urls_result.append(row_json)

    # 获取文件路径
    data_sir = paths_utils.get_resource_path('resources/public_excel')

    # 创建新表
    new_workbook = Workbook()
    # 获取表格
    new_sheet = new_workbook['Sheet']
    # 设置表头
    new_sheet.append([
        '用户ID', '事项ID', '交付时间', '客户名称', '事项名称', '法律顾问',
        '文件1', '文件名1',
        '文件2', '文件名2',
        '文件3', '文件名3',
        '文件4', '文件名4',
        '文件5', '文件名5'
    ])

    # 设置数据
    data_list = [
        (
            row['customer_id'],
            row['service_id'],
            row['delivery_time'],
            row['company_name'],
            row['service_name'],
            row['lawers'],
            # 文件不一定都有，所以要判断
            row['file1'] if 'file1' in row else '',
            row['fileName1'] if 'fileName1' in row else '',
            row['file2'] if 'file2' in row else '',
            row['fileName2'] if 'fileName2' in row else '',
            row['file3'] if 'file3' in row else '',
            row['fileName3'] if 'fileName3' in row else '',
            row['file4'] if 'file4' in row else '',
            row['fileName4'] if 'fileName4' in row else '',
            row['file5'] if 'file5' in row else '',
            row['fileName5'] if 'fileName5' in row else ''
        ) for row in delivery_urls_result
    ]
    # 循环新增
    for data in data_list:
        new_sheet.append(data)

    # 保存表格
    new_workbook.save(
        f'{data_sir}/{view_data['deliveryTimeSection']}交付数据及文件路径.xlsx')

    return DictResult.success_response(
        message=f"获取成功，共{len(delivery_urls_result)}条数据，请前往【resources/public_excel】文件夹查看",
        status_code=200,
        types="submit_get_delivery_url_data",
        data=None
    )
