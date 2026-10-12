import json
import time
import traceback
import unicodedata
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import PatternFill
from tqdm import tqdm

from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
from src.utils import paths_utils as paths
from src.utils.dict_result import DictResult
from src.utils.logging_utils import loggings_info, loggings_error
from src.utils.sheet_column_index_utils import ColumnIndex, ColumnIndexTow


"""
主程序
"""
def public_sync_main(main_file_name, out_file_name):
    try:
        # 执行程序1
        loggings_info("开始执行程序1: 线下客户表更新")
        _sync_customer_procedure_one(main_file_name)

        # 执行程序2
        loggings_info("开始执行程序2: 线下客户表数据调整")
        new_workbook = _sync_customer_procedure_two(main_file_name)

        # 执行程序3
        loggings_info("开始执行程序3：处理回购客户金额数据")
        _sync_customer_money_procedure_three(new_workbook)

        # 执行程序4
        loggings_info("开始执行程序4：处理调解未升级客户半年到期时间")
        _sync_customer_mediate_end_time_four(new_workbook)

        # 执行最终程序
        loggings_info(f"开始执行最终程序：写入{out_file_name}.xlsx")
        _sync_customer_procedure_final_end(new_workbook, out_file_name)

        loggings_info("程序执行结束")

        return DictResult.success_response(
            message="同步成功，请前往【resource/excel_templates】文件夹查看结果",
            status_code=200,
            types="sync_data_info",
            data=None
        )

    except Exception as e:
        error_msg = f'程序执行出错：{e}'
        loggings_error(error_msg)
        loggings_error(traceback.format_exc())

        return DictResult.error_response(
            message=f"同步失败，请联系开发人员：{error_msg}",
            status_code=500,
            types="sync_data_info",
            data=None
        )

"""最终程序，写入表格"""
def _sync_customer_procedure_final_end(new_workbook, out_file_name):
    # 获取资源路径
    data_dir = paths.get_resource_path('resources/excel_templates')

    loggings_info(f"正在写入{out_file_name}.xlsx......")
    start_time = time.time()

    new_workbook.save(f"{data_dir}/{out_file_name}.xlsx")

    # 执行完成并输出日志
    end_time = time.time()
    processing_time = end_time - start_time
    completion_msg = f"写入{out_file_name}.xlsx结束......！总耗时: {processing_time:.2f} 秒"
    loggings_info(completion_msg)

    new_workbook.close()

"""
处理调解未升级客户半年到期时间
"""
def _sync_customer_mediate_end_time_four(new_workbook):
    # 获取资源路径
    data_dir = paths.get_resource_path('resources/excel_templates')
    # 获取调解套餐升级数据
    mediate_to_member_customer_list = _get_mediate_to_member_customer(data_dir)
    # 预处理
    member_customer_dict = { (item['调解名称'], item['调解到账时间']) : item for item in mediate_to_member_customer_list}

    # 获取表格
    sheet = new_workbook['线下客户表']
    # 获取数据
    min_row = 2
    rows_list = list(sheet.iter_rows(min_row= min_row, values_only=False))
    # 处理数据
    for index, row in enumerate(rows_list):
        # 先隔一层，判断套餐类型是否是调解类型，如果是就跳过减少处理时间
        member_type = row[ColumnIndexTow.MEMBER_TYPE].value
        if '调解服务套餐' not in member_type:
            continue

        # 这里通过客户表信息的客户名称和到账时间匹配
        # 客户名称
        company_name = row[ColumnIndexTow.COMPANY_NAME].value
        # 到账时间
        accounting_date = row[ColumnIndexTow.ACCOUNTING_TIME].value

        # 通过客户名称 + 到账时间组合key，判断member_customer_dict中是否存在
        key = (company_name, accounting_date)
        member_customer = member_customer_dict.get(key)
        if member_customer is not None:
            # 说明当前客户已经升级为一年会员，将当前数据标灰
            row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color="C0C0C0", end_color="C0C0C0",
                                                                     fill_type="solid")
            # 然后在【调解户调解到期时间】列写入“已升级为年费会员”
            row[ColumnIndexTow.MEMBER_END_TIME].value = "已升级为年费会员"

            # 已升级的不继续处理时间，跳过
            continue

        # 能走到这的说明是要处理半年的调解到期时间的客户
        # 依据这名客户的到账时间，在此基础上加6个月再减1天
        new_accounting_date = accounting_date + relativedelta(months=6) - relativedelta(days=1)
        # 将新数据写入
        row[ColumnIndexTow.MEMBER_END_TIME].value = new_accounting_date

"""
处理回购客户金额数据（程序3）
"""
def _sync_customer_money_procedure_three(new_workbook):
    # 获取表格
    sheet = new_workbook['线下客户表']
    # 获取数据
    rows_list = list(sheet.iter_rows(min_row=2, values_only=False))
    # 处理数据
    for index, row in enumerate(rows_list):
        # 这里只获取回购的数据
        if row[ColumnIndexTow.MEMBER_TYPE].value is not None and '回购' in row[ColumnIndexTow.MEMBER_TYPE].value:
            # 获取客户名称
            current_company_name = row[ColumnIndexTow.COMPANY_NAME].value
            # 获取联系方式
            current_contact_phone = row[ColumnIndexTow.CONTACT_PHONE].value
            # 获取身份证号码或企业信用代码
            current_code = row[ColumnIndexTow.CODE].value

            """回购的判断逻辑也可以按照找续费旧单的逻辑进行，原理依旧是按照ID排序后向上查找"""
            for desc_index in range(index, -1, -1):
                # 过滤自己
                if desc_index == index:
                    continue
                # 获取相关行数据
                desc_row = rows_list[desc_index]

                """这里先简单判断同名客户的回购，暂时不涵盖异主体旧单回购"""
                # 依次获取客户名称、联系方式、身份证号码或企业信用代码、合同类型
                desc_company_name = desc_row[ColumnIndexTow.COMPANY_NAME].value
                desc_contact_phone = desc_row[ColumnIndexTow.CONTACT_PHONE].value
                desc_code = desc_row[ColumnIndexTow.CODE].value
                desc_member_type = desc_row[ColumnIndexTow.MEMBER_TYPE].value

                # 进行判断，只找会员单（调解会员是否涵盖待后续确定）
                if '会员' not in desc_member_type:
                    continue

                # 判断1: 同名客户名称 加上 联系方式或身份证及企业信用代码一致，即判断为对应会员到期单
                bol_one = current_company_name == desc_company_name and (current_contact_phone == desc_contact_phone or current_code == desc_code)
                # 判断2: 同名客户名称+联系方式 加上 联系方式或身份证及企业信用代码一致，即判断为对应会员到期单
                bol_two = (current_company_name + current_contact_phone) == desc_company_name and (current_contact_phone == desc_contact_phone or current_code == desc_code)
                # 两个判断条件成立一个即可
                if bol_one or bol_two:
                    # 将当前回购单的金额，填到找到的原会员单的回购列中
                    desc_row[ColumnIndexTow.REPO].value += row[ColumnIndexTow.RECEIVE_MONEY].value
                    # 给当前单设置历史会员ID
                    row[ColumnIndexTow.OLD_CUSTOMER_ID].value = desc_row[ColumnIndexTow.CUSTOMER_ID].value

                    # 打断这个循环
                    break

