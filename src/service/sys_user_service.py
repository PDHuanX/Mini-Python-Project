from src.utils.dict_result import DictResult
from src.mapper.local.local_db_query_impl import LocalMysqlDatabase as LocalQueryMysqlDatabase
from src.mapper.local.local_db_insert_impl import LocalMysqlDatabase as LocalInsertMysqlDatabase
from src.mapper.local.local_db_update_impl import LocalMysqlDatabase as LocalUpdateMysqlDatabase

def public_update_sys_user(view_data):
    return _get_update_sys_user(view_data)

def _get_update_sys_user(view_data):
    LocalUpdateMysqlDatabase().update_sys_user(view_data)
    return DictResult.success_response(
        message=f"修改用户[{view_data['updateSysUserName']}]成功",
        status_code=200,
        types="add_sys_user",
        data=None
    )

def public_add_sys_user(view_data):
    return _get_add_sys_user(view_data)

def _get_add_sys_user(view_data):
    LocalInsertMysqlDatabase().add_sys_user(view_data)
    return DictResult.success_response(
        message=f"新增用户[{view_data['sysUserName']}]成功",
        status_code=200,
        types="add_sys_user",
        data=None
    )

def public_get_sys_user_list():
    return _get_sys_user_list()

def _get_sys_user_list():
    result = LocalQueryMysqlDatabase().query_sys_user_list()
    return DictResult.success_response(
        message="获取函数列表成功",
        status_code=200,
        types="get_sys_user_list",
        context=None,
        data=result
    )