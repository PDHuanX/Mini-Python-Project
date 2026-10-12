import datetime

from src.utils.db_utils import create_connection_pymysql


class MysqlDatabase:
    def __init__(self):
        # 初始化链接
        pooled_db = create_connection_pymysql()
        self.connection = pooled_db.connection()

    """回退交付状态"""
    def rollback_status(self, view_data):
        cursor = self.connection.cursor()

        # 第一条SQL，目的是将事项从已交付状态回退到待交付状态（delivery_status = 'WAITPAY'），并置空交付时间
        cursor.execute("update law_service_record set delivery_time = null, delivery_status = 'WAITPAY' where service_id = %s", (view_data['serviceId'],))

        # 第二条SQL，是将已交付的文件做逻辑删除
        cursor.execute("update law_delivery set del_flag = 1 where service_id = %s",(view_data['serviceId'],))

        if view_data["isEnd"] and "end" == view_data["isEnd"]:
            # 第三条SQL需要确定完结才执行，将是否确认变更为未确认（is_verify = 'NO'），服务状态回退为开启（service_status = 'START'），并置空确认时间（confirm_date = null）
            cursor.execute("update law_service_record set is_verify = 'NO', service_status = 'START', confirm_date = null where service_id = %s", (view_data['serviceId'],))

        self.connection.commit()
        self.connection.close()

    """批量审批"""
    def update_delay_record_by_delay_ids(self, delay_ids, audit_status):
        cursor = self.connection.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        updates = [
            (audit_status, now, now, delay_id) for delay_id in delay_ids
        ]

        update_sql = f"""
            update law_delay_record set audit_status = %s, audit_time = %s, update_by = '质检/运维 黄键楠', update_id = 980, update_time = %s where delay_id = %s
        """
        cursor.executemany(update_sql, updates)

        self.connection.commit()
        self.connection.close()

    """审批完成后修改计划完成时间"""
    def update_service_record_by_service_ids(self, data):
        cursor = self.connection.cursor()

        updates = []
        for key, value in data['changeData'].items():
            updates.append((value['new_time'], int(value['service_id'])))

        update_sql = """
            update law_service_record set plan_time = %s where service_id = %s
        """
        cursor.executemany(update_sql, updates)

        self.connection.commit()
        self.connection.close()