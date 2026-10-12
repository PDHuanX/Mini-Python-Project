from src.service.get_law_during_service import public_get_law_during_data
from src.service.get_law_out_service import public_get_law_out_date_data
from src.service.get_server_during_service import public_get_server_during_data
from src.service.get_server_out_service import public_get_server_out_date_data
from src.utils.dict_result import DictResult

"""
因为只是将四个分散的功能合并成一个，所以直接分开调用其余4个函数即可
"""
def public_get_two_job_during_and_out_customer(view_data):
    # 因为是统合参数，需要变更为4个函数需要的入参，这里偷懒，后续也基本不会再动
    public_data = {
        # 获取法律顾问在期客户所需
        "deadlineLaw": view_data['twoJobDeadlineDuring'],
        "lawStr": view_data['towJobLaw'],
        "sourceDataFileNameLaw": view_data['towJobDataSource'],
        # 获取法律顾问过期客户所需
        "lawStrOut": view_data["towJobLaw"],
        "deadlineLawOut": view_data["twoJobDeadlineOut"],
        "sourceDataFileNameLawOut": view_data["towJobDataSource"],
        # 获取服务顾问在期客户所需
        "deadline" : view_data["twoJobDeadlineDuring"],
        "serverStr": view_data["twoJobServer"],
        "sourceDataFileNameServer": view_data["towJobDataSource"],
        # 获取服务顾问过期客户所需
        "serverStrOut": view_data["twoJobServer"],
        "deadlineServerOut": view_data["twoJobDeadlineOut"],
        "sourceDataFileNameServerOut": view_data["towJobDataSource"]
    }

    # 获取法律顾问在期客户
    public_get_law_during_data(public_data)
    # 获取法律顾问过期客户
    public_get_law_out_date_data(public_data)
    # 获取服务顾问在期客户
    public_get_server_during_data(public_data)
    # 获取服务顾问过期客户
    public_get_server_out_date_data(public_data)

    return DictResult.success_response(
        message="获取成功，请前往相应文件夹查看",
        status_code=200,
        types="submit_get_two_job_during_and_out_customer_data",
        data=None
    )