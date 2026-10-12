import datetime
import src.utils.paths_utils as paths_utils
from openpyxl.reader.excel import load_workbook
from openpyxl import Workbook
from src.utils.dict_result import DictResult
from src.utils.sheet_column_index_utils import ColumnIndexTow

"""对外接口"""
def public_get_steward_server_during_data_to_excel(data):
    # 获取数据源文件
    data_sir = paths_utils.get_resource_path(f"resources/excel_templates/{data['sourceDataFileName']}.xlsx")

    # 读取这份源文件
    workbook = load_workbook(data_sir)
    # 这份源文件的第一个字表是目标数据表
    sheet = workbook['线下客户表']
    # 获取表格数据
    sheet_data_list = list(sheet.iter_rows(min_row=2, max_row=sheet.max_row))

    # 当前日期
    now_date = datetime.datetime.strptime(str(data['stewardEndTime']), '%Y-%m-%d')
    # 获取管家数据
    steward_result_list = _get_steward_during_data(data, now_date, sheet_data_list)
    # 获取服务顾问数据
    server_result_list = _get_server_during_data(data, now_date, sheet_data_list)

    # 获取数据后，创建新表
    new_workbook = Workbook()
    # 删除第一个空表
    del new_workbook['Sheet']
    # 新建两个目标表
    new_sheet_one = new_workbook.create_sheet(f"{now_date.strftime('%Y%m')}客服")
    new_sheet_tow = new_workbook.create_sheet(f"{now_date.strftime('%Y%m')}服务")

    # 创建表头
    headers = ['客户ID', '客户名称', '合同开始时间', '合同结束时间', '加选最长到期时间', '合同类型', '签约公司', '客服管家',
               '服务顾问', '业务员', '合作金额']
    new_sheet_one.append(headers)
    new_sheet_tow.append(headers)

    # 设置管家数据
    for row in steward_result_list:
        new_sheet_one.append(row)

    # 设置服务数据
    for row in server_result_list:
        new_sheet_tow.append(row)

    # 保存数据
    out_url = paths_utils.get_resource_path("resources/get_steward_server_excel")
    new_workbook.save(f"{out_url}/{now_date.strftime('%Y%m')}月初分公司客户数据总表.xlsx")

    return DictResult.success_response(
        message="已获取完毕，请前往【resources/get_steward_server_excel】文件夹下查看",
        status_code=200,
        types="get_steward_server_during_data_to_excel",
        data=None
    )

"""获取服务的在期数据"""
def _get_server_during_data(data, now_date, sheet_data_list):
    # 拆分获取需要的管家名字
    server_list = data['stewardOrServerStr'].split(",") if "," in data['stewardOrServerStr'] else data['stewardOrServerStr'].split("，")

    # 循环获取对应数据，同时判断获取的数据是否还在合同其内
    result_list = []
    for server in server_list:
        for row in sheet_data_list:
            # 获取 客户名称单元格的颜色，过滤掉不需要的
            fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
            # 如果是这些颜色的数据，跳过，这些数据不算户数
            if fg_color.rgb[2:] in ['FFFF00', '9999FF', 'C0C0C0', '666699']:
                continue

            # 服务
            server_name = row[ColumnIndexTow.SERVE_NAME].value
            # 为空跳过
            if server_name is None or server_name == "缺失":
                continue

            # 这里这么处理主要是暂时兼容同名同姓的，不是最终版本
            check_server_name = server_name == '服务顾问黄莹' if server == '黄莹' else server_name == '服务顾问黄莹1' if server == '黄莹1' else server in server_name

            # 合同结束时间
            end_time = row[ColumnIndexTow.END_TIME].value
            # 加选时间
            add_end_time = row[ColumnIndexTow.ADD_END_TIME].value
            # 套餐类型
            criterion_type = row[ColumnIndexTow.MEMBER_TYPE].value
            # 判断当前日期是否小于合同结束时间
            check_time_bol = now_date < end_time if '会员' in criterion_type or '调解服务套餐' in criterion_type else now_date < add_end_time

            # 然后判断是不是这个管家的数据
            if check_server_name and check_time_bol:
                result_list.append(
                    [
                        row[ColumnIndexTow.CUSTOMER_ID].value,
                        row[ColumnIndexTow.COMPANY_NAME].value,
                        row[ColumnIndexTow.START_TIME].value,
                        end_time,
                        add_end_time,
                        criterion_type,
                        row[ColumnIndexTow.SALESMAN_COMPANY].value,
                        row[ColumnIndexTow.STEWARD_NAME].value,
                        server_name,
                        row[ColumnIndexTow.SALESMAN_NAME].value,
                        row[ColumnIndexTow.RECEIVE_MONEY].value
                    ]
                )

    # 返回最终数据
    return result_list

"""获取管家的在期数据"""
def _get_steward_during_data(data, now_date, sheet_data_list):
    # 拆分获取需要的管家名字
    steward_list = data['stewardOrServerStr'].split(",") if "," in data['stewardOrServerStr'] else data['stewardOrServerStr'].split("，")

    # 循环获取对应数据，同时判断获取的数据是否还在合同其内
    result_list = []
    for steward in steward_list:
        for row in sheet_data_list:
            # 获取 客户名称单元格的颜色，过滤掉不需要的
            fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
            # 如果是这些颜色的数据，跳过，这些数据不算户数
            if fg_color.rgb[2:] in ['FFFF00', '9999FF', 'C0C0C0', '666699']:
                continue

            # 管家
            steward_name = row[ColumnIndexTow.STEWARD_NAME].value
            # 为空跳过
            if steward_name is None or steward_name == '缺失':
                continue

            # 这里这么处理主要是暂时兼容同名同姓的，不是最终版本
            check_steward_name = steward_name == '客服管家黄莹' if steward == '黄莹' else steward_name == '客服管家黄莹1' if steward == '黄莹1' else steward in steward_name

            # 合同结束时间
            end_time = row[ColumnIndexTow.END_TIME].value
            # 加选时间
            add_end_time = row[ColumnIndexTow.ADD_END_TIME].value
            # 套餐类型
            criterion_type = row[ColumnIndexTow.MEMBER_TYPE].value
            # 判断当前日期是否小于合同结束时间
            check_time_bol = now_date < end_time if '会员' in criterion_type or '调解服务套餐' in criterion_type else now_date < add_end_time

            # 然后判断是不是这个管家的数据
            if check_steward_name and check_time_bol:
                result_list.append(
                    [
                        row[ColumnIndexTow.CUSTOMER_ID].value,
                        row[ColumnIndexTow.COMPANY_NAME].value,
                        row[ColumnIndexTow.START_TIME].value,
                        end_time,
                        add_end_time,
                        criterion_type,
                        row[ColumnIndexTow.SALESMAN_COMPANY].value,
                        steward_name,
                        row[ColumnIndexTow.SERVE_NAME].value,
                        row[ColumnIndexTow.SALESMAN_NAME].value,
                        row[ColumnIndexTow.RECEIVE_MONEY].value
                    ]
                )

    # 返回最终数据
    return result_list