"""
线下客户表更新（程序1）
"""
def _sync_customer_procedure_one(main_file_name):
    # 获取资源路径
    data_dir = paths.get_resource_path('resources/excel_templates')
    # 读表
    loggings_info(f"正在读取【客户源表.xlsx】......")
    workbook = load_workbook(f"{data_dir}/客户源表.xlsx")
    sheet = workbook["线下客户表"]
    loggings_info(f"读取【客户源表.xlsx】结束......")

    # 调解升级单
    mediate_to_member_customer_list = _get_mediate_to_member_customer(data_dir)

    # 循环获取表中的客户id，同时对部分单元格进行新增
    customer_ids = []
    row_list = list(sheet.iter_rows(min_row=2, values_only=False))
    for row in row_list:
        # 获取客户id
        customer_ids.append(row[0].value)

    # 创建第二个子表
    if "客户交付事项明细" in workbook.sheetnames:
        del workbook["客户交付事项明细"]

    sheet_two = workbook.create_sheet("客户交付事项明细")
    # 建立首行
    headers = ["客户ID", "序号", "客户名称", "客户事项", "事项类型", "服务顾问", "法律顾问", "交付时间"]
    for col_index, header in enumerate(headers, start=1):
        sheet_two.cell(row=1, column=col_index, value=header)

    # 调用处理方法，得到最终数据
    json_result = _auxiliary_procedure(customer_ids, mediate_to_member_customer_list)

    # 客户交付事项明细初始序号
    sheet_two_index = 1

    # 循环结果集，并处理这些数据
    loggings_info("开始设置客户数据到Excel")
    for index, json_data in tqdm(enumerate(list(json_result), start= 2), total= len(json_result), desc= "设置客户数据中......"):
        # 客户ID
        sheet.cell(row=index, column= ColumnIndex.CUSTOMER_ID, value=json_data["id"])
        # 续费旧单ID
        sheet.cell(row=index, column= ColumnIndex.OLD_CUSTOMER_ID, value='')
        # 服务总次数
        sum_count = json_data["obj"].ok_num + json_data["obj"].no_num
        sheet.cell(row=index, column= ColumnIndex.SUM_COUNT, value=sum_count)
        # 立案初始次数
        sheet.cell(row=index, column= ColumnIndex.LAWSUIT_COUNT, value= json_data['lawsuitCount'] if 'lawsuitCount' in json_data else "")
        # 服务剩余次数
        sheet.cell(row=index, column= ColumnIndex.SURPLUS_COUNT, value=(sum_count - json_data['hjCount']))

        """设置合同信息"""
        # 客户名称
        sheet.cell(row=index, column= ColumnIndex.COMPANY_NAME, value=json_data["obj"].company_name)
        # 开始时间
        sheet.cell(row=index, column= ColumnIndex.START_TIME, value=json_data["startTime"])
        # 结束时间
        sheet.cell(row=index, column= ColumnIndex.END_TIME, value=(json_data["minEndTime"] if json_data["minEndTime"] else ""))
        # 加选结束时间
        sheet.cell(row=index, column= ColumnIndex.ADD_END_TIME, value=(json_data["maxEndTime"] if json_data["maxEndTime"] else ""))
        # 套餐类型
        sheet.cell(row=index, column= ColumnIndex.ITEM_MEAL, value=json_data["itemMeal"])
        # 行业分类
        sheet.cell(row=index, column= ColumnIndex.INDUSTRY_TYPE, value=json_data["obj"].industry_type)
        # 联系人
        sheet.cell(row=index, column= ColumnIndex.CONTACT, value=json_data["obj"].contact)
        # 联系方式
        sheet.cell(row=index, column= ColumnIndex.CONTACT_PHONE, value=json_data["obj"].contact_phone)
        # 是否建群
        room_id = json_data["obj"].room_id
        sheet.cell(row=index, column= ColumnIndex.IS_GROUP, value="是" if room_id else "否")
        # 群id
        sheet.cell(row=index, column= ColumnIndex.ROOM_ID, value=room_id)
        # 关联自然人、企业
        sheet.cell(row=index, column= ColumnIndex.ASSOCIATED_PERSON, value=json_data["obj"].associated_person)
        sheet.cell(row=index, column= ColumnIndex.ENTERPRISE_NAME, value=json_data["obj"].enterprise_name)
        # 谈单方式
        methods = json_data["obj"].enterprise_name
        methods = "非诉指导" if "NLG" == methods else \
            "非诉+诉讼指导" if "NLG_LG" == methods else \
                "诉讼指导" if "LG" == methods else "暂无"
        sheet.cell(row=index, column= ColumnIndex.METHODS, value=methods)
        # 分公司名称
        sheet.cell(row=index, column= ColumnIndex.SALESMAN_COMPANY, value=json_data["obj"].salesman_company)
        # 债权（客服）
        sheet.cell(row=index, column= ColumnIndex.STEWARD_NAME, value= "" if json_data["obj"].steward_name is None else json_data["obj"].steward_name)
        # 服务顾问
        sheet.cell(row=index, column= ColumnIndex.SERVE_NAME, value= "" if json_data["obj"].serve_name is None else json_data["obj"].serve_name)
        # 法律顾问
        lawers = json_data["obj"].lawers
        law_name = None
        if lawers:
            lawers = json.loads(lawers)
            law_name = lawers[0]["lawName"] if (lawers and len(lawers) > 0) else ""
            sheet.cell(row=index, column= ColumnIndex.LAWERS, value=law_name)
        else:
            # 这里主要是兼容置空操作
            sheet.cell(row=index, column= ColumnIndex.LAWERS, value="")

        # 合同顾问
        sheet.cell(row=index, column= ColumnIndex.CONSULTANT_NAME, value=json_data["obj"].consultant_name)
        # 收款金额
        receive_money = json_data["obj"].receive_money
        sheet.cell(row=index, column= ColumnIndex.RECEIVE_MONEY, value= receive_money)

        # 服务过程中加选金额
        add_money_count = json_data["addMoneyCount"] if 'addMoneyCount' in json_data else 0
        sheet.cell(row=index, column= ColumnIndex.ADD_ON_MONEY, value= add_money_count)
        # 回购
        sheet.cell(row=index, column= ColumnIndex.REPO, value= 0)
        # 单项
        sheet.cell(row=index, column= ColumnIndex.SINGLE, value= '')
        # 续费
        sheet.cell(row=index, column= ColumnIndex.RENEWAL, value= 0)
        # 升级会员
        upgrade_money_count = json_data["upgradeMoneyCount"] if 'upgradeMoneyCount' in json_data else 0
        sheet.cell(row=index, column= ColumnIndex.UPGRADE, value= upgrade_money_count)
        # 历史共计收款金额
        old_money_count = receive_money + add_money_count + upgrade_money_count
        sheet.cell(row=index, column= ColumnIndex.OLD_MONEY_COUNT, value=old_money_count)
        # 收款大于等于10000元
        # sheet.cell(row=index, column= ColumnIndex.MORE_THAN_10000, value=f'=IF(SUM(Y{index}:AD{index})>=10000,"是","否")')
        sheet.cell(row=index, column=ColumnIndex.MORE_THAN_10000, value='')

        # 我方收款公司
        sheet.cell(row=index, column= ColumnIndex.PAYEE_NAME, value=json_data["obj"].payee_name_str)
        # 社会代码或身份证号
        sheet.cell(row=index, column= ColumnIndex.CODE, value=json_data["obj"].code)
        # 签约主体
        payee_name = json_data["obj"].payee_name
        sheet.cell(row=index, column= ColumnIndex.PAYEE_OBJ, value="未知" if not payee_name else "法益网" if "FYW" in payee_name else "状先生")
        # 分配顾问时间
        sheet.cell(row=index, column= ColumnIndex.AFTER_TIME, value=json_data["afterTime"])
        # 是否在期
        sheet.cell(row=index, column= ColumnIndex.IS_DURING, value="废弃")
        # 是否已分配顾问
        serve_name = json_data["obj"].serve_name
        is_exist_law_serve = serve_name or law_name
        sheet.cell(row=index, column= ColumnIndex.IS_EXIST_LAW_SERVER, value="是" if is_exist_law_serve else "否")

        """设置交付数据"""
        sheet.cell(row=index, column= ColumnIndex.HJ_COUNT, value=json_data["hjCount"])
        sheet.cell(row=index, column= ColumnIndex.QSZ, value=json_data["qsz"])
        sheet.cell(row=index, column= ColumnIndex.ZDLA, value=json_data["zdla"])
        sheet.cell(row=index, column= ColumnIndex.LSH, value=json_data["lsh"])
        sheet.cell(row=index, column= ColumnIndex.CKH, value=json_data["ckh"])
        sheet.cell(row=index, column= ColumnIndex.QZZX, value=json_data["qzzx"])
        sheet.cell(row=index, column= ColumnIndex.BQ, value=json_data["bq"])
        sheet.cell(row=index, column= ColumnIndex.DBZ, value=json_data["dbz"])
        sheet.cell(row=index, column= ColumnIndex.HTWS, value=json_data["htws"])

        """设置交付事项明细"""
        customer_service = json_data["serviceList"]
        for service_record in list(customer_service):
            # 客户ID
            sheet_two.cell(row=(sheet_two_index + 1), column=1, value=service_record.customer_id)
            # 序号
            sheet_two.cell(row=(sheet_two_index + 1), column=2, value=sheet_two_index)
            # 客户名称
            sheet_two.cell(row=(sheet_two_index + 1), column=3, value=service_record.company_name)
            # 客户事项
            sheet_two.cell(row=(sheet_two_index + 1), column=4, value=service_record.service_name)
            # 事项类型
            sheet_two.cell(row=(sheet_two_index + 1), column=5, value=service_record.item_name)
            # 服务顾问
            sheet_two.cell(row=(sheet_two_index + 1), column=6, value=service_record.serve_id)
            # 法律顾问
            service_law = service_record.lawers
            service_law_name = ""
            if service_law:
                service_law = json.loads(service_law)
                service_law_name = service_law[0]["lawName"] if (service_law and len(service_law) > 0 and 'lawName' in service_law[0]) else ""

            sheet_two.cell(row=(sheet_two_index + 1), column=7, value=service_law_name)
            # 交付时间
            sheet_two.cell(row=(sheet_two_index + 1), column=8, value=service_record.confirm_date)
            # 递增
            sheet_two_index += 1

    # 写出文件
    loggings_info(f"正在写入{main_file_name}.xlsx......")
    # 使用一个线程计时保存文件时间
    start_time = time.time()
    try:
        workbook.save(f"{data_dir}/{main_file_name}.xlsx")
    except Exception as e:
        error_msg = f'文件保存出错：{e}'
        loggings_error(error_msg)

    # 执行完成并输出日志
    end_time = time.time()
    processing_time = end_time - start_time
    completion_msg = f"写入{main_file_name}.xlsx结束......总耗时: {processing_time:.2f} 秒"
    loggings_info(completion_msg)

    workbook.close()

