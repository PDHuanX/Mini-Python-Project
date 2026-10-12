from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
from src.utils.dict_result import DictResult

"""获取指定时间内未分配管家的客户数据"""
def public_get_not_steward(data):
    result = QueryMysqlDatabase().get_not_steward_list(data['not_start_time'], data['not_end_time'])
    return DictResult.success_response(message="获取成功",status_code=200, types="get_not_steward_list", data=result)
