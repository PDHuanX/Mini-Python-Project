import datetime

from openpyxl import Workbook

from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
from src.utils.dict_result import DictResult
from src.utils.paths_utils import get_resource_path

"""对外函数"""
def public_get_salesman_delivery_main(data):
    if data['select_type'] == 'year':
        return _get_salesman_delivery_year(data)
    else :
        return _get_salesman_delivery_month(data)

"""业务函数，获取分公司交付数据，年度"""
def _get_salesman_delivery_year(data):
    # 获取分公司交付数据
    delivery_result = QueryMysqlDatabase().get_salesman_delivery(data['start_time'], data['end_time'])
    # 使用推导式预处理数据，减少后续时间消耗
    delivery_dit = {}
    for delivery in delivery_result[:]:
        if delivery['salesman_company'] not in delivery_dit:
            delivery_dit[delivery['salesman_company']] = []
        delivery_dit[delivery['salesman_company']].append(delivery)

    # 获取分公司字典
    salesman_dict = _salesman_dict()

    # 最终结果
    final_result = {}
    for key, value in salesman_dict.items():
        # 总数
        count = 0
        # 拆分
        salesman_list = value.split(",")
        for salesman in salesman_list:
            if salesman in delivery_dit:
                delivery_list = delivery_dit[salesman]
                count += len(delivery_list)

        # 求和完成后，设置
        final_result[key] = count

    # 创建表格
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "分公司年度交付数据"

    # 创建表头
    headers = ["", "年度交付总数"]
    sheet.append(headers)

    # 推导式形成数据集
    table_data = [
        [
            key,
            value
        ] for key, value in final_result.items()
    ]
    # 设置数据
    for row in table_data:
        sheet.append(row)

    # 添加末行求和
    end_row = ["合计", f"=SUM(B2:B{sheet.max_row})"]
    sheet.append(end_row)

    # 输出
    out_url = get_resource_path("resources/salesman_excel")
    workbook.save(f"{out_url}/分公司年度交付数据{datetime.datetime.today()}.xlsx")

    return DictResult.success_response(
        message="已获取完毕，请前往【resources/salesman_excel】文件夹下查看",
        status_code=200,
        types="get_salesman_delivery",
        data=None
    )