"""
程序1辅助函数
"""
def _auxiliary_procedure(customer_ids, mediate_to_member_customer_list):
    loggings_info("开始获取客户数据")

    # 根据customer_ids获取客户数据
    customer_list = QueryMysqlDatabase().query_customer_by_ids(customer_ids)

    # 获取客服账号
    steward_list = QueryMysqlDatabase().query_sys_user_list(
        [customer.steward_id for customer in customer_list]
    )

    # 获取合同信息
    contract_list = QueryMysqlDatabase().query_customer_contract_list(customer_ids)

    # 获取顾问分配记录
    counselor_log_list = QueryMysqlDatabase().query_counselor_log_list()

    # 获取已计提的交付数据
    service_record_list = QueryMysqlDatabase().query_service_record_confirm_list(customer_ids)

    # 获取顾问账号信息
    sys_user_list = QueryMysqlDatabase().query_law_server_sys_user_list([3, 4])
    sys_user_map = {sysUser.user_id : sysUser.user_name for sysUser in sys_user_list}

    # 获取行业类型数据字典
    sys_dict_data_list = QueryMysqlDatabase().query_sys_dict_data_list("law_industry_type")
    sys_dict_data_map = { sysDict.dict_value : sysDict.dict_label for sysDict in sys_dict_data_list}

    # 获取我方收款公司选项
    sys_payee_data_list = QueryMysqlDatabase().query_sys_dict_data_list("law_payee_name")
    sys_payee_data_map = { sysDict.dict_value : sysDict.dict_label for sysDict in sys_payee_data_list }

    # 获取客户的加选金额数据
    customer_add_money_list = QueryMysqlDatabase().get_customer_add_money(customer_ids)

    # 获取客户的立案初始次数
    customer_lawsuit_init_count_list = QueryMysqlDatabase().get_customer_lawsuit_init_count(customer_ids)

    start_time_msg = f"开始处理客户数据，需要处理{len(customer_list)}条，开始时间：{time.strftime('%H:%M:%S')}"
    loggings_info(start_time_msg)

    # 处理结束后把最终集合返回
    return _optimized_loop(customer_list, steward_list, counselor_log_list,
                        contract_list, service_record_list, sys_dict_data_map,
                        sys_user_map, sys_payee_data_map, customer_add_money_list, mediate_to_member_customer_list, customer_lawsuit_init_count_list)

