import datetime
import src.utils.paths_utils as paths_utils
from openpyxl.reader.excel import load_workbook
from openpyxl import Workbook
from src.utils.dict_result import DictResult
from src.utils.sheet_column_index_utils import ColumnIndexTow
from datetime import datetime

"""对外接口"""
def public_get_steward_server_during_data_to_excel_new(data):
    # 获取数据源文件
    data_sir = paths_utils.get_resource_path(f"resources/excel_templates/{data['sourceDataFileName']}.xlsx")

    # 读取这份源文件
    workbook = load_workbook(data_sir)
    # 这份源文件的第一个字表是目标数据表
    sheet = workbook['线下客户表']
    # 获取表格数据
    sheet_data_list = list(sheet.iter_rows(min_row=2, max_row=sheet.max_row))

    # 指定日期
    now_date = datetime.strptime(str(data['stewardEndTime']), '%Y-%m-%d')

    # 周区间
    interval_end_str = data['stewardIntervalEndTimeNew']

    # 拆分获取需要的管家名字
    steward_list = data['stewardOrServerStr'].split(",") if "," in data['stewardOrServerStr'] else data['stewardOrServerStr'].split("，")

    # 获取管家在期客户数（会员 + 调解 + 杂项）
    steward_result_json = _get_steward_serve_result_json(steward_list, now_date, sheet_data_list, True)

    # 获取管家服务岗在期客户数（会员 + 调解 + 杂项）
    serve_result_json = _get_steward_serve_result_json(steward_list, now_date, sheet_data_list, False)

    # 获取管家指定区间新增客户数据（会员 + 调解）
    steward_add_result_json = _get_steward_server_add_result_json(steward_list, interval_end_str, sheet_data_list, True)

    # 获取管家服务岗新增客户数据（会员 + 调解）
    serve_add_result_json = _get_steward_server_add_result_json(steward_list, interval_end_str, sheet_data_list, False)

    # 获取管家指定区间到期客户数（会员 + 调解）
    steward_out_result_json = _get_steward_server_out_result_json(steward_list, interval_end_str, sheet_data_list, True)

    # 获取管家服务岗指定区间到期客户数（会员 + 调解）
    server_out_result_json = _get_steward_server_out_result_json(steward_list, interval_end_str, sheet_data_list, False)

    # 获取数据后，创建新表
    new_workbook = Workbook()
    # 删除第一个空表
    del new_workbook['Sheet']

    # 创建第一个子表
    new_sheet_one = new_workbook.create_sheet("数据汇总")
    # 创建并设置汇总表头
    headers_one = ['顾问名称', '管家会员数', '管家调解数', '管家其它数', '服务会员数', '服务调解数', '服务其它数',
                   '管家会员新增数', '管家调解新增数', '服务会员新增数', '服务调解新增数', '管家会员到期数', '管家调解到期数', '服务会员到期数', '服务调解到期数']
    new_sheet_one.append(headers_one)
    # 定义明细表表头 - 会员
    headers_member = ['客户ID', '客户名称', '合同开始时间', '合同结束时间',
                      '套餐类型', '签约公司', '客服管家', '服务顾问', '签约销售', '收款金额']
    # 定义明细表表头 - 调解
    headers_mediate = ['客户ID', '客户名称', '合同开始时间', '合同结束时间', '调解户调解到期时间（半年）'
                      '套餐类型', '签约公司', '客服管家', '服务顾问', '签约销售', '收款金额']
    # 定义明细表表头 - 单项、回购等
    headers_other = ['客户ID', '客户名称', '合同开始时间', '合同结束时间', '加选/单项/回购到期时间'
                      '套餐类型', '签约公司', '客服管家', '服务顾问', '签约销售', '收款金额']

    # 这里先基于管家集循环
    for steward in steward_list:
        # 管家会员单
        steward_member_count = 0
        # 管家调解单
        steward_mediate_count = 0
        # 管家单项/回购数
        steward_other_count = 0
        # 服务会员单
        serve_member_count = 0
        # 服务调解单
        serve_mediate_count = 0
        # 服务单项/回购数
        serve_other_count = 0
        # 管家新增会员数
        steward_add_member_count = 0
        # 管家新增调解数
        steward_add_mediate_count = 0
        # 服务新增会员数
        serve_add_member_count = 0
        # 服务新增调解数
        serve_add_mediate_count = 0
        # 管家到期会员数
        steward_out_member_count = 0
        # 管家到期调解数
        steward_out_mediate_count = 0
        # 服务到期会员数
        serve_out_member_count = 0
        # 服务到期调解数
        serve_out_mediate_count = 0

        # 获取管家数据
        steward_result_dict = steward_result_json[steward] if steward in steward_result_json else {}
        for key, value in steward_result_dict.items():
            if "member" == key:
                # 会员数
                steward_member_count = len(value)
                # 创建表格
                new_sheet_two = new_workbook.create_sheet(f"{steward}管家会员客户明细")
                new_sheet_two.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_two.append(res_data)

            elif "mediate" == key:
                # 调解数
                steward_mediate_count = len(value)
                # 创建表格
                new_sheet_two = new_workbook.create_sheet(f"{steward}管家调解客户明细")
                new_sheet_two.append(headers_mediate)

                # 循环数据
                for res_data in value:
                    new_sheet_two.append(res_data)
            else :
                steward_other_count = len(value)
                # 创建表格
                new_sheet_two = new_workbook.create_sheet(f"{steward}管家其它客户明细")
                new_sheet_two.append(headers_other)
                # 循环数据
                for res_data in value:
                    new_sheet_two.append(res_data)

        # 获取服务数据
        serve_result_dict = serve_result_json[steward] if steward in serve_result_json else {}
        for key, value in serve_result_dict.items():
            if "member" == key:
                serve_member_count = len(value)
                # 创建表格
                new_sheet_three = new_workbook.create_sheet(f"{steward}服务会员客户明细")
                new_sheet_three.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_three.append(res_data)
            elif "mediate" == key:
                serve_mediate_count = len(value)
                # 创建表格
                new_sheet_three = new_workbook.create_sheet(f"{steward}服务调解客户明细")
                new_sheet_three.append(headers_mediate)

                # 循环数据
                for res_data in value:
                    new_sheet_three.append(res_data)
            else :
                serve_other_count = len(value)
                # 创建表格
                new_sheet_three = new_workbook.create_sheet(f"{steward}服务其它客户明细")
                new_sheet_three.append(headers_other)
                # 循环数据
                for res_data in value:
                    new_sheet_three.append(res_data)

        # 获取管家新增数
        steward_add_dict = steward_add_result_json[steward] if steward in steward_add_result_json else {}
        for key, value in steward_add_dict.items():
            if "member" == key:
                steward_add_member_count = len(value)
                # 创建表格
                new_sheet_four = new_workbook.create_sheet(f"{steward}管家会员新增客户明细")
                new_sheet_four.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_four.append(res_data)

            elif "mediate" == key:
                steward_add_mediate_count = len(value)
                # 创建表格
                new_sheet_four = new_workbook.create_sheet(f"{steward}管家调解新增客户明细")
                new_sheet_four.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_four.append(res_data)

        # 获取服务新增数
        serve_add_dict = serve_add_result_json[steward] if steward in serve_add_result_json else {}
        for key, value in serve_add_dict.items():
            if "member" == key:
                serve_add_member_count = len(value)
                # 创建表格
                new_sheet_five = new_workbook.create_sheet(f"{steward}服务会员新增客户明细")
                new_sheet_five.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_five.append(res_data)

            elif "mediate" == key:
                serve_add_mediate_count = len(value)
                # 创建表格
                new_sheet_five = new_workbook.create_sheet(f"{steward}服务调解新增客户明细")
                new_sheet_five.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_five.append(res_data)

        # 获取管家到期数
        steward_out_dict = steward_out_result_json[steward] if steward in steward_out_result_json else {}
        for key, value in steward_out_dict.items():
            if "member" == key:
                steward_out_member_count = len(value)
                # 创建表格
                new_sheet_six = new_workbook.create_sheet(f"{steward}管家会员到期客户明细")
                new_sheet_six.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_six.append(res_data)

            elif "mediate" == key:
                steward_out_mediate_count = len(value)
                # 创建表格
                new_sheet_six = new_workbook.create_sheet(f"{steward}管家调解到期客户明细")
                new_sheet_six.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_six.append(res_data)

        # 获取服务到期数
        serve_out_dict = server_out_result_json[steward] if steward in server_out_result_json else {}
        for key, value in serve_out_dict.items():
            if "member" == key:
                serve_out_member_count = len(value)
                # 创建表格
                new_sheet_seven = new_workbook.create_sheet(f"{steward}管家会员到期客户明细")
                new_sheet_seven.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_seven.append(res_data)

            elif "mediate" == key:
                serve_out_mediate_count = len(value)
                # 创建表格
                new_sheet_seven = new_workbook.create_sheet(f"{steward}管家调解到期客户明细")
                new_sheet_seven.append(headers_member)

                # 循环数据
                for res_data in value:
                    new_sheet_seven.append(res_data)

        # 设置汇总数据
        new_sheet_one.append([
            steward,
            steward_member_count,
            steward_mediate_count,
            steward_other_count,
            serve_member_count,
            serve_mediate_count,
            serve_other_count,
            steward_add_member_count,
            steward_add_mediate_count,
            serve_add_member_count,
            serve_add_mediate_count,
            steward_out_member_count,
            steward_out_mediate_count,
            serve_out_member_count,
            serve_out_mediate_count,
        ])

    # 保存数据
    out_url = paths_utils.get_resource_path("resources/get_steward_server_excel_new")
    new_workbook.save(
        f"{out_url}/{now_date.date()}管家及其服务客户数据表.xlsx")

    return DictResult.success_response(
        message="已获取完毕，请前往【resources/get_steward_server_excel_new】文件夹下查看",
        status_code=200,
        types="get_steward_server_during_data_to_excel",
        data=None
    )

