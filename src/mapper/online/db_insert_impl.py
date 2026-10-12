import datetime
import json

from src.utils.db_utils import create_connection_pymysql
from src.utils.logging_utils import loggings_info


class MysqlDatabase:
    def __init__(self):
        # 初始化链接
        pooled_db = create_connection_pymysql()
        self.connection = pooled_db.connection()

    """批量新增外省客户"""
    def batch_insert_customer(self, source_data_list):
        # 获取链接
        cursor = self.connection.cursor()

        # 当前时间
        now = datetime.datetime.today()

        # 构建唯一标识（根据业务字段）
        data_tuples = [
            (
                customer.accounting_date,
                customer.salesman_company,
                customer.salesman_name,
                customer.receive_money,
                customer.company_name,
                customer.code,
                customer.contact,
                customer.contact_phone,
                customer.associated_person,
                customer.is_renewal,
                customer.is_group,
                json.dumps(customer.lawers),
                customer.serve_name,
                customer.serve_id,
                customer.remark,
                customer.start_time,
                customer.end_time,
                customer.industry_type,
                customer.steward_id,
                customer.steward_name,
                customer.finance_audit,
                customer.quality_audit,
                customer.is_item,
                customer.performance_company,
                customer.item_name,
                now,
                980,
                "质检/运维 黄键楠",
                customer.audit_pass_time,
                customer.fill_time,
                customer.consultant_id,
                customer.consultant_name,
            ) for customer in source_data_list
        ]
        insert_placeholders = ', '.join(['%s'] * len(data_tuples[0]))

        # 新增sql
        insert_sql = (f"INSERT INTO law_customer (accounting_date, "
                      f"salesman_company, "
                      f"salesman_name, "
                      f"receive_money, company_name, code, contact, contact_phone,"
                      f"associated_person, is_renewal, is_group, lawers, serve_name, serve_id,"
                      f"remark, start_time, end_time, industry_type, steward_id,"
                      f"steward_name, finance_audit, quality_audit, is_item, performance_company, item_name, create_time,"
                      f"create_id, create_by, audit_pass_time, fill_time, consultant_id, consultant_name) "
                      f"VALUES ({insert_placeholders})")
        # 执行新增
        cursor.executemany(insert_sql, data_tuples)

        """查询条件，只需要定位当前时间（now，这个对于一个批次导入具有唯一性，因为同一批次用的同个时间）、创建人ID这两个即可"""
        select_query = f"""
                SELECT customer_id, company_name, lawers, serve_id, start_time, end_time  FROM law_customer WHERE create_time = '{now}' and create_id = 980
                """
        cursor.execute(select_query)

        results = cursor.fetchall()

        final_result = [{
            "customer_id": row[0],
            "company_name": row[1],
            "lawers": row[2],
            "serve_id": row[3],
            "start_time": row[4],
            "end_time": row[5],
        } for row in results]

        # 事务提交
        self.connection.commit()
        self.connection.close()
        loggings_info(f"成功新增客户数据{len(source_data_list)}条......")

        return final_result

    """批量新增客户的合同内容"""
    def batch_insert_contract(self, source_data_list):
        # 获取链接
        cursor = self.connection.cursor()

        # 当前时间
        now = datetime.datetime.today()
        # 形成数据元组
        data_tuples = [
            (
                row["customer_id"],
                row["lawers"],
                row["serve_id"],
                row["start_time"],
                row["end_time"],
                row["item_id"],
                row["item_name"],
                row["item_meal"],
                row["item_type"],
                row["count"],
                row["residue_count"],
                row["item_count"],
                row["init_item_count"],
                row["price"],
                row["item_price"],
                now,
                980,
                "质检/运维 黄键楠",
                0
            ) for row in source_data_list
        ]
        # 数据个数
        insert_placeholders = ', '.join(['%s'] * len(data_tuples[0]))

        insert_sql = f"""
            insert into law_contract(
                customer_id,
                lawers,
                serve_id,
                start_time,
                end_time,
                item_id,
                item_name,
                item_meal,
                item_type,
                count,
                residue_count,
                item_count,
                init_item_count,
                price,
                item_price,
                create_time,
                create_id,
                create_by,
                del_flag
            ) values ({insert_placeholders})
        """

        # 执行新增，直接提交事务，无需其它操作
        cursor.executemany(insert_sql, data_tuples)
        self.connection.commit()
        self.connection.close()

        loggings_info(f"成功新增合同数据{len(source_data_list)}条......")
        return {
            "statusCode": 200,
            "msg": f"成功新增合同数据{len(source_data_list)}"
        }

    """批量修改客户主表中的剩余次数"""
    def batch_update_customer(self, source_data_list):
        # 获取链接
        cursor = self.connection.cursor()

        # 当前时间
        now = datetime.datetime.today()
        # 形成数据元组
        data_tuples = [
            (
                row['ok_num'],
                row['no_num'],
                now,
                980,
                "质检/运维 黄键楠",
                row['customer_id']
            ) for row in source_data_list
        ]
        # 修改sql
        update_sql = f"""
            update law_customer set 
                ok_num = %s,
                no_num = %s,
                update_time = %s,
                update_id = %s,
                update_by = %s
            where customer_id = %s
        """

        # 执行批量更新
        affected_rows = cursor.executemany(update_sql, data_tuples)
        self.connection.commit()
        self.connection.close()

        loggings_info(f"成功修改{affected_rows}条数据......")
        return {
            "statusCode": 200,
            "msg": f"成功修改{affected_rows}条数据......"
        }