"""
检查合同类型并转换
"""
def _check_item_meal(item_meal, thali_id):
    match item_meal:
        case "MEDIATION":
            item_meal = "调解服务套餐" + ("" if "无" == thali_id else " + 调解立案加选")

        case "ONEYEAR":
            item_meal = "一年会员" + ("" if "无" == thali_id else " + 加选")

        case "TWOYEAR":
            item_meal = "两年会员" + ("" if "无" == thali_id else " + 加选")

        case "THREEYEAR":
            item_meal = "三年会员" + ("" if "无" == thali_id else " + 加选")

        case "REPO":
            item_meal = "回购"

        case "SINGLE":
            item_meal = "单项"

        case "NON,REPO":
            item_meal = "回购 + 加选"

        case _:
            # 依次为：加选、加急
            non = "NON" in item_meal
            urgent = "URGENT" in item_meal
            # case没匹配，进一步判断
            if "MEDIATION" in item_meal and "MEDIATION_ADD" in item_meal:
                item_meal = "调解服务套餐 + 调解立案加选"

            elif "ONEYEAR" in item_meal and not ("TWOYEAR" in item_meal) and not ("THREEYEAR" in item_meal):
                item_meal = "一年会员" + (" + 加选" if non else "") + (" + 加急" if urgent else "")

            elif "TWOYEAR" in item_meal and not ("ONEYEAR" in item_meal) and not ("THREEYEAR" in item_meal):
                item_meal = "两年会员" + (" + 加选" if non else "") + (" + 加急" if urgent else "")

            elif "THREEYEAR" in item_meal and not ("TWOYEAR" in item_meal) and not ("ONEYEAR" in item_meal):
                item_meal = "三年会员" + (" + 加选" if non else "") + (" + 加急" if urgent else "")

            elif 'REPO,URGENT' in item_meal:
                item_meal = "回购 + 加急"

            elif 'NON' in item_meal and 'YEAR' not in item_meal:
                # 这里和上面之所以冲突，是因为这里要处理调整之前的数据，共有17条数据在调整前，故其应当为回购数据
                item_meal = '回购'

            else:
                if "ONEYEAR" in item_meal and "THREEYEAR" in item_meal:
                    item_meal = "(三+一)年会员" + (" + 加选" if non else "") + (" + 加急" if urgent else "")

                elif "ONEYEAR" in item_meal and "TWOYEAR" in item_meal:
                    item_meal = "(二+一)年会员" + (" + 加选" if non else "") + (" + 加急" if urgent else "")

                elif "THREEYEAR" in item_meal and "TWOYEAR" in item_meal:
                    item_meal = "(三+二)年会员" + (" + 加选" if non else "") + (" + 加急" if urgent else "")

    return item_meal

