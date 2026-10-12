from src.mapper.local.local_db_query_impl import LocalMysqlDatabase as LocalQueryMysqlDatabase
from src.utils.hash_password_utils import verify_password

def login(username: str, password: str) -> dict:
    user = LocalQueryMysqlDatabase().get_sys_user_by_username(username)
    if not user:
        raise ValueError("用户名或密码错误")
    if user.get("sys_user_status") != 0:
        raise ValueError("账号已被禁用")
    if not verify_password(plain=password, hashed=user.get("sys_user_password")):
        raise ValueError("用户名或密码错误")

    # 查用户的所有 function_key
    function_param = LocalQueryMysqlDatabase().get_user_role_functions(user.get("sys_user_id"))

    return {
        "sys_user_id": user.get("sys_user_id"),
        "sys_user_name": user.get("sys_user_name"),
        "sys_user_nick_name": user.get("sys_user_nick_name"),
        "function_keys": list(function_param)
    }