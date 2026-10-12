import datetime

from openpyxl.reader.excel import load_workbook
from tqdm import tqdm

from src.entity.insert_dao import Customer
from src.mapper.online.db_insert_impl import MysqlDatabase as InsertMysqlDatabase
from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
from src.utils import paths_utils as paths
from src.utils.dict_result import DictResult
from src.utils.logging_utils import loggings_info, loggings_error

"""提供一个对外统一接口"""
def public_batch_insert(data):
    return _batch_insert_customer(data)

"""提供一个对外统一接口"""
def public_get_user_list():
    return _get_user_list()

"""
获取服务顾问和法律顾问，这里是个总集
"""
def _get_user_list():
    sys_user_list = QueryMysqlDatabase().query_law_server_sys_user_list_during([3, 4, 15])

    result = [{"user_id": sysUser.user_id,
               "user_name": sysUser.user_name,
               "nick_name": sysUser.nick_name,
               "role_name": "法律顾问" if sysUser.role_id == 3 else "服务顾问" if sysUser.role_id == 4 else "合同顾问"} for sysUser in sys_user_list]

    return DictResult.success_response(status_code= 200, message="获取顾问集合成功", types="get_user_list", data=result)

"""
将批量导入作为可选功能开放，需要先解决顾问id的问题，目前方案是将顾问的姓名及相应id向外开放
查到相应的数据后，交由页面进行处理
"""
def _batch_insert_customer(data):
    # 获取目录
    data_dir = paths.get_resource_path("resources/insert_customer_excel_templates")

    # 获取前端选择的两岗顾问信息，将其合成一个字典
    user_dict = {**data["law"], **data["server"]}
    # 然后倒因为果（暂时不考虑重名问题）
    user_dict = { val: key for key, val in user_dict.items()}

    # 读取对应的文件
    loggings_info(f"开始读取导入文件{data['fileName']}.xlsx")
    workbook = load_workbook(f"{data_dir}/{data['fileName']}.xlsx")
    if "客户列表" in workbook.sheetnames:
        sheet = workbook['客户列表']
    else :
        sheet = workbook['Sheet1']
    loggings_info(f"读取导入文件{data['fileName']}.xlsx结束")

    # 获取对应数据
    contract_data_dict = {}
    insert_data_list = []
    source_data_list = list(sheet.iter_rows(min_row=2, max_row=sheet.max_row))
    for row in tqdm(source_data_list, desc="获取客户基础信息......"):
        # 获取序号，以此为是否存在数据标准
        index = row[0].value
        if index is None:
            continue

        # 先获取法律顾问列，这里需要拼接成json字符串
        law = row[13].value

        law_json_str = []
        if law:
            law_json_str = [
                {
                    # 这里要转成数值id，字符串的话提需求后对应法律顾问可能无法获取相关的需求
                    "lawId": int(user_dict[law]),
                    "lawName": law,
                }
            ]

        customer = Customer(
            # 到账时间
            accounting_date= row[1].value,
            # 分公司
            salesman_company = data['salesmanCompany'],
            # 销售
            salesman_name = row[4].value,
            # 到账金额
            receive_money = row[5].value,
            # 客户名称
            company_name = row[6].value,
            # 统一信用代码或身份证号
            code = row[7].value,
            # 联系人
            contact = row[8].value,
            # 联系方式
            contact_phone = row[9].value,
            # 关联人、关联企业
            associated_person = row[10].value if row[10].value else "暂无",
            # 是否是续费
            is_renewal = 1 if row[11].value and row[11].value == "是" else 0,
            # 是否建群
            is_group = 1 if row[12].value and row[12].value == "是" else 0,
            # 法律顾问
            lawers = law_json_str,
            # 服务顾问
            serve_name = row[14].value,
            # 服务顾问id
            serve_id = int(user_dict[row[14].value]) if row[14].value else None,
            # 合同顾问ID
            consultant_id = int(user_dict[row[15].value]) if row[15].value else None,
            # 合同顾问
            consultant_name = row[15].value,
            # 备注
            remark = row[17].value,
            # 合同开始时间
            start_time = row[18].value,
            # 合同结束时间
            end_time = row[19].value,
            # 行业类型，统一为其它
            industry_type = "OTHER",
            # 客服顾问，统一设置为测试账号
            steward_id = 1272,
            steward_name = "测试账号-债权",
            # 财务、质检审批，统一为OK
            finance_audit = "OK",
            quality_audit = "OK",
            # 是否是会员，统一为是
            is_item = "1",
            # 分公司名称，取前端填写数据
            performance_company = row[3].value,
            item_name = row[20].value,
            audit_pass_time = datetime.datetime.now(),
            fill_time = datetime.datetime.now()
        )

        # 新增到集合中
        insert_data_list.append(customer)

        # 获取合同类型及相关加选信息，后边要用到
        contract_data_dict[row[6].value] = {
            "server_contract": row[20].value,
            "add_server_contract": row[21].value
        }

    # 进行新增，返回的集合是新增客户的id及客户名称，用于后续处理合同
    result = list(InsertMysqlDatabase().batch_insert_customer(insert_data_list))
    # 合同内容集合，用于后续新增
    customer_contract_list = []
    for res in tqdm(result, desc="处理客户合同内容........"):
        # 获取当前客户的合同及加选内容
        contract_content_dict = contract_data_dict[res['company_name']]

        # 先看会员内容，根据其文本获取对应年限的会员信息
        server_contract = contract_content_dict['server_contract']
        # 这里分出几个逻辑
        if '会员' in server_contract:
            # 处理会员内容
            _check_create_server(res=res, server_contract=server_contract,
                                 customer_contract_list=customer_contract_list)

            # 再看加选内容
            add_server_contract = contract_content_dict['add_server_contract']

            if add_server_contract:
                # 如果存在加选，首先看一下关键符号，如顿号，中文分号这两种，形成一个集合
                if "、" in add_server_contract:
                    add_content = add_server_contract.split("、")
                elif "；" in add_server_contract:
                    add_content = add_server_contract.split("；")
                elif ";" in add_server_contract:
                    add_content = add_server_contract.split(";")
                elif "," in add_server_contract:
                    add_content = add_server_contract.split(",")
                else:
                    add_content = add_server_contract.split("，")

                # 能拆分为一个集合，循环处理
                if add_content:
                    for content in add_content:
                        # 然后看一下加选次数
                        content_count = None
                        if "*" in content:
                            content_count = content.split("*")

                        # 处理加选内容
                        _check_create_add_server(
                            res = res,
                            add_server_contract = content_count[0] if content_count and len(
                                content_count) >= 1 else content,
                            customer_contract_list = customer_contract_list,
                            init_count = content_count[1] if content_count and len(content_count) >= 2 else 1
                        )

        elif '回购' in server_contract:
            # 回购的，使用加配字段作为数据源
            add_server_contract = contract_content_dict['add_server_contract']

            if add_server_contract:
                # 跟加选同理，首先看一下关键符号，如顿号，中文分号这两种，形成一个集合
                if "、" in add_server_contract:
                    add_content = add_server_contract.split("、")
                else:
                    add_content = add_server_contract.split("；")

                # 能拆分为一个集合，循环处理
                if add_content:
                    for content in add_content:
                        # 然后看一下加选次数
                        content_count = None
                        if "*" in content:
                            content_count = content.split("*")

                        # 处理回购内容
                        _check_create_buy_back(
                                res = res,
                                add_server_contract = content_count[0] if content_count and len(content_count) >= 1 else content,
                                customer_contract_list = customer_contract_list,
                                init_count = content_count[1] if content_count and len(content_count) >= 2 else 1
                        )

        # 做完合同处理后，还需要处理新增合同及修改customer表的使用次数（OK_NUM）和未使用次数（NO_NUM）
        no_num = 0
        for contract in customer_contract_list:
            # 获取count，求和，得到NO_NUM
            if contract['customer_id'] == res['customer_id']:
                no_num += int(contract['count'])

        res['ok_num'] = 0
        res['no_num'] = no_num

    # 先新增合同内容，让合同内容先落库
    InsertMysqlDatabase().batch_insert_contract(customer_contract_list)

    # 最后执行修改主表操作
    InsertMysqlDatabase().batch_update_customer(result)

    return DictResult.success_response(
        message=f"新增{len(insert_data_list)}条{data['salesmanCompany']}客户成功",
        status_code=200,
        types="batch_insert_customer",
        data= None
    )