"""
线下客户表数据更新（程序2）
"""
def _sync_customer_procedure_two(main_file_name):
    # 获取资源路径
    data_dir = paths.get_resource_path('resources/excel_templates')

    # 获取调解套餐升级数据
    mediate_to_member_customer_list = _get_mediate_to_member_customer(data_dir)

    # 获取退款客户数据
    return_price_customer_list = _get_return_price(data_dir)

    # 获取续费客户新旧单据数据
    old_receipt_data_list = _get_old_receipt_data(data_dir)

    # 获取特殊客户表第一子表数据
    special_company_record_one_data_list = _check_special_company_record_one_sheet(data_dir)
    # 给个源集，后续需要
    source_special_company_record_one_data_list = special_company_record_one_data_list.copy()

    # 获取表格
    loggings_info(f"正在读取{main_file_name}.xlsx......")
    workbook = load_workbook(f"{data_dir}/{main_file_name}.xlsx")
    sheet = workbook["线下客户表"]
    loggings_info(f"读取{main_file_name}.xlsx结束......")

    # 设置批注
    sheet.cell(1, ColumnIndex.COMPANY_NAME).comment = Comment('颜色说明：\n '
                    '1、（均不选）灰色，续费原(旧)单，核算实际户数时可以直接扣除相应总数 \n  '
                    '2、（均选）绿色，续费单，能够找到旧单的续费客户，核算实际户数需要算上相应总数 \n  '
                    '3、（均选）红色，续费单，但无法找到旧单，核算实际户数时应算上相应总数 \n  '
                    '4、（均选）橙色，续费单，其原单为老套餐客户，核算实际户数时应算上相应总数 \n  '
                    '5、（均不选）黄色，已退费客户，视实际情况核算总数 \n  '
                    '6、（叶）紫色，续费原(原)单。其最新续费单没分配顾问，且本单还在期并系统分有顾问，核算分户数时应勾选上 \n  '
                    '7、（非续费数外不选）蓝灰色，特殊续费单，该颜色的续费单合并进旧单中，其时间已被旧单延长，核算户数时应当扣减', "HJN")

    # 回购列设置批注
    sheet.cell(1, ColumnIndex.REPO).comment = Comment('回购的金额当前是放在对应的到期会员单上，但这样会让历史收款金额的合计出现问题，合计应当是由最新'
                                                      '数据依次累加，而不是在旧的数据中求和，所以当前未将回购金额统计进历史收款金额中', 'HJN')

    # 历史收款金额合计批注
    sheet.cell(1, ColumnIndex.OLD_MONEY_COUNT).comment = Comment('历史收款合计，获取上一个符合条件的客户数据的【历史收款合计】，多相同单据时只获取最近的那一个', 'HJN')

    sheet.cell(1, ColumnIndex.LAWSUIT_COUNT).comment = Comment('这个数据仅统计立案的初始次数（合同+加选），其存在误差，影响项包括但不限于：\n'
                                                               '1、续费后手动继承原单未使用数据\n'
                                                               '2、特批处理，如用立案换合同等\n'
                                                               '3、升级，升级不改变升级前数据，即一年2个立案，升级为二年5个立案，数据库只记录最初的2', 'HJN')

    # 获取表格所有行数据
    row_list = list(sheet.iter_rows(min_row= 2, values_only= False))
    # 循环处理
    loggings_info("开始循环处理客户数据")
    for index, row in enumerate(tqdm(row_list, desc='循环处理进度......')):
        # 目的是为了过滤首行
        if index == 0:
            continue

        # 公司名称
        company_name = row[ColumnIndexTow.COMPANY_NAME].value
        if company_name is None:
            # 过滤空白行
            continue

        # 身份证号或统一信用号
        code = row[ColumnIndexTow.CODE].value
        # 联系方式
        phone = row[ColumnIndexTow.CONTACT_PHONE].value
        # 到账时间
        accounting_date = row[ColumnIndexTow.ACCOUNTING_TIME].value
        # 服务顾问
        new_server_name = row[ColumnIndexTow.SERVE_NAME].value
        # 法律顾问
        new_law_name = row[ColumnIndexTow.LAWERS].value

        #判断是否是退费客户
        return_price_data = _check_return_price(company_name, accounting_date, return_price_customer_list)
        if return_price_data is not None:
            # 说明当前客户有退费记录，标黄色
            row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color = "FFFF00", end_color = "FFFF00", fill_type = "solid")
            row[ColumnIndexTow.COMPANY_NAME].comment = Comment(f'退费客户，退费时间：{return_price_data['退款时间']}，退费原因：{return_price_data['退款原因']}', 'ZFN')
            row[ColumnIndexTow.IS_REFUND].value = "是"
            # 进入下个循环，当前客户数据不再处理
            continue

        # 获取会员类型
        member_type = row[ColumnIndexTow.MEMBER_TYPE].value
        if '会员' not in member_type:
            # 如果当前客户不是会员类，不做处理
            continue

        # 客户ID
        customer_id = row[ColumnIndexTow.CUSTOMER_ID].value
        # 是否是续费客户
        is_xf = row[ColumnIndexTow.IS_RENEWAL].value

        if '否' == is_xf:
            special_customer = None
            # 不是续费客户，则先判断是不是特殊记录的客户
            for item in special_company_record_one_data_list:
                if item['客户id'] == customer_id:
                    special_customer = item
                    special_company_record_one_data_list.remove(item)
                    break

            #说明不是特殊记录客户
            if special_customer is None:
                start_date = row[ColumnIndexTow.START_TIME].value
                # 进一步检查是否是调解升级
                if '调解升级' in company_name:
                    for item in mediate_to_member_customer_list:
                        if company_name == item['会员名称']:
                            start_date = item['调解到账时间']
                            break

                # 确定开始时间后，处理并生成结束时间
                row[ColumnIndexTow.END_TIME].value = _create_new_end_time(start_date, member_type)
            else :
                # 如果是特殊记录客户，以该表中记录为准
                row[ColumnIndexTow.END_TIME].value = special_customer['客户合同结束时间']
                row[ColumnIndexTow.ADD_END_TIME].value = special_customer['客户加选最长结束时间']
                row[ColumnIndexTow.MEMBER_TYPE].value = special_customer['客户套餐类型']
                if special_customer['颜色'] is not None:
                    if '蓝灰' == special_customer['颜色']:
                        row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color = "666699", end_color = "666699", fill_type = "solid")
                    else :
                        # 白色
                        row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color = "FFFFFF", end_color = "FFFFFF", fill_type = "solid")
        else :
            """
            续费客户，需要找到历史单据
            逻辑：对客户表的客户ID进行升序后，续费单的客户ID因为采用数值递增模式必然比旧单的客户ID大
                 那么从（当前行数 - 1）向上查找，找到最近一条符合条件的数据，按照（客户名称/客户名称+联系方式 + 身份信息/企业信用代码）判断
            """
            # 旧单的结束时间
            desc_end_date = None

            # 第一步、先检查是否是特殊续费客户，如果是说明这个客户数据已经存在合并情况
            not_special = True
            for item in source_special_company_record_one_data_list:
                if item['客户id'] == customer_id:
                    # 找到，将not_special标识为False
                    not_special = False
                    break

            # 第二步、向上查找历史数据（这里直接根据相同的客户名称查询）
            for desc_index in range(index, -1, -1):
                # 避免自己匹配自己
                if desc_index == index:
                    continue

                # 获取当前表格中已处理的数据
                desc_row = row_list[desc_index]
                # 只匹配年费会员
                desc_member_type = desc_row[ColumnIndexTow.MEMBER_TYPE].value
                if '会员' not in desc_member_type:
                    continue

                # 获取关键判断信息，客户名、联系方式、身份证号或统一信用号、
                desc_company_name = desc_row[ColumnIndexTow.COMPANY_NAME].value
                desc_code = desc_row[ColumnIndexTow.CODE].value
                desc_phone = desc_row[ColumnIndexTow.CONTACT_PHONE].value

                # 判断条件一：客户名相同，或，历史单据客户名 + 联系方式等于当前单据的客户名
                check_bol_1 = company_name == desc_company_name or company_name == (desc_company_name  + phone)
                # 判断条件二：两个联系方式相同，或，身份证号码/企业统一信用号相同
                check_bol_2 = code == desc_code or phone == desc_phone

                # 条件一和条件二同时成立，就说明找到了旧单
                if check_bol_1 and check_bol_2:
                    # 前置设置续费客户旧单ID
                    row[ColumnIndexTow.OLD_CUSTOMER_ID].value = desc_row[ColumnIndexTow.CUSTOMER_ID].value

                    # 检查的合同类型，看看是否存在（N + M）的情况
                    if "(" in desc_member_type and ")" in desc_member_type:
                        # 存在，则视为已经手动调整为正确时间，所以当前单据不能再做延长
                        not_special = False
                    else :
                        # 找到旧单，且不是（N + M）模式，判断这个旧单符合哪种情况
                        # 获取旧单的服务顾问、法律顾问、旧单结束时间
                        desc_server_name = desc_row[ColumnIndexTow.SERVE_NAME].value
                        desc_law_name = desc_row[ColumnIndexTow.LAWERS].value
                        desc_end_date = desc_row[ColumnIndexTow.END_TIME].value
                        # 旧单的历史收款金额
                        desc_old_money_count = desc_row[ColumnIndexTow.OLD_MONEY_COUNT].value

                        # 判断条件一：判断旧单是否还存在两岗顾问之一
                        check_counselor_bol_1 = (desc_server_name and desc_law_name) or desc_server_name is not None or desc_law_name is not None
                        # 判断条件二：判断续费单是否未分配两岗顾问之一
                        check_counselor_bol_2 = not new_server_name or not new_law_name or new_server_name is None or new_law_name is None
                        # 判断条件三：判断旧单的结束时间是否没到期或已过期（其实这个判断可以忽略，并没有实际意义，属于之前过度思考结果）
                        check_time_bol = desc_end_date < datetime.now() or datetime.now() < desc_end_date

                        if check_counselor_bol_1 and check_counselor_bol_2 and check_time_bol:
                            # 三个条件同时成立，标紫
                            desc_row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color="9999FF", end_color="9999FF", fill_type="solid")
                        else :
                            # 不成立，标灰
                            desc_row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color="C0C0C0", end_color="C0C0C0", fill_type="solid")

                        # 这里通过正常的客户名称能找到，就不需要再去记录表中查找
                        not_special = True

                        # 将原单的历史金额合计，作为续费金额
                        row[ColumnIndexTow.RENEWAL].value += desc_old_money_count
                        # 重新计算历史合计
                        row[ColumnIndexTow.OLD_MONEY_COUNT].value += desc_old_money_count

                    #找到旧单后，终止这个旧单循环
                    break

            if not_special:
                return_old_receipt_data = None
                # 不是特殊合并情况，则正常处理结束时间
                if desc_end_date is None:
                    # 如果向上找不到旧单，其有可能是不录入系统的老套餐客户，需要从线下记录表中再检查
                    return_old_receipt_data = _check_old_receipt_data_list(old_receipt_data_list, company_name, accounting_date)
                    # 如果返回的是None，说明其不需要处理
                    if return_old_receipt_data is not None:
                        if '钻石' in return_old_receipt_data['旧单合同类型'] or '标准' in return_old_receipt_data['旧单合同类型']:
                            # 老客户不做处理，仅作标记
                            row[ColumnIndexTow.COMPANY_NAME].comment = Comment(f'客户名称：{return_old_receipt_data['旧单客户名称']}，'
                                                     f'\n签约类型：{return_old_receipt_data['旧单合同类型']}', 'LXY')
                        else :
                            # 有特殊记录的，根据这个特殊记录，重新向上查询
                            for desc_index in range(index, -1, -1):
                                # 避免自己匹配自己
                                if desc_index == index:
                                    continue

                                desc_row = row_list[desc_index]
                                # 同样只匹配会员
                                desc_member_type = desc_row[ColumnIndexTow.MEMBER_TYPE].value
                                if '会员' not in desc_member_type:
                                    continue

                                # 获取客户名称
                                desc_company_name = desc_row[ColumnIndexTow.COMPANY_NAME].value
                                # 获取到账时间
                                desc_accounting_date = desc_row[ColumnIndexTow.ACCOUNTING_TIME].value
                                # 旧单的历史收款金额
                                desc_old_money_count = desc_row[ColumnIndexTow.OLD_MONEY_COUNT].value

                                if (desc_company_name == return_old_receipt_data['旧单客户名称']
                                        and desc_accounting_date == return_old_receipt_data['旧单到账时间']) :
                                    # 获取旧单结束时间
                                    desc_end_date = desc_row[ColumnIndexTow.END_TIME].value
                                    # 并标灰
                                    desc_row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color="C0C0C0", end_color="C0C0C0", fill_type="solid")
                                    # 设置续费客户旧单ID
                                    row[ColumnIndexTow.OLD_CUSTOMER_ID].value = desc_row[ColumnIndexTow.CUSTOMER_ID].value

                                    # 将原单的历史金额合计，作为续费金额
                                    row[ColumnIndexTow.RENEWAL].value += desc_old_money_count
                                    # 重新计算历史合计
                                    row[ColumnIndexTow.OLD_MONEY_COUNT].value += desc_old_money_count

                                    # 终止循环
                                    break

                if desc_end_date is not None:
                    # 找到原单的结束时间，处理
                    if accounting_date > desc_end_date:
                        # 如果续费单的到账时间大于旧单的结束时间，属于区间外续费，正常按时间走
                        pass
                    else :
                        # 区间内续费，特殊调整
                        row[ColumnIndexTow.START_TIME].value = desc_end_date + timedelta(days=1)
                        row[ColumnIndexTow.END_TIME].value = _create_new_end_time(desc_end_date + timedelta(days=1), member_type)

                    # 设置批注
                    if return_old_receipt_data is not None:
                        # 旧单客户名称
                        desc_company_name = return_old_receipt_data['旧单客户名称']
                        # 旧单到账时间
                        desc_accounting_date = return_old_receipt_data['旧单到账时间']
                        # 旧单会员类型
                        desc_member_date = return_old_receipt_data['旧单合同类型']
                        # 设置批注
                        row[ColumnIndexTow.COMPANY_NAME].comment = Comment(f'旧单客户名称：{desc_company_name}\n，'
                                                 f'到账时间：{desc_accounting_date}\n，套餐类型：{desc_member_date}', 'LXY')

                    # 续费单，标绿
                    row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color="00ff00", end_color="00ff00", fill_type="solid")
                else :
                    if return_old_receipt_data is not None:
                        # 找到了旧单，根据旧单的类型设置颜色，旧套餐标橙色，新套餐标红色
                        row[ColumnIndexTow.COMPANY_NAME].comment = Comment(f'旧单名称：{return_old_receipt_data['旧单客户名称']}，'
                                                 f'签约时间：{return_old_receipt_data['旧单到账时间']}，'
                                                 f'签约类型：{return_old_receipt_data['旧单合同类型']}','LXY')

                        pattern_file = PatternFill(start_color="FF0000" if 'RED' == return_old_receipt_data['颜色'] else 'FF6600',
                                    end_color="FF0000" if 'RED' == return_old_receipt_data['颜色'] else 'FF6600',
                                    fill_type="solid")
                    else :
                        # 未找到原单，标红
                        row[ColumnIndexTow.COMPANY_NAME].comment = Comment('未找到旧单', 'LXY')
                        pattern_file = PatternFill(start_color="FF0000",
                                              end_color="FF0000",
                                              fill_type="solid")
                    row[ColumnIndexTow.COMPANY_NAME].fill = pattern_file

            else :
                # 特殊情况，这个续费单已被合并，标蓝灰色
                row[ColumnIndexTow.COMPANY_NAME].fill = PatternFill(start_color="666699", end_color="7393B3", fill_type="solid")

    # 返回workbook，后续程序就不再读取表格
    return workbook