"""获取管家及其服务岗的指定时间段到期数据"""
def _get_steward_server_out_result_json(steward_list, interval_end_str, sheet_data_list, is_steward):
    # 返回数据
    result_json = {}

    # 拆分时间
    start_date_str, end_date_str = interval_end_str.split("~")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    # 循环管家集
    for steward in steward_list:
        # 会员集合
        member_result_list = []
        # 调解集合
        mediate_result_list = []
        # 循环
        for row in sheet_data_list:
            # 先看是不是退费，是退费直接跳过
            is_refound = row[ColumnIndexTow.IS_REFUND].value
            if is_refound == "是":
                continue

            # 判断is_steward是走哪个分支
            if is_steward:
                # 判断管家
                steward_name = row[ColumnIndexTow.STEWARD_NAME].value
                if steward_name is None or steward_name == '缺失' or steward not in steward_name:
                    continue

                # 获取 客户名称单元格的颜色，过滤掉不需要的
                fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
                # 如果是这些颜色的数据，跳过，这些数据不算户数
                if fg_color.rgb[2:] in ['FFFF00', 'C0C0C0', '666699']:
                    continue
            else:
                # 这里判断的是服务顾问岗
                serve_name = row[ColumnIndexTow.SERVE_NAME].value
                if serve_name is None or serve_name == '缺失' or steward not in serve_name:
                    continue

                # 获取 客户名称单元格的颜色，过滤掉不需要的
                fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
                # 如果是这些颜色的数据，跳过，这些数据不算户数
                if fg_color.rgb[2:] in ['FFFF00', 'C0C0C0', '666699', '9999FF']:
                    continue

            # 获取客户套餐
            criterion_type = row[ColumnIndexTow.MEMBER_TYPE].value
            # 只获取会员及调解的客户
            if "会员" in criterion_type or "调解服务套餐" in criterion_type:
                # 合同到期时间
                end_time = row[ColumnIndexTow.END_TIME].value

                # 这里要分流
                if "会员" in criterion_type:
                    # 判断这个结束时间是否在区间内
                    between_date_bol = start_date <= end_time.date() <= end_date
                    if between_date_bol:
                        # 成立，获取相关信息
                        member_result_list.append([
                            # 客户ID
                            row[ColumnIndexTow.CUSTOMER_ID].value,
                            # 客户名称
                            row[ColumnIndexTow.COMPANY_NAME].value,
                            # 合同开始时间
                            row[ColumnIndexTow.START_TIME].value,
                            # 合同结束时间
                            row[ColumnIndexTow.END_TIME].value,
                            # 套餐类型
                            criterion_type,
                            # 签约公司
                            row[ColumnIndexTow.SALESMAN_COMPANY].value,
                            # 管家名称
                            row[ColumnIndexTow.STEWARD_NAME].value,
                            # 对应服务顾问
                            row[ColumnIndexTow.SERVE_NAME].value,
                            # 销售
                            row[ColumnIndexTow.SALESMAN_NAME].value,
                            # 首款金额
                            row[ColumnIndexTow.RECEIVE_MONEY].value
                        ])
                else:
                    # 判断这个结束时间是否在区间内
                    between_date_bol = start_date <= end_time.date() <= end_date
                    if between_date_bol:
                        mediate_result_list.append([
                            # 客户ID
                            row[ColumnIndexTow.CUSTOMER_ID].value,
                            # 客户名称
                            row[ColumnIndexTow.COMPANY_NAME].value,
                            # 合同开始时间
                            row[ColumnIndexTow.START_TIME].value,
                            # 合同结束时间
                            row[ColumnIndexTow.END_TIME].value,
                            # 调解户调解到期时间（半年）
                            row[ColumnIndexTow.MEMBER_END_TIME].value,
                            # 套餐类型
                            criterion_type,
                            # 签约公司
                            row[ColumnIndexTow.SALESMAN_COMPANY].value,
                            # 管家名称
                            row[ColumnIndexTow.STEWARD_NAME].value,
                            # 对应服务顾问
                            row[ColumnIndexTow.SERVE_NAME].value,
                            # 销售
                            row[ColumnIndexTow.SALESMAN_NAME].value,
                            # 首款金额
                            row[ColumnIndexTow.RECEIVE_MONEY].value
                        ])

        # 获取完数据后，设置到dict中
        result_json[steward] = {
            "member": member_result_list,
            "mediate": mediate_result_list
        }

    return result_json

