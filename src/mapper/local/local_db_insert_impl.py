import sqlite3
import src.utils.paths_utils as paths
from src.utils.logging_utils import loggings_info
import src.utils.hash_password_utils as password_utls

class LocalMysqlDatabase:
    def __init__(self):
        # 获取系统路径后获取数据库
        self.local_db_path = f'{paths.get_resource_path("db")}/local_db.db'
        self.connection = sqlite3.connect(self.local_db_path)

    """新增系统用户"""
    def add_sys_user(self, view_data):
        cursor = self.connection.cursor()
        insert_sql = """
            insert into sys_user(
                username, 
                password_hash,
                nickname,
                status
            ) values(?, ?, ?, ?)
        """

        cursor.execute(insert_sql, (
            view_data["sysUserName"],
            password_utls.hash_password(view_data["password"]),
            view_data["sysNickName"],
            0,
        ))

        # 拿到刚插入的自增 ID
        user_id = cursor.lastrowid

        # 如果有 roleIds，写关联表
        role_ids = view_data.get("roleIds", [])
        if role_ids:
            user_role_data = [(user_id, roleId) for roleId in role_ids]
            cursor.executemany(
                "insert into sys_user_role (user_id, role_id) values (?, ?)",
                user_role_data
            )

        self.connection.commit()
        self.connection.close()

        loggings_info(f"成功新增用户{view_data}.....")


    """新增函数"""
    def add_function(self, view_data):
        cursor = self.connection.cursor()
        insert_sql = """
            insert into sys_function(function_key, function_name, function_button)
                values(?, ?, ?)
        """
        data = [
            (
                view_data["functionKey"],
                view_data["functionName"],
                view_data["functionButton"].strip() if view_data["functionButton"] else None
            )
        ]
        # 执行并提交
        cursor.executemany(insert_sql, data)
        self.connection.commit()
        self.connection.close()

        loggings_info(f"成功新增函数{view_data}.....")

    """新增角色"""
    def add_role(self, view_data):
        cursor = self.connection.cursor()
        """新增SQL"""
        insert_sql = """
            insert into sys_role
                (role_Name, remark)
            values(?, ?)
        """

        # 新增角色基础数据
        cursor.execute(insert_sql, (
            view_data["roleName"],
            view_data["remark"]
        ))

        # 拿到刚插入的自增 ID
        role_id = cursor.lastrowid

        # 如果有 functionIds，写关联表
        function_ids = view_data.get("functionIds", [])
        if function_ids:
            role_function_data = [(role_id, fid) for fid in function_ids]
            cursor.executemany(
                "insert into sys_role_function (role_id, function_id) values (?, ?)",
                role_function_data
            )

        self.connection.commit()
        self.connection.close()

        loggings_info(f"成功新增角色{view_data}.....")

    """检查表是否存在"""
    def table_exists(self, table_name):
        # 获取链接
        cursor = self.connection.cursor()

        # 查询数据表是否存在
        cursor.execute("""
                       SELECT count(*)
                       FROM sqlite_master
                       WHERE type = 'table'
                         AND name = ?
                       """, (table_name,))

        result = cursor.fetchone()[0]
        self.connection.close()

        return result > 0

    """批量新增调解升级客户"""
    def batch_insert_mediate_upgrade(self, mediate_upgrade_list):
        # 获取链接
        cursor = self.connection.cursor()
        # 先校验对应的数据表是否存在
        if not self.table_exists('law_mediate_upgrade_customer'):
            create_table_sql = '''
                create table if not exists law_mediate_upgrade_customer(
                    mediate_upgrade_id INTEGER PRIMARY KEY,
                    old_company_name varchar(100) NOT NULL,
                    old_accounting_date datetime(6),
                    old_start_time datetime(6),
                    old_end_time datetime(6),
                    old_receive_money decimal(10, 2),
                    old_quality_audit datetime(6),
                    old_remark text,
                    new_company_name varchar(100) NOT NULL,
                    new_accounting_date datetime(6),
                    new_receive_money decimal(10, 2),
                    new_criterion_type varchar(100),
                    new_quality_audit datetime(6),
                    new_remark text
                )
            '''
            # 执行并提交
            cursor.execute(create_table_sql)
            self.connection.commit()

        # 处理参数
        data_tuples = [
            (
                mediate_upgrade_data['old_company_name'],
                mediate_upgrade_data['old_accounting_date'],
                mediate_upgrade_data['old_start_time'],
                mediate_upgrade_data['old_end_time'],
                mediate_upgrade_data['old_receive_money'],
                mediate_upgrade_data['old_quality_audit'],
                mediate_upgrade_data['old_remark'],
                mediate_upgrade_data['new_company_name'],
                mediate_upgrade_data['new_accounting_date'],
                mediate_upgrade_data['new_receive_money'],
                mediate_upgrade_data['new_criterion_type'],
                mediate_upgrade_data['new_quality_audit'],
                mediate_upgrade_data['new_remark']
            ) for mediate_upgrade_data in mediate_upgrade_list
        ]

        # 新增sql
        insert_sql = """
            insert into law_mediate_upgrade_customer(
                old_company_name,
                old_accounting_date,
                old_start_time,
                old_end_time,
                old_receive_money,
                old_quality_audit,
                old_remark,
                new_company_name,
                new_accounting_date,
                new_receive_money,
                new_criterion_type,
                new_quality_audit,
                new_remark
            ) values(
                ?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """

        # 执行并提交
        cursor.executemany(insert_sql, data_tuples)
        self.connection.commit()
        self.connection.close()

        loggings_info(f"成功新增调解升级客户数据{len(data_tuples)}条......")

    """批量新增退费客户"""
    def batch_insert_refound(self, refound_list):
        # 获取链接
        cursor = self.connection.cursor()

        # 先校验对应的数据表是否存在
        if not self.table_exists('law_refound_customer'):
            create_table_sql = """
                create table if not exists law_refound_customer(
                    refound_id INTEGER PRIMARY KEY,
                    accounting_time datetime(6),
                    subject varchar(100),
                    audit_number varchar(100),
                    salesman_company varchar(100),
                    performance_company varchar(100),
                    salesman_name varchar(100),
                    company_name varchar(100),
                    receive_money decimal(10, 2),
                    is_group char(1),
                    lawers varchar(100),
                    server varchar(100),
                    is_renewal char(1),
                    start_time datetime(6),
                    end_time datetime(6),
                    criterion_type varchar(100),
                    refound_time datetime(6),
                    refound_money decimal(10, 2),
                    is_end char(1),
                    refound_cause varchar(100)
                )
            """

            # 提交建表
            cursor.execute(create_table_sql)
            self.connection.commit()
            
        # 处理导入参数
        data_tuples = [
            (
                refound_data['accounting_time'],
                refound_data['subject'],
                refound_data['audit_number'],
                refound_data['salesman_company'],
                refound_data['performance_company'],
                refound_data['salesman_name'],
                refound_data['company_name'],
                refound_data['receive_money'],
                refound_data['is_group'],
                refound_data['lawers'],
                refound_data['server'],
                refound_data['is_renewal'],
                refound_data['start_time'],
                refound_data['end_time'],
                refound_data['criterion_type'],
                refound_data['refound_time'],
                refound_data['refound_money'],
                refound_data['is_end'],
                refound_data['refound_cause']
            ) for refound_data in refound_list
        ]
        
        # 新增sql
        insert_sql = """
            insert into law_refound_customer(
                accounting_time,
                subject,
                audit_number,
                salesman_company,
                performance_company,
                salesman_name,
                company_name,
                receive_money,
                is_group,
                lawers,
                server,
                is_renewal,
                start_time,
                end_time,
                criterion_type,
                refound_time,
                refound_money,
                is_end,
                refound_cause
            ) values(
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """
        
        # 执行新增
        cursor.executemany(insert_sql, data_tuples)
        self.connection.commit()
        self.connection.close()

        loggings_info(f"成功新增退款客户数据{len(data_tuples)}条......")