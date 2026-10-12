from src.utils.dict_result import DictResult
from src.mapper.local.local_db_insert_impl import LocalMysqlDatabase as LocalInsertMysqlDatabase
from src.mapper.local.local_db_query_impl import LocalMysqlDatabase as LocalQueryMysqlDatabase
from src.mapper.local.local_db_update_impl import LocalMysqlDatabase as LocalUpdateMysqlDatabase

"""新增角色对外接口"""
def public_update_role(view_data):
    return _update_role(view_data)

"""新增角色对外接口"""
def public_add_role(view_data):
    return _add_role(view_data)

"""获取角色列表对外接口"""
def public_get_role_list(view_data):
    return _get_role_list(view_data)

"""新增角色接口"""
def _update_role(view_data):
    LocalUpdateMysqlDatabase().update_role(view_data)
    return DictResult.success_response(
        message="修改角色成功",
        status_code=200,
        types="update_role",
        data=None
    )

"""获取角色列表接口"""
def _get_role_list(view_data):
    result = LocalQueryMysqlDatabase().query_role_list()
    return DictResult.success_response(
        message="获取角色列表成功",
        status_code=200,
        types="get_role_list",
        context=view_data["context"] if "context" in view_data else None,
        data=result
    )

"""新增角色接口"""
def _add_role(view_data):
    LocalInsertMysqlDatabase().add_role(view_data)
    return DictResult.success_response(
        message="新增角色成功",
        status_code=200,
        types="add_role",
        data=None
    )