"""处理回购，该函数不处理业务逻辑，只设置对应参数，业务逻辑如选配多笔等，放到外层调用时处理"""
def _check_create_buy_back(res, add_server_contract, customer_contract_list, init_count):
    index = 0

    if "合同文书" in add_server_contract or "合同起草与审核" in add_server_contract:
        # 设置基本信息
        contract = {
            "customer_id": res['customer_id'],
            "lawers": res['lawers'],
            "serve_id": res['serve_id'],
            "start_time": res['start_time'],
            "end_time": res['end_time'],
            "item_id": 52,
            "item_name": "合同起草与审核",
            "item_meal": "REPO",
            "item_type": "RADIO",
            "count": init_count,
            "residue_count": init_count,
            "item_count": init_count,
            "init_item_count": init_count,
            "price": 200,
            "item_price": 200 * int(init_count)
        }
        # 新增合同内容
        customer_contract_list.append(contract)
    else:
        while index < 2:
            # 设置基本信息
            contract = {
                "customer_id": res['customer_id'],
                "lawers": res['lawers'],
                "serve_id": res['serve_id'],
                "start_time": res['start_time'],
                "end_time" : res['end_time'],
            }

            # 分支处理
            match add_server_contract:
                case "1000立案" | "10以内立案" | "立案1000":
                    match index:
                        case 0:
                            contract['item_id'] = 53
                            contract['item_name'] = "指导立案（单笔10万标的内）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 1000
                            contract['item_price'] = 1000
                        case 1:
                            contract['item_id'] = 54
                            contract['item_name'] = "指导立案（单笔10万标的内）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 1000
                            contract['item_price'] = 1000

                case "1500立案" | "10-30立案" | "立案1500":
                    match index:
                        case 0:
                            contract['item_id'] = 55
                            contract['item_name'] = "指导立案（单笔标的额10万-30万内）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 1500
                            contract['item_price'] = 1500
                        case 1:
                            contract['item_id'] = 56
                            contract['item_name'] = "代写诉讼文书（单笔标的额10万-30万内）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 1500
                            contract['item_price'] = 1500

                case "2000立案" | "30-50立案" | "立案2000":
                    match index:
                        case 0:
                            contract['item_id'] = 57
                            contract['item_name'] = "指导立案（单笔标的额30万-50万内）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 2000
                            contract['item_price'] = 2000
                        case 1:
                            contract['item_id'] = 58
                            contract['item_name'] = "代写诉讼文书（单笔标的额30万-50万内）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 2000
                            contract['item_price'] = 2000

                case "3000立案" | "50-100立案" | "立案3000":
                    match index:
                        case 0:
                            contract['item_id'] = 59
                            contract['item_name'] = "指导立案（单笔标的额50万-100万内）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 3000
                            contract['item_price'] = 3000
                        case 1:
                            contract['item_id'] = 60
                            contract['item_name'] = "代写诉讼文书（单笔标的额50万-100万内）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 3000
                            contract['item_price'] = 3000

                case "5000立案" | "100以上立案" | "立案5000":
                    match index:
                        case 0:
                            contract['item_id'] = 61
                            contract['item_name'] = "指导立案（单笔标的额100万以上）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 5000
                            contract['item_price'] = 5000
                        case 1:
                            contract['item_id'] = 62
                            contract['item_name'] = "代写诉讼文书（单笔标的额100万以上）"
                            contract['item_meal'] = "REPO"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 5000
                            contract['item_price'] = 5000


            # 自增，防止死循环
            index += 1

            # 新增合同内容
            customer_contract_list.append(contract)


