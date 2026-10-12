import sqlite3
import src.utils.paths_utils as paths
import src.utils.hash_password_utils as password_utls

class LocalMysqlDatabase:
    def __init__(self):
        # 获取系统路径后获取数据库
        self.local_db_path = f'{paths.get_resource_path("db")}/local_db.db'
        self.connection = sqlite3.connect(self.local_db_path)

    def update_sys_user(self, view_data):
        cursor = self.connection.cursor()
        try:
            update_sql = """
                         update sys_user \
                         set username      = ?, \
                             nickname      = ?, \
                             password_hash = ? \
                         where user_id = ? \
                         """
            cursor.execute(update_sql, (
                view_data["updateSysUserName"],
                view_data["updateSysNickName"],
                password_utls.hash_password(view_data["updatePassword"]),
                view_data["updateSysUserId"]
            ))

            # 这里需要对关联表数据做根据userId的“全删全增”操作
            # 全删
            delete_sql = """
                         delete \
                         from sys_user_role \
                         where user_id = ? \
                         """
            cursor.execute(delete_sql, view_data["updateSysUserId"])

            # 全增
            role_ids = view_data.get("roleIds", [])
            if role_ids:
                user_role_data = [(view_data["updateSysUserId"], roleId) for roleId in role_ids]
                cursor.executemany(
                    "insert into sys_user_role (user_id, role_id) values (?, ?)",
                    user_role_data
                )
            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise
        finally:
            self.connection.close()


    def update_function(self, view_data):
        cursor = self.connection.cursor()

        updates = [
            (
                view_data["updateFunctionName"],
                view_data["updateFunctionKey"],
                view_data["updateFunctionButton"],
                view_data["updateFunctionId"]
            )
        ]

        update_sql = """
            update sys_function set function_name = ?, function_key = ?, function_button = ? where id = ?
        """

        cursor.executemany(update_sql, updates)

        self.connection.commit()
        self.connection.close()

    def update_role(self, view_data):
        cursor = self.connection.cursor()

        try:
            updates = [
                (
                    view_data["updateRoleName"],
                    view_data["updateRemark"],
                    view_data["updateRoleId"]
                )
            ]

            update_sql = """
                         update sys_role \
                         set role_name = ?, \
                             remark    = ? \
                         where role_id = ? \
                         """

            cursor.executemany(update_sql, updates)

            # 这里需要对关联表数据做根据roleId的“全删全增”操作
            # 全删
            delete_sql = """
                delete from sys_role_function where role_id = ?
            """
            cursor.execute(delete_sql, view_data["updateRoleId"])

            # 全增
            function_ids = view_data.get("functionIds", [])
            if function_ids:
                role_function_data = [(view_data["updateRoleId"], fid) for fid in function_ids]
                cursor.executemany(
                    "insert into sys_role_function (role_id, function_id) values (?, ?)",
                    role_function_data
                )
            self.connection.commit()

        except Exception:
            # 事务管理，任何一条出错就回滚
            self.connection.rollback()
            raise
        finally:
            self.connection.close()