"""
检查续费单的新旧客户名称匹配情况
"""
def _check_old_receipt_data_list(old_receipt_data_list, company_name, accounting_date):
    return_data = None
    for item in old_receipt_data_list:
        if item['续费单客户名称'] == company_name and item['续费单到账时间'] == accounting_date:
            return_data = item
            break

    return return_data

"""
生成新的合同结束时间
"""
def _create_new_end_time(start_date, member_type):
    # 判断需要添加的年限
    year_count = 1 if '一年' in member_type else 2 if '两年' in member_type else 4 if '(三+一)' in member_type else 3
    # 增加对应年限
    new_end_date = start_date + relativedelta(years=year_count)
    # 然后再减一日
    new_end_date = new_end_date - timedelta(days=1)

    return new_end_date

"""
校验退费客户
"""
def _check_return_price(company_name, accounting_date, return_price_customer_list):
    #进行标准化
    normalize_new_name = _normalize_company_name(company_name)

    return_data = None
    for item in return_price_customer_list:
        old_accounting_date = item['到账时间']
        # 进行标准化
        old_company_name = _normalize_company_name(item['客户名称'])

        # 匹配客户名称及到账时间
        if ((old_company_name in normalize_new_name or _check_company_name_string(normalize_new_name, old_company_name))
                and old_accounting_date == accounting_date):
            return_data = item
            break

    return return_data

