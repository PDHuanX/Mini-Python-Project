import src.utils.paths_utils as paths_utils
import datetime
from openpyxl.reader.excel import load_workbook
from src.utils.dict_result import DictResult
from openpyxl import Workbook
from src.utils.sheet_column_index_utils import ColumnIndexTow

def public_get_law_out_date_data(data):
    return _get_law_out_date_data(data)

def _get_law_out_date_data(data):
    # 拆解需要的法律顾问
    law_string_list = data['lawStrOut'].split(',') if ',' in data['lawStrOut'] else data['lawStrOut'].split('，')

    # 时间，这里的时间是～的区间
    date_list = data['deadlineLawOut'].split('~') if '~' in data['deadlineLawOut'] else data['deadlineLawOut'].split('～')
    view_start_date = datetime.datetime.strptime(date_list[0], '%Y-%m-%d')
    view_end_date = datetime.datetime.strptime(date_list[1], '%Y-%m-%d')

    # 获取文件路径
    data_sir = paths_utils.get_resource_path('resources/excel_templates')

    # 获取表格
    workbook = load_workbook(f'{data_sir}/{data['sourceDataFileNameLawOut']}.xlsx')
    sheet = workbook['线下客户表']

    # 获取表格数据
    sheet_row_data_list = list(sheet.iter_rows(min_row=2, max_row=sheet.max_row))

    # 结果集
    result_list = {}
    # 获取需要的数据
    for law in law_string_list:
        for row in sheet_row_data_list:
            # 法律顾问
            law_name = row[ColumnIndexTow.LAWERS].value
            # 不获取空数据
            if law_name is None:
                continue

            # 获取 客户名称单元格的颜色，过滤掉不需要的
            fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
            # 如果不包含这些颜色的数据，跳过，不算户数
            if fg_color.rgb[2:] in ['C0C0C0', '666699', '9999FF']:
                continue

            # 合同结束时间
            end_time = row[ColumnIndexTow.END_TIME].value
            # 如果到期时间为空，说明不是会员或调解套餐
            if end_time is None or not end_time: continue

            # 结束时间在所给的时间区间内，并且是当前顾问的数据
            if view_start_date <= end_time <= view_end_date and law in law_name:
                # 如果不存在这个key，初始化
                if law not in result_list.keys():
                    result_list[law] = {'customers': [], 'count': 0}

                # id集，用于数据出错时溯源
                result_list[law]['customers'].append((
                    row[ColumnIndexTow.CUSTOMER_ID].value,
                    row[ColumnIndexTow.COMPANY_NAME].value,
                    row[ColumnIndexTow.START_TIME].value,
                    row[ColumnIndexTow.END_TIME].value,
                    row[ColumnIndexTow.MEMBER_TYPE].value,
                    row[ColumnIndexTow.SERVE_NAME].value,
                    row[ColumnIndexTow.LAWERS].value
                ))
                result_list[law]['count'] += 1

    # 创建新表
    new_workbook = Workbook()
    # 汇总表格
    new_sheet_one = new_workbook['Sheet']
    new_sheet_one.title = '汇总'
    # 设置表头
    new_sheet_one.append(['顾问名称', '过期户数'])
    data_list = [
        (key, val['count']) for key, val in result_list.items()
    ]
    # 设置数据
    for row in data_list:
        new_sheet_one.append(row)

    # 表头
    handers = ['客户id', '客户名称', '合同开始时间', '合同结束时间', '套餐类型', '服务顾问', '法律顾问']

    # 循环处理数据
    for key, val in result_list.items():
        # 根据顾问名称生成新子表
        new_sheet = new_workbook.create_sheet(key)
        # 设置表头
        new_sheet.append(handers)

        # 这个val本身也是dict类型，直接取customers即可
        for customer in val['customers']:
            new_sheet.append(customer)

    # 保存表格
    new_workbook.save(f'{paths_utils.get_resource_path('resources/law_out')}/{data['deadlineLawOut']}法律顾问过期户数.xlsx')

    return DictResult.success_response(
        message="获取成功，请前往【resources/law_out】文件夹查看",
        status_code=200,
        types="submit_get_law_out_date_data",
        data=None
    )