import datetime
import requests
import src.utils.paths_utils as paths_utils
from src.utils.dict_result import DictResult
from openpyxl import Workbook

def public_get_register_data():
    return _get_register_data()

def _get_register_data():
    # 项目登陆api，主要为了获取token，保证后续的api能正常访问
    java_login_url = "https://fawu.gxfywzx.com/prod-api/admin/login"
    credentials = {
        "username": "",
        "password": ""
    }
    response = requests.post(java_login_url, json= credentials)
    token = "Bearer " + response.json().get("token")

    # 组装请求头
    headers = {
        "Authorization": token
    }
    # 请求API
    # api_url = "https://fawu.gxfywzx.com/prod-api/admin/register/list?pageNum=1&pageSize=1000&remainingTime=0"
    api_url = "https://fawu.gxfywzx.com/prod-api/admin/register/list"
    params = {
        'pageNum': 1,
        'pageSize': 1000,
        # 'serveIds': [736]
        'remainingTime': 0
    }
    response = requests.get(api_url, headers= headers, params= params)
    # 获取json中的rows数据，这就是目标数据
    register_list = response.json().get('rows')

    # 获取文件路径
    data_sir = paths_utils.get_resource_path('resources/public_excel')

    # 创建新表
    new_workbook = Workbook()
    # 获取表格
    new_sheet = new_workbook['Sheet']
    # 设置表头
    new_sheet.append([
        '序号', '当前服务节点', '城市', '客户名称', '法律顾问',
        '服务顾问', '服务名称', '需求名称', '当事人A', '当事人B',
        '需求提单通过日期', '剩余跟进天数'
    ])

    # 循环核心数据，组成行数据
    for index, register_data in enumerate(register_list):
        new_sheet.append([
            index + 1,
            register_data['currentServiceName'],
            register_data['performanceName'],
            register_data['companyName'],
            register_data['lawers'],
            register_data['serveName'],
            register_data['serviceName'],
            register_data['needName'],
            register_data['clienta'],
            register_data['clientb'],
            register_data['passDate'],
            register_data['remainingTime']
        ])

    # 保存表格
    new_workbook.save(f'{data_sir}/{format(datetime.datetime.today(), '%Y%m%d')}立案剩余跟进0天数据.xlsx')

    return DictResult.success_response(
        message=f"获取成功，共{len(register_list)}条数据，请前往【resources/public_excel】文件夹查看",
        status_code=200,
        types="submit_get_register_day_zero_data",
        data=None
    )

if __name__ == '__main__':
    public_get_register_data()