"""
配合校验退费客户，因为表中的一些文字并不相同
"""
def _normalize_company_name(name):
    """标准化公司名称"""
    # 先进行NFKC标准化（兼容性分解）
    normalized = unicodedata.normalize('NFKC', name)
    return normalized

"""
辅助检查字符串的匹配程度
"""
def _check_company_name_string(new_string, old_string):
    set_new_string = set(new_string)
    set_old_string = set(old_string)
    intersection = set_new_string.intersection(set_old_string)
    union = set_new_string.union(set_old_string)
    return len(intersection) / len(union) * 100 > 70

"""
获取特殊客户表第一子表数据
"""
def _check_special_company_record_one_sheet(data_dir):
    workbook = load_workbook(f"{data_dir}/特殊客户表.xlsx")
    sheet = workbook['特殊续费客户']
    data_array = []
    for row in sheet.iter_rows(min_row=2):
        data_array.append({
            '客户id': row[0].value,
            '客户名称': row[1].value,
            '客户套餐类型': row[2].value,
            '客户合同开始时间': row[3].value,
            '客户合同结束时间': row[4].value,
            '客户加选最长结束时间': row[5].value,
            '颜色': row[6].value,
        })
    # 关流
    workbook.close()
    return data_array

"""
获取续费客户新旧单据数据
"""
def _get_old_receipt_data(data_dir):
    workbook = load_workbook(f"{data_dir}/客户信息表.xlsx")
    sheet = workbook['续费']
    data_array = []
    for row in sheet.iter_rows(min_row=3):
        if row[0].value is not None and row[14].value is not None:
            data_array.append({
                '续费单到账时间' : row[0].value,
                '旧单客户名称' : row[14].value,
                '续费单客户名称' : row[1].value,
                '旧单到账时间' : row[13].value,
                '旧单合同类型': row[15].value,
                '颜色' : 'RED' if '会员' in row[15].value else 'ORANGE'
            })
    # 关流
    workbook.close()
    return data_array

"""
获取退款客户数据
"""
def _get_return_price(data_dir):
    workbook = load_workbook(f"{data_dir}/退费客户表.xlsx")
    sheet = workbook['Sheet1']
    data_array = []
    for row in sheet.iter_rows(min_row=2):
        if row[1].value is not None and row[18].value in '终止服务':
            data_array.append({
                '客户名称' : row[7].value,
                '到账时间': row[1].value,
                '退款时间': row[16].value,
                '退款原因': row[19].value if row[19].value is not None else '缺失',
            })
    # 关流
    workbook.close()
    return data_array

"""
获取调解套餐升级客户信息
"""
def _get_mediate_to_member_customer(data_dir):
    workbook = load_workbook(f"{data_dir}/调解套餐升级会员单明细.xlsx")
    sheet = workbook['Sheet1']
    data_array = []
    for row in sheet.iter_rows(min_row=4):
        data_array.append({
            "调解名称" : row[1].value,
            "升级前收款金额": row[5].value,
            "调解到账时间": row[2].value,
            "会员名称": row[8].value,
        })
    # 关流
    workbook.close()
    return data_array

"""=======================优化程序1中对于数据获取的逻辑======================"""
"""
向外调用接口
"""
def _optimized_loop(customer_list, steward_list, counselor_log_list,
                        contract_list, service_record_list, sys_dict_data_map,
                        sys_user_map, sys_payee_data_map, customer_add_money_list, mediate_to_member_customer_list,
                         customer_lawsuit_init_count_list):
    """
    使用预处理数据的优化版本
    """
    # 预处理数据
    loggings_info("开始预处理数据")
    (
        steward_dict,
        counselor_dict,
        contract_dict,
        service_dict,
        add_money_dict,
        customer_upgrade_money_dict,
        customer_lawsuit_init_count_dict
    ) = _preprocess_all_data(
        steward_list, counselor_log_list, contract_list, service_record_list, customer_add_money_list, customer_lawsuit_init_count_list
    )

    # 结果集
    result = []

    # 获取最新的数据
    loggings_info("开始处理客户基本信息")
    for customer in tqdm(list(customer_list), desc="处理基本信息中......"):
        json_data = _process_customer_with_preprocessed_data(
            customer, steward_dict, counselor_dict, contract_dict, service_dict,
            sys_dict_data_map, sys_user_map, sys_payee_data_map, add_money_dict, customer_upgrade_money_dict, mediate_to_member_customer_list,
            customer_lawsuit_init_count_dict
        )
        result.append(json_data)

    return result