"""业务函数，获取分公司交付数据，月度"""
def _get_salesman_delivery_month(data):
    # 获取分公司交付数据
    delivery_result = QueryMysqlDatabase().get_salesman_delivery(data['start_time'], data['end_time'])
    # 使用推导式预处理数据，减少后续时间消耗
    delivery_dit = {}
    for delivery in delivery_result[:]:
        if delivery['salesman_company'] not in delivery_dit:
            delivery_dit[delivery['salesman_company']] = []
        delivery_dit[delivery['salesman_company']].append(delivery)

    # 获取分公司字典
    salesman_dict = _salesman_dict()

    # 最终结果
    final_result = {}
    # 处理分公司数据
    for key, value in salesman_dict.items():
        # 初始变量，依次为：起诉状、上诉状、劳动仲裁、商事仲裁
        BOP = PFA = ALA = ACA = 0
        # 网立、仲裁立案
        OF = AF = 0
        # 合同起草、合同审核、催款函、财保、强执、答辩状、律师函
        CD = CR = CL = PPA = CEA = PD = LL = 0
        # 拆分
        salesman_list = value.split(",")
        # 循环分公司
        for salesman in salesman_list:
            # 因为数据集已经预处理，所以可以按照分公司直接获取
            if salesman in delivery_dit:
                # 直接获取后，循环
                delivery_list = delivery_dit[salesman]
                for delivery in delivery_list:
                    # 这里只判断secondary_name
                    if delivery["secondary_name"]:
                        match delivery["secondary_name"]:
                            case "BOP":
                                # 起诉状
                                BOP += 1
                            case "PFA":
                                # 上诉状
                                PFA += 1
                            case "ALA":
                                # 劳动仲裁
                                ALA += 1
                            case "ACA":
                                # 商事仲裁
                                ACA += 1
                            case "OF":
                                # 网立
                                OF += 1
                            case "AF":
                                # 仲裁立案
                                AF += 1
                            case "CD" | "CD3":
                                # 合同起草
                                CD += 1
                            case "CR":
                                # 合同审核
                                CR += 1
                            case "CL" | "PD3":
                                # 催款函
                                CL += 1
                            case "PPA":
                                # 财保
                                PPA += 1
                            case "CEA" | "CEA3":
                                # 强执
                                CEA += 1
                            case "PD":
                                # 答辩状
                                PD += 1
                            case "LL":
                                # 律师函
                                LL += 1

        final_result[key] = {
            "起诉状" : (BOP + PFA + ALA + ACA),
            "立案": (OF + AF),
            "合同起草": CD,
            "合同审核": CR,
            "催款函": CL,
            "财产保全文书": PPA,
            "强制执行文书": CEA,
            "答辩状": PD,
            "律师函": LL,
            "合计": (BOP + PFA + ALA + ACA + OF + AF + CD + CR + CL + PPA + CEA + PD + LL),
        }

    # 创建表格
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "分公司数据明细"

    # 创建表头
    headers = ["", "起诉状", "立案", "合同起草", "合同审核", "催款函", "财产保全文书", "强制执行文书", "答辩状", "律师函", "合计"]
    sheet.append(headers)
    # 推导式形成数据集
    table_data = [
        [
            key,
            value['起诉状'],
            value['立案'],
            value['合同起草'],
            value['合同审核'],
            value['催款函'],
            value['财产保全文书'],
            value['强制执行文书'],
            value['答辩状'],
            value['律师函'],
            value['合计']
        ] for key, value in final_result.items()
    ]
    # 设置数据
    for row in table_data:
        sheet.append(row)

    # 添加末行求和
    end_row = ["合计",
               f"=SUM(B2:B{sheet.max_row})",
               f"=SUM(C2:C{sheet.max_row})",
               f"=SUM(D2:D{sheet.max_row})",
               f"=SUM(E2:E{sheet.max_row})",
               f"=SUM(F2:F{sheet.max_row})",
               f"=SUM(G2:G{sheet.max_row})",
               f"=SUM(H2:H{sheet.max_row})",
               f"=SUM(I2:I{sheet.max_row})",
               f"=SUM(J2:J{sheet.max_row})",
               f"=SUM(K2:K{sheet.max_row})",]
    sheet.append(end_row)

    # 输出
    out_url = get_resource_path("resources/salesman_excel")
    workbook.save(f"{out_url}/分公司月度交付数据{datetime.datetime.today()}.xlsx")

    return DictResult.success_response(
        message="已获取完毕，请前往【resources/salesman_excel】文件夹下查看",
        status_code=200,
        types="get_salesman_delivery",
        data=None
    )

"""分公司集合，本来想过使用json文件，但是非专业知识的人员维护较难，所以干脆写死"""
def _salesman_dict():
    return {
        "南宁": "南宁分公司,南宁第二分公司",
        "柳州1": "柳州分公司,柳州第一分公司",
        "崇左": "崇左分公司",
        "青秀1": "青秀第一分公司",
        "钦州": "钦州分公司",
        "贺州": "贺州分公司",
        "来宾": "来宾分公司",
        "平南": "平南分公司",
        "玉林": "玉林分公司",
        "梧州": "梧州分公司",
        "贵港1": "贵港分公司,贵港第一分公司",
        "贵港2": "贵港第二分公司",
        "桂林": "桂林分公司,桂林第一分公司,桂林第二分公司,灵川（桂林）",
        "北海": "北海分公司,北海第一分公司,北海第二分公司",
        "防城港": "防城港分公司",
        "青秀2": "青秀第二分公司",
        "云浮": "广东云浮分公司,罗定门店",
        "河池2": "河池宜州分公司,河池第二分公司",
        "柳州2": "柳州第二分公司",
    }