"""获取管家及其服务岗的指定时间段新增数据"""
def _get_steward_server_add_result_json(steward_list, interval_end_str, sheet_data_list, is_steward):
    # 返回数据
    result_json = {}

    # 拆分时间
    start_date_str, end_date_str = interval_end_str.split("~")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    # 循环管家集
    for steward in steward_list:
        # 会员集合
        member_result_list = []
        # 调解集合
        mediate_result_list = []
        # 循环
        for row in sheet_data_list:
            # 先看是不是退费，是退费直接跳过
            is_refound = row[ColumnIndexTow.IS_REFUND].value
            if is_refound == "是":
                continue

            # 判断is_steward是走哪个分支
            if is_steward:
                # 判断管家
                steward_name = row[ColumnIndexTow.STEWARD_NAME].value
                if steward_name is None or steward_name == '缺失' or steward not in steward_name:
                    continue

                # 获取 客户名称单元格的颜色，过滤掉不需要的
                fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
                # 如果是这些颜色的数据，跳过，这些数据不算户数
                if fg_color.rgb[2:] in ['FFFF00', 'C0C0C0', '666699']:
                    continue
            else:
                # 这里判断的是服务顾问岗
                serve_name = row[ColumnIndexTow.SERVE_NAME].value
                if serve_name is None or serve_name == '缺失' or steward not in serve_name:
                    continue

                # 获取 客户名称单元格的颜色，过滤掉不需要的
                fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
                # 如果是这些颜色的数据，跳过，这些数据不算户数
                if fg_color.rgb[2:] in ['FFFF00', 'C0C0C0', '666699', '9999FF']:
                    continue

            # 获取客户套餐
            criterion_type = row[ColumnIndexTow.MEMBER_TYPE].value
            # 只获取会员及调解的客户
            if "会员" in criterion_type or "调解服务套餐" in criterion_type:
                # 质检审核通过时间
                quality_audit_date = row[ColumnIndexTow.QUALITY_AUDIT_DATE].value
                if quality_audit_date is None:
                    continue
                # 这里要分流，因为会员和调解的到期时间依据不一样
                if "会员" in criterion_type:
                    # 会员
                    # 判断这个结束时间是否在区间内
                    between_date_bol = start_date <= quality_audit_date.date() <= end_date
                    if between_date_bol:
                        # 成立，获取相关信息
                        member_result_list.append([
                            # 客户ID
                            row[ColumnIndexTow.CUSTOMER_ID].value,
                            # 客户名称
                            row[ColumnIndexTow.COMPANY_NAME].value,
                            # 合同开始时间
                            row[ColumnIndexTow.START_TIME].value,
                            # 合同结束时间
                            row[ColumnIndexTow.END_TIME].value,
                            # 套餐类型
                            criterion_type,
                            # 签约公司
                            row[ColumnIndexTow.SALESMAN_COMPANY].value,
                            # 管家名称
                            row[ColumnIndexTow.STEWARD_NAME].value,
                            # 对应服务顾问
                            row[ColumnIndexTow.SERVE_NAME].value,
                            # 销售
                            row[ColumnIndexTow.SALESMAN_NAME].value,
                            # 首款金额
                            row[ColumnIndexTow.RECEIVE_MONEY].value
                        ])
                else:
                    # 调解
                    # 判断这个结束时间是否在区间内
                    between_date_bol = start_date <= quality_audit_date.date() <= end_date
                    if between_date_bol:
                        mediate_result_list.append([
                            # 客户ID
                            row[ColumnIndexTow.CUSTOMER_ID].value,
                            # 客户名称
                            row[ColumnIndexTow.COMPANY_NAME].value,
                            # 合同开始时间
                            row[ColumnIndexTow.START_TIME].value,
                            # 合同结束时间
                            row[ColumnIndexTow.END_TIME].value,
                            # 调解户调解到期时间（半年）
                            row[ColumnIndexTow.MEMBER_END_TIME].value,
                            # 套餐类型
                            criterion_type,
                            # 签约公司
                            row[ColumnIndexTow.SALESMAN_COMPANY].value,
                            # 管家名称
                            row[ColumnIndexTow.STEWARD_NAME].value,
                            # 对应服务顾问
                            row[ColumnIndexTow.SERVE_NAME].value,
                            # 销售
                            row[ColumnIndexTow.SALESMAN_NAME].value,
                            # 首款金额
                            row[ColumnIndexTow.RECEIVE_MONEY].value
                        ])

        # 获取完数据后，设置到dict中
        result_json[steward] = {
            "member": member_result_list,
            "mediate": mediate_result_list
        }

    return result_json