"""
对管家数据集，按账号ID分组
对分配记录、合同数据、交付记录，3个数据集按客户ID分组
将上述4个数据集转为字典格式数据
"""
def _preprocess_all_data(steward_list, counselor_log_list, contract_list, service_record_list, customer_add_money_list, customer_lawsuit_init_count_list):
    """
    预处理所有数据，创建查找字典
    """
    # 创建查找字典
    steward_dict = {steward.user_id: steward.nick_name for steward in steward_list}
    counselor_dict = {counselor.customer_id: counselor.create_time for counselor in counselor_log_list}

    # 按客户ID分组合同和服务记录
    contract_dict = {}
    for contract in contract_list[:]:  # 使用切片复制，避免修改原列表
        if contract.customerId not in contract_dict:
            contract_dict[contract.customerId] = []
        contract_dict[contract.customerId].append(contract)

    service_dict = {}
    for service_record in service_record_list[:]:
        if service_record.customer_id not in service_dict:
            service_dict[service_record.customer_id] = []
        service_dict[service_record.customer_id].append(service_record)

    # 过程中加选数据
    customer_add_money_dict = {}
    # 升级数据
    customer_upgrade_money_dict = {}
    # 数据处理
    for add_money in customer_add_money_list[:]:
        # 判断是否含有年限选项，如果含有年限选项，说明这是升级数据，单独存放
        if 'YEAR' in add_money['item_meal']:
            if add_money['customer_id'] not in customer_upgrade_money_dict:
                customer_upgrade_money_dict[add_money['customer_id']] = []

            # 设置加选数据
            customer_upgrade_money_dict[add_money['customer_id']].append(add_money)
        else :
            # 非升级，过程中加选
            if add_money['customer_id'] not in customer_add_money_dict:
                customer_add_money_dict[add_money['customer_id']] = []

            # 设置加选数据
            customer_add_money_dict[add_money['customer_id']].append(add_money)

    # 预处理客户立案初始次数
    customer_lawsuit_init_count_dict = {}
    for init_count_json in customer_lawsuit_init_count_list:
        if init_count_json['customer_id'] not in customer_lawsuit_init_count_dict:
            customer_lawsuit_init_count_dict[init_count_json['customer_id']] = []

        # 将客户的立案初始次数设置到字典
        customer_lawsuit_init_count_dict[init_count_json['customer_id']].append(init_count_json)

    return steward_dict, counselor_dict, contract_dict, service_dict, customer_add_money_dict, customer_upgrade_money_dict, customer_lawsuit_init_count_dict

"""
处理数据主体函数
"""
def _process_customer_with_preprocessed_data(customer, steward_dict, counselor_dict,
                                            contract_dict, service_dict,
                                            sys_dict_data_map, sys_user_map,
                                             sys_payee_data_map, add_money_dict,
                                             customer_upgrade_money_dict, mediate_to_member_customer_list,
                                             customer_lawsuit_init_count_dict):
    """
    使用预处理数据快速处理单个客户
    """
    # 基本信息
    customer.steward_name = steward_dict.get(customer.steward_id, "缺失")
    customer.industry_type = sys_dict_data_map.get(customer.industry_type, "其它")
    customer.payee_name_str = sys_payee_data_map.get(customer.payee_name, "缺失")

    json_data = {
        "id": customer.customer_id,
        "name": customer.company_name,
        "obj": customer,
        "afterTime": counselor_dict.get(customer.customer_id, "缺失")
    }

    contracts = contract_dict.get(customer.customer_id, [])
    if contracts:
        contract = contracts[0]  # 取第一个合同
        json_data.update({
            "startTime": contract.yearStartTime if contract.yearStartTime else contract.nonStartTime,
            "minEndTime": contract.yearEndTime,
            "maxEndTime": contract.nonEndTime,
            "itemMeal": _check_item_meal(contract.itemMeal, contract.thaliId)
        })

    # 处理服务记录
    services = service_dict.get(customer.customer_id, [])
    qsz = zdla = lsh = ckh = dbz = bq = qzzx = htws = 0
    customer_service_list = []

    for service_record in services:
        service_record.serve_id = sys_user_map.get(int(service_record.serve_id),
                                                   "缺失") if service_record.serve_id else "缺失"
        customer_service_list.append(service_record)

        # 统计服务类型
        count_result = _count_service_type(service_record.item_name, service_record.service_name)
        qsz += count_result["qsz"]
        zdla += count_result["zdla"]
        lsh += count_result["lsh"]
        ckh += count_result["ckh"]
        dbz += count_result["dbz"]
        bq += count_result["bq"]
        qzzx += count_result["qzzx"]
        htws += count_result["htws"]

    hj_count = qsz + zdla + lsh + ckh + dbz + bq + qzzx + htws

    json_data.update({
        "serviceList": customer_service_list,
        "qsz": qsz, "zdla": zdla, "lsh": lsh, "ckh": ckh,
        "dbz": dbz, "bq": bq, "qzzx": qzzx, "htws": htws,
        "hjCount": hj_count
    })

    # 处理加选金额数据
    if customer.customer_id in add_money_dict:
        customer_add_money_list = add_money_dict[customer.customer_id]
        add_money_count = 0
        for add_money in customer_add_money_list[:]:
            add_money_count += add_money['receive_money']

        json_data.update({
            "addMoneyCount": add_money_count
        })

    # 处理升级金额数据
    if customer.customer_id in customer_upgrade_money_dict:
        customer_upgrade_money_list = customer_upgrade_money_dict[customer.customer_id]
        customer_upgrade_money_count = 0
        for customer_upgrade_money in customer_upgrade_money_list[:]:
            customer_upgrade_money_count += customer_upgrade_money['receive_money']

        json_data.update({
            "upgradeMoneyCount": customer_upgrade_money_count
        })

    # 处理调解升级单，获取原单金额
    if '调解升级' in customer.company_name:
        mediate_to_member_money = 0
        for mediate_to_member in mediate_to_member_customer_list:
            if customer.company_name == mediate_to_member['会员名称']:
                mediate_to_member_money += mediate_to_member['升级前收款金额']

        # 使用升级会员相同的字段
        if "upgradeMoneyCount" in json_data:
            json_data['upgradeMoneyCount'] += mediate_to_member_money
        else :
            json_data['upgradeMoneyCount'] = mediate_to_member_money

    # 处理客户立案初始次数
    if customer.customer_id in customer_lawsuit_init_count_dict:
        # 获取集合
        customer_lawsuit_init_count_list = customer_lawsuit_init_count_dict[customer.customer_id]
        # 合计次数
        sum_count = 0
        for customer_lawsuit in customer_lawsuit_init_count_list:
            sum_count += customer_lawsuit['count']

        # 设置到返回集中
        json_data.update({
            "lawsuitCount": sum_count
        })

    return json_data

def _count_service_type(item_name, service_name):
    """统计服务类型（纯函数，可以并行化）"""
    result = {"qsz": 0, "zdla": 0, "lsh": 0, "ckh": 0, "dbz": 0, "bq": 0, "qzzx": 0, "htws": 0}

    if "指导立案" in item_name:
        result["zdla"] = 1
    elif "代写诉讼文书" in item_name:
        result["qsz"] = 1
    elif "律师函" in item_name:
        result["lsh"] = 1
    elif "合同起草与审核" in item_name:
        if "催款" in service_name or "催告" in service_name:
            result["ckh"] = 1
        elif "答辩" in service_name:
            result["dbz"] = 1
        elif "保全" in service_name:
            result["bq"] = 1
        elif "强执" in service_name or "强制执行" in service_name or "强制" in service_name:
            result["qzzx"] = 1
        else:
            result["htws"] = 1

    return result