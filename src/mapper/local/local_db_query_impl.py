import sqlite3
import src.utils.paths_utils as paths

class LocalMysqlDatabase:
    def __init__(self):
        # 获取系统路径后获取数据库
        self.local_db_path = f'{paths.get_resource_path("db")}/local_db.db'
        self.connection = sqlite3.connect(self.local_db_path)

    def get_user_role_functions(self, sys_user_id):
        cursor = self.connection.cursor()
        query_sql = """
            select
                sr.role_id,
                sr.role_name,
                sf.id,
                sf.function_name,
                sf.function_key,
                sf.function_button
            from
                sys_user_role as sur
            left join sys_role as sr on sur.role_id = sr.role_id
            left join sys_role_function as srf on sur.role_id = srf.role_id
            left join sys_function as sf on srf.function_id = sf.id
            where
                sur.user_id = ?
        """
        cursor.execute(query_sql, (sys_user_id,))
        result = cursor.fetchall()
        return [{
            'role_id': row[0],
            'role_name': row[1],
            'function_id': row[2],
            'function_name': row[3],
            "function_key": row[4],
            "function_button": row[5]
        } for row in result]

    def get_sys_user_by_username(self, username: str):
        cursor = self.connection.cursor()
        query_sql = """
            select 
                su.user_id, 
                su.username, 
                su.nickname, 
                su.password_hash,
                su.status
            from sys_user as su
            where
                su.username = ?
        """
        cursor.execute(query_sql, (username,))
        user = cursor.fetchall()
        result = None
        if user:
            result = {
                "sys_user_id": user[0][0],
                "sys_user_name": user[0][1],
                "sys_user_nick_name": user[0][2],
                "sys_user_password": user[0][3],
                "sys_user_status": user[0][4]
            }

        return result

    def query_sys_user_list(self):
        cursor = self.connection.cursor()
        query_sql = """
            select 
                su.user_id, 
                su.username, 
                su.nickname, 
                su.status,
                GROUP_CONCAT(sur.role_id, ',') as role_id
            from sys_user as su
            left join sys_user_role as sur on su.user_id = sur.user_id
            where 
                su.status = 0
            group by sur.user_id
        """
        # 查询
        cursor.execute(query_sql)
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'user_id': row[0],
            'sysUserName': row[1],
            'sysNickName': row[2],
            'status': row[3],
            "roleIds": row[4]
        } for row in result]


    def query_fun_list(self):
        cursor = self.connection.cursor()

        query_sql = """
            select id, function_key, function_name, function_button from sys_function
         """

        # 查询
        cursor.execute(query_sql)
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'id': row[0],
            'function_key': row[1],
            'function_name': row[2],
            'function_button': row[3]
        } for row in result]

    """获取角色列表"""
    def query_role_list(self):
        cursor = self.connection.cursor()

        query_sql = """
            select
                sr.role_id,
                sr.role_name,
                sr.remark,
                GROUP_CONCAT(srf.function_id, ',') as functionIds
            from
                sys_role as sr
            left join sys_role_function as srf on sr.role_id = srf.role_id
            group by srf.role_id
        """

        # 查询
        cursor.execute(query_sql)
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'role_id': row[0],
            'role_name': row[1],
            'remark': row[2],
            'functionIdsStr': row[3]
        } for row in result]