"""处理加选内容，该函数不处理业务逻辑，只设置对应参数，业务逻辑如选配多笔等，放到外层调用时处理"""
def _check_create_add_server(res, add_server_contract, customer_contract_list, init_count):
    index = 0

    if "合同文书" in add_server_contract or "合同起草与审核" in add_server_contract:
        # 设置基本信息
        contract = {
            "customer_id": res['customer_id'],
            "lawers": res['lawers'],
            "serve_id": res['serve_id'],
            "start_time": res['start_time'],
            "end_time": res['end_time'],
            "item_id": 23,
            "item_name": "合同起草与审核",
            "item_meal": "NON",
            "item_type": "RADIO",
            "count": init_count,
            "residue_count": init_count,
            "item_count": init_count,
            "init_item_count": init_count,
            "price": 200,
            "item_price": 200 * int(init_count)
        }
        # 新增合同内容
        customer_contract_list.append(contract)
    else :
        while index < 2:
            # 设置基本信息
            contract = {
                "customer_id": res['customer_id'],
                "lawers": res['lawers'],
                "serve_id": res['serve_id'],
                "start_time": res['start_time'],
                "end_time": res['end_time'],
            }

            # 分支处理
            match add_server_contract:
                case "1000立案" | "10以内立案" | "立案1000":
                    match index:
                        case 0:
                            contract['item_id'] = 20
                            contract['item_name'] = "指导立案（单笔10万标的内）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 1000
                            contract['item_price'] = 1000
                        case 1:
                            contract['item_id'] = 26
                            contract['item_name'] = "代写诉讼文书（单笔10万标的内）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 1000
                            contract['item_price'] = 1000

                case "1500立案" | "10-30立案" | "立案1500":
                    match index:
                        case 0:
                            contract['item_id'] = 21
                            contract['item_name'] = "指导立案（单笔10-30万标的）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 1500
                            contract['item_price'] = 1500
                        case 1:
                            contract['item_id'] = 34
                            contract['item_name'] = "代写诉讼文书（单笔10-30万标的）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 1500
                            contract['item_price'] = 1500

                case "2000立案" | "30-50立案" | "立案2000":
                    match index:
                        case 0:
                            contract['item_id'] = 22
                            contract['item_name'] = "指导立案（单笔30-50万标的）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 2000
                            contract['item_price'] = 2000
                        case 1:
                            contract['item_id'] = 35
                            contract['item_name'] = "代写诉讼文书（单笔30-50万标的）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 2000
                            contract['item_price'] = 2000

                case "3000立案" | "50-100立案" | "立案3000":
                    match index:
                        case 0:
                            contract['item_id'] = 28
                            contract['item_name'] = "指导立案（单笔50-100万标的）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 3000
                            contract['item_price'] = 3000
                        case 1:
                            contract['item_id'] = 36
                            contract['item_name'] = "代写诉讼文书（单笔50-100万标的）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 3000
                            contract['item_price'] = 3000

                case "5000立案" | "100以上立案" | "立案5000":
                    match index:
                        case 0:
                            contract['item_id'] = 29
                            contract['item_name'] = "指导立案（单笔100万以上标的）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 5000
                            contract['item_price'] = 5000
                        case 1:
                            contract['item_id'] = 37
                            contract['item_name'] = "代写诉讼文书（单笔100万以上标的）"
                            contract['item_meal'] = "NON"
                            contract['item_type'] = "RADIO"
                            contract['count'] = init_count
                            contract['residue_count'] = init_count
                            contract['item_count'] = init_count
                            contract['init_item_count'] = init_count
                            contract['price'] = 5000
                            contract['item_price'] = 5000

            # 自增，防止死循环
            index += 1

            # 新增合同内容
            customer_contract_list.append(contract)

