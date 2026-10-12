import datetime
import src.utils.paths_utils as paths_utils
import pandas as pd
from openpyxl.reader.excel import load_workbook
from src.utils.dict_result import DictResult

'''对外接口'''
def public_get_salesman_company_during_data(data):
    return _get_salesman_company_during_data(data)

'''获取分公司在期客户数据'''
def _get_salesman_company_during_data(data):
    # 截止时间
    now_time = datetime.datetime.strptime(data['endTimeSal'], '%Y-%m-%d')
    if now_time is None:
        now_time = datetime.datetime.now()

    # 获取文件路径
    data_sir = paths_utils.get_resource_path('resources/excel_templates')

    # 先获取【我方收款公司】的数据有哪些，下面需要基于这个数据获取各分公司的在期客户
    pd_sheet = pd.read_excel(f'{data_sir}/{data['fileSource']}.xlsx', sheet_name='线下客户表')
    unique_values = pd_sheet['我方收款公司'].unique()
    _ = unique_values

    # 获取表格
    workbook = load_workbook(f'{data_sir}/{data['fileSource']}.xlsx')
    sheet = workbook['线下客户表']

    # 获取数据
    data_list = list(sheet.iter_rows(min_row=2, max_row=sheet.max_row))
    # 结果集
    result_list = []

    for row in data_list:
        # 获取 客户名称单元格的颜色，过滤掉不需要的
        fg_color = row[3].fill.fgColor
        if fg_color.rgb[2:] not in ['FFFFFF', 'FF0000', '00FF00', 'FF6600']:
            continue

        # 这里只获取会员的
        if '会员' not in row[7].value or '调解服务套餐' not in row[7].value:
            continue

        # 判断到期时间是不是大于当前时间或者所填的时间，小于则跳过
        if row[5].value <= now_time:
            continue

        result_list.append((
            row[0].value,
            row[3].value,
            row[4].value,
            row[5].value,
            row[6].value,
            row[7].value,
        ))

    return DictResult.success_response(
        message="该功能未完成，存在难题",
        status_code=500,
        types="submit_get_salesman_company_during_data",
        data=None
    )