"""获取管家及其服务岗的客户数据（会员 + 调解 + 单项、回购等）"""
def _get_steward_serve_result_json(steward_list, now_date, sheet_data_list, is_steward):
    # 返回数据
    result_json = {}

    # 循环管家集
    for steward in steward_list:
        # 会员集合
        member_result_list = []
        # 调解集合
        mediate_result_list = []
        # 单项、回购等杂项
        other_result_list = []
        # 循环
        for row in sheet_data_list:

            # 先看是不是退费，是退费直接跳过
            is_refound = row[ColumnIndexTow.IS_REFUND].value
            if is_refound == "是":
                continue

            # 判断is_steward是走哪个分支
            if is_steward:
                # 判断管家
                steward_name = row[ColumnIndexTow.STEWARD_NAME].value
                if steward_name is None or steward_name == '缺失' or steward not in steward_name:
                    continue

                # 获取 客户名称单元格的颜色，过滤掉不需要的
                fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
                # 如果是这些颜色的数据，跳过，这些数据不算户数
                if fg_color.rgb[2:] in ['FFFF00', 'C0C0C0', '666699', '9999FF']:
                    continue
            else:
                # 这里判断的是服务顾问岗
                serve_name = row[ColumnIndexTow.SERVE_NAME].value
                if serve_name is None or serve_name == '缺失' or steward not in serve_name:
                    continue

                # 获取 客户名称单元格的颜色，过滤掉不需要的
                fg_color = row[ColumnIndexTow.COMPANY_NAME].fill.fgColor
                # 如果是这些颜色的数据，跳过，这些数据不算户数
                if fg_color.rgb[2:] in ['FFFF00', 'C0C0C0', '666699']:
                    continue

            # 获取客户套餐
            criterion_type = row[ColumnIndexTow.MEMBER_TYPE].value
            # 只获取会员及调解的客户
            if "会员" in criterion_type or "调解服务套餐" in criterion_type:
                # 这里要分流，因为会员和调解的到期时间依据不一样
                if "会员" in criterion_type:
                    # 会员
                    # 合同结束时间
                    end_time = row[ColumnIndexTow.END_TIME].value
                    # 判断指定的时间是否小于合同结束时间
                    check_item_bol = now_date <= end_time
                    if check_item_bol:
                        # 成立，获取相关信息
                        member_result_list.append([
                            # 客户ID
                            row[ColumnIndexTow.CUSTOMER_ID].value,
                            # 客户名称
                            row[ColumnIndexTow.COMPANY_NAME].value,
                            # 合同开始时间
                            row[ColumnIndexTow.START_TIME].value,
                            # 合同结束时间
                            end_time,
                            # 套餐类型
                            criterion_type,
                            # 签约公司
                            row[ColumnIndexTow.SALESMAN_COMPANY].value,
                            # 管家名称
                            row[ColumnIndexTow.STEWARD_NAME].value,
                            # 对应服务顾问
                            row[ColumnIndexTow.SERVE_NAME].value,
                            # 销售
                            row[ColumnIndexTow.SALESMAN_NAME].value,
                            # 首款金额
                            row[ColumnIndexTow.RECEIVE_MONEY].value
                        ])
                else:
                    # 调解
                    branch = False
                    if branch:
                        # 调解的结束时间  暂时  按照“调解户调解到期时间（半年）”这个字段来
                        member_end_time = row[ColumnIndexTow.MEMBER_END_TIME].value
                    else:
                        # 合同结束时间
                        member_end_time = row[ColumnIndexTow.END_TIME].value

                    # 判断指定的时间是否小于调解的结束时间
                    check_item_bol = now_date <= member_end_time
                    if check_item_bol:
                        mediate_result_list.append([
                            # 客户ID
                            row[ColumnIndexTow.CUSTOMER_ID].value,
                            # 客户名称
                            row[ColumnIndexTow.COMPANY_NAME].value,
                            # 合同开始时间
                            row[ColumnIndexTow.START_TIME].value,
                            # 合同结束时间
                            row[ColumnIndexTow.END_TIME].value,
                            # 调解户调解到期时间（半年）
                            member_end_time,
                            # 套餐类型
                            criterion_type,
                            # 签约公司
                            row[ColumnIndexTow.SALESMAN_COMPANY].value,
                            # 管家名称
                            row[ColumnIndexTow.STEWARD_NAME].value,
                            # 对应服务顾问
                            row[ColumnIndexTow.SERVE_NAME].value,
                            # 销售
                            row[ColumnIndexTow.SALESMAN_NAME].value,
                            # 首款金额
                            row[ColumnIndexTow.RECEIVE_MONEY].value
                        ])
            else:
                # 单项、回购等杂项
                add_end_time = row[ColumnIndexTow.ADD_END_TIME].value
                check_item_bol = now_date <= add_end_time
                if check_item_bol:
                    other_result_list.append([
                        # 客户ID
                        row[ColumnIndexTow.CUSTOMER_ID].value,
                        # 客户名称
                        row[ColumnIndexTow.COMPANY_NAME].value,
                        # 合同开始时间
                        row[ColumnIndexTow.START_TIME].value,
                        # 合同结束时间
                        row[ColumnIndexTow.END_TIME].value,
                        # 单项、回购等的到期时间
                        add_end_time,
                        # 套餐类型
                        criterion_type,
                        # 签约公司
                        row[ColumnIndexTow.SALESMAN_COMPANY].value,
                        # 管家名称
                        row[ColumnIndexTow.STEWARD_NAME].value,
                        # 对应服务顾问
                        row[ColumnIndexTow.SERVE_NAME].value,
                        # 销售
                        row[ColumnIndexTow.SALESMAN_NAME].value,
                        # 首款金额
                        row[ColumnIndexTow.RECEIVE_MONEY].value
                    ])

            # 获取完数据后，设置到dict中
            result_json[steward] = {
                "member": member_result_list,
                "mediate": mediate_result_list,
                "other": other_result_list
            }

    return result_json