"""处理会员套餐内容"""
def _check_create_server(res, server_contract, customer_contract_list):
    index = 0
    while index < 3:
        # 设置基本信息
        contract = {
            "customer_id": res['customer_id'],
            "lawers": res['lawers'],
            "serve_id": res['serve_id'],
            "start_time": res['start_time'],
            "end_time": res['end_time'],
        }

        # 分支处理
        match server_contract:
            case "一年会员":
                match index:
                    case 0:
                        contract['item_id'] = 2
                        contract['item_name'] = "指导立案（单笔10万标的内）"
                        contract['item_meal'] = "ONEYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 2
                        contract['residue_count'] = 2
                        contract['item_count'] = 2
                        contract['init_item_count'] = 2
                        contract['price'] = 1750
                        contract['item_price'] = 1750
                    case 1:
                        contract['item_id'] = 3
                        contract['item_name'] = "代写诉讼文书（单笔10万标的内）"
                        contract['item_meal'] = "ONEYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 2
                        contract['residue_count'] = 2
                        contract['item_count'] = 2
                        contract['init_item_count'] = 2
                        contract['price'] = 1750
                        contract['item_price'] = 1750
                    case 2:
                        contract['item_id'] = 4
                        contract['item_name'] = "合同起草与审核"
                        contract['item_meal'] = "ONEYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 10
                        contract['residue_count'] = 10
                        contract['item_count'] = 10
                        contract['init_item_count'] = 10
                        contract['price'] = 1000
                        contract['item_price'] = 1000
            case "两年会员":
                match index:
                    case 0:
                        contract['item_id'] = 8
                        contract['item_name'] = "指导立案（单笔10万标的内）"
                        contract['item_meal'] = "TWOYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 5
                        contract['residue_count'] = 5
                        contract['item_count'] = 5
                        contract['init_item_count'] = 5
                        contract['price'] = 2000
                        contract['item_price'] = 2000
                    case 1:
                        contract['item_id'] = 9
                        contract['item_name'] = "代写诉讼文书（单笔10万标的内）"
                        contract['item_meal'] = "TWOYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 5
                        contract['residue_count'] = 5
                        contract['item_count'] = 5
                        contract['init_item_count'] = 5
                        contract['price'] = 2000
                        contract['item_price'] = 2000
                    case 2:
                        contract['item_id'] = 10
                        contract['item_name'] = "合同起草与审核"
                        contract['item_meal'] = "TWOYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 20
                        contract['residue_count'] = 20
                        contract['item_count'] = 20
                        contract['init_item_count'] = 20
                        contract['price'] = 2000
                        contract['item_price'] = 2000
            case "三年会员":
                match index:
                    case 0:
                        contract['item_id'] = 14
                        contract['item_name'] = "指导立案（单笔10万标的内）"
                        contract['item_meal'] = "THREEYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 8
                        contract['residue_count'] = 8
                        contract['item_count'] = 8
                        contract['init_item_count'] = 8
                        contract['price'] = 3000
                        contract['item_price'] = 3000
                    case 1:
                        contract['item_id'] = 15
                        contract['item_name'] = "代写诉讼文书（单笔10万标的内）"
                        contract['item_meal'] = "THREEYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 8
                        contract['residue_count'] = 8
                        contract['item_count'] = 8
                        contract['init_item_count'] = 8
                        contract['price'] = 3000
                        contract['item_price'] = 3000
                    case 2:
                        contract['item_id'] = 16
                        contract['item_name'] = "合同起草与审核"
                        contract['item_meal'] = "THREEYEAR"
                        contract['item_type'] = "SERIES"
                        contract['count'] = 30
                        contract['residue_count'] = 30
                        contract['item_count'] = 30
                        contract['init_item_count'] = 30
                        contract['price'] = 2000
                        contract['item_price'] = 2000

        # 自增，防止死循环
        index += 1

        # 新增合同内容
        customer_contract_list.append(contract)