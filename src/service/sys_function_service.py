from src.utils.dict_result import DictResult
from src.mapper.local.local_db_query_impl import LocalMysqlDatabase as LocalQueryMysqlDatabase
from src.mapper.local.local_db_insert_impl import LocalMysqlDatabase as LocalInsertMysqlDatabase
from src.mapper.local.local_db_update_impl import LocalMysqlDatabase as LocalUpdateMysqlDatabase

def public_update_function(view_data):
    return _update_function_list(view_data)

def _update_function_list(view_data):
    LocalUpdateMysqlDatabase().update_function(view_data)
    return DictResult.success_response(
        message="修改函数成功",
        status_code=200,
        types="update_function",
        data=None
    )

def public_add_function(view_data):
    return _add_function(view_data)

def _add_function(view_data):
    LocalInsertMysqlDatabase().add_function(view_data)
    return DictResult.success_response(
        message="新增函数成功",
        status_code=200,
        types="add_function",
        data=None
    )

def public_get_fun_list(view_data):
    return _get_fun_list(view_data)

def _get_fun_list(view_data):
    result = LocalQueryMysqlDatabase().query_fun_list()
    return DictResult.success_response(
        message="获取函数列表成功",
        status_code=200,
        types="get_fun_list",
        context=view_data["context"] if "context" in view_data else None,
        data=result
    )