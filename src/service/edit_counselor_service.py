import requests
from src.utils.dict_result import DictResult

def public_edit_counselor_service():
    return _edit_counselor_service()

def _edit_counselor_service():
    # 项目登陆api，主要为了获取token，保证后续的api能正常访问
    java_login_url = "https://fawu.gxfywzx.com/prod-api/admin/login"
    credentials = {
        "username": "",
        "password": ""
    }
    response = requests.post(java_login_url, json=credentials)
    token = "Bearer " + response.json().get("token")

    # 组装请求头
    headers = {
        "Authorization": token,
        "Content-Type": "application/json;charset=utf-8"
    }

    # 请求API
    api_url = "https://fawu.gxfywzx.com/prod-api/admin/customer/editCounselor"

    # 法律顾问
    # params = {
    #     'customerIds': [
    #
    #     ],
    #     'isLawer': '1', # 置空改为0
    #     'lawersVOS': [
    #         {
    #             'lawId': None,
    #             'lawName': None,
    #         }
    #     ]
    # }

    # 服务顾问
    params = {
        'customerIds': [
        ],
        'isServe': '1',
        'serveId': None,
        'serveName': None
    }

    # 客服管家
    # params = {
    #     'customerIds': [
    #     ],
    #     'isSteward': '1',
    #     'stewardId': None,
    #     'stewardName': None
    # }

    response = requests.post(api_url, headers=headers, json=params)
    return DictResult.success_response(message= response.json(), status_code= response.status_code, types= "edit_counselor_service", data= None)

if __name__ == '__main__':
    public_edit_counselor_service()