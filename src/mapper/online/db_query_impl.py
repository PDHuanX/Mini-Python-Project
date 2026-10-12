import datetime

from src.entity.query_dao import Contract, CounselorLog, Customer, SysUser, ServiceRecord, SysDictData
from src.utils.db_utils import create_connection_pymysql

class MysqlDatabase:
    def __init__(self):
        # 初始化链接
        pooled_db = create_connection_pymysql()
        self.connection = pooled_db.connection()

    """服务顾问月度新增事项明细"""
    def get_server_month_add_service(self, view_data):
        cursor = self.connection.cursor()

        month_range = view_data["monthRange"].split("~")
        start_date = datetime.datetime.strptime(month_range[0], "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
        end_date = (datetime.datetime.strptime(month_range[1], "%Y-%m-%d") + datetime.timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

        query_sql = """
            select 
                lsr.service_name as service_name,
                lsr.item_name as item_name,
                lar.create_time as create_time,
                lar.create_by as create_by,
                su.nick_name as nick_name
            from 
                law_service_record as lsr
            left join law_audit_record as lar on lsr.service_id = lar.service_id and lar.audit_type = 'DATA' and lar.audit_status = 'OK'
            left join sys_user as su on su.user_id = lsr.serve_id
            where 
                lsr.service_status != 'INVALID'
            and lar.create_time >= %s and lar.create_time < %s
        """
        cursor.execute(query_sql, (start_date, end_date))
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'service_name': row[0],
            'item_name': row[1],
            'create_time': row[2],
            'create_by': row[3],
            'nick_name': row[4],
        } for row in result]

    """月初执行-走到立案节点的数据"""
    def get_submit_case_register_service(self, view_data):
        cursor = self.connection.cursor()
        query_sql = """
            SELECT
                lc.customer_id,
                lc.company_name AS company_name,
                lc.serve_name AS serve_name,
                REGEXP_REPLACE ( JSON_EXTRACT( lc.lawers, '$[0].lawName' ), '"', '' ) AS law_name,
                lsr.service_name AS service_name,
                lc.salesman_company AS salesman_company,
                lc.performance_company AS performance_company,
                (select sdd.dict_label from sys_dict_data as sdd where sdd.dict_value = lc.payee_name COLLATE utf8mb4_general_ci) as payee_name,
                DATE_FORMAT( lrfr.create_time, '%%Y/%%m/%%d' ) AS submit_case_date
            FROM
                law_register AS lr
                LEFT JOIN law_register_filing_result AS lrfr ON lr.register_id = lrfr.register_id
                LEFT JOIN law_service_record AS lsr ON lsr.service_id = lr.service_id
                LEFT JOIN law_customer AS lc ON lc.customer_id = lsr.customer_id 
            WHERE
                lr.current_service_id >= 5 
                AND lr.current_service_id != 15 
                AND lr.del_flag = 0 
                AND lrfr.del_flag = 0 
                AND lc.company_name NOT LIKE concat( '%%', '测试', '%%' )
                and lrfr.create_time < %s
        """
        cursor.execute(query_sql, (view_data["assignDate"]))
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'customer_id': row[0],
            'company_name': row[1],
            'serve_name': row[2],
            'law_name': row[3],
            'service_name': row[4],
            'salesman_company': row[5],
            'performance_company': row[6],
            'payee_name': row[7],
            'submit_case_date': row[8],
        } for row in result]

    """月初执行-搁置事项数（依据立案模块搁置数据）"""
    def get_shelve_case_register(self):
        cursor = self.connection.cursor()
        query_sql = """
            SELECT
                lc.company_name as company_name,
                lc.serve_name as serve_name,
                REGEXP_REPLACE(JSON_EXTRACT(lc.lawers, '$[0].lawName'), '"', '') as law_name,
                lsr.service_name as service_name,
                lsr.item_name as item_name,
                case lsr.delivery_status
                when 'WAITPAY' then '待交付'
                when 'ALLPAY' then '已交付'
                when 'OVERPAY' then '延期交付'
                else '其他' end as delivery_status,
                lc.salesman_company as salesman_company,
                (
                        select res.yearStartTime from (
                            select
                        lct.customer_id,
                        (select MIN( start_time ) from law_contract as lc where lc.del_flag = 0 and lc.customer_id = lct.customer_id and (item_meal like concat('%%', 'YEAR', '%%') or item_meal = 'MEDIATION') group by lc.customer_id) AS yearStartTime
                    from law_contract as lct where lct.del_flag = 0
                    group by lct.customer_id
                        ) as res where res.customer_id = lc.customer_id
                ) as contract_start_date,
                (
                        select res.yearEndTime from (
                            select
                        lct.customer_id,
                        (select MIN( end_time ) from law_contract as lc where lc.del_flag = 0 and lc.customer_id = lct.customer_id and (item_meal like concat('%%', 'YEAR', '%%') or item_meal = 'MEDIATION') group by lc.customer_id) AS yearEndTime
                    from law_contract as lct where lct.del_flag = 0
                    group by lct.customer_id
                        ) as res where res.customer_id = lc.customer_id
                ) as contract_end_date,
                DATE_FORMAT(lrh.create_time,'%%Y-%%m-%%d') as shelve_date,
                lrh.hold_reason as shelve_reason
            FROM
                law_register AS lr
            left join law_register_hold as lrh on lrh.register_id = lr.register_id
            left join law_service_record as lsr on lr.service_id = lsr.service_id
            left join law_customer as lc on lsr.customer_id = lc.customer_id
            where
                lr.register_status = 'HO'
            and lr.current_service_id != '0'
            and lr.del_flag = 0
            and lc.company_name not like concat('%%', '测试', '%%')
        """
        cursor.execute(query_sql)
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'company_name': row[0],
            'serve_name': row[1],
            'law_name': row[2],
            'service_name': row[3],
            'item_name': row[4],
            'delivery_status': row[5],
            'salesman_company': row[6],
            'contract_start_date': row[7],
            'contract_end_date': row[8],
            'shelve_date': row[9],
            'shelve_reason': row[10],
        } for row in result]

    """获取逾期事项"""
    def get_overdue_service(self, view_data):
        cursor = self.connection.cursor()
        query_sql = """
            select 
                lsr.service_id as service_id,
                lc.company_name as company_name,
                REGEXP_REPLACE(JSON_EXTRACT(lc.lawers, '$[0].lawName'), '"', '') as law_name,
                lsr.service_name as service_name,
                lsr.item_name as item_name,
                lor.plan_time as plan_time,
                lor.overdue_time as overdue_time
            from 
                law_overdue_record as lor
            left join law_service_record as lsr on lor.service_id = lsr.service_id
            left join law_customer as lc on lsr.customer_id = lc.customer_id
            where
                lor.del_flag = 0
            and lsr.del_flag = 0
            and lc.del_flag = 0
            and lor.overdue_time like concat('', DATE_SUB(DATE_FORMAT(NOW(), '%%Y-%%m-%%d'),INTERVAL %s DAY), '')
        """
        cursor.execute(query_sql, (view_data["overdueDate"]))
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'service_id': row[0],
            'company_name': row[1],
            'law_name': row[2],
            'service_name': row[3],
            'item_name': row[4],
            'plan_time': row[5],
            'overdue_time': row[6]
        } for row in result]

    """获取预警事项"""
    def get_warning_service(self):
        cursor = self.connection.cursor()
        query_sql = """
            SELECT
                lsr.service_id as service_id,
                lsr.company_name as company_name,
                lsr.service_name as service_name,
                lsr.item_name as item_name,
                lsr.plan_time as plan_time,
                REGEXP_REPLACE(JSON_EXTRACT(lc.lawers, '$[0].lawName'), '"', '') as law_name
            FROM
                law_service_record as lsr
            left join law_customer as lc on lsr.customer_id = lc.customer_id
            WHERE
                lsr.plan_time like concat('%', DATE_FORMAT(now(), '%Y-%m-%d'), '%')
                AND lsr.service_status = 'START' 
                AND lsr.del_flag = 0
                AND lsr.delivery_time is null
                AND lsr.company_name not like concat('%','测试','%')
            ORDER BY
                lsr.plan_time ASC
        """
        cursor.execute(query_sql)
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'service_id': row[0],
            'company_name': row[1],
            'service_name': row[2],
            'item_name': row[3],
            'plan_time': row[4],
            'law_name': row[5]
        } for row in result]

    """获取指定日期的延期事项"""
    def get_delay_service(self, view_data):
        cursor = self.connection.cursor()
        query_sql = """
            select
                lsr.service_id as service_id,
                lsr.company_name as company_name,	
                REGEXP_REPLACE(JSON_EXTRACT(lc.lawers, '$[0].lawName'), '"', '') as law_name,
                lsr.service_name as service_name,
                lsr.item_name as item_name,
                lsr.plan_time as plan_time,
                DATE_FORMAT(ldr4.create_time,'%%Y-%%m-%%d %%H:%%i:%%s') as new_delay_date,
                ldr1.count as delay_count,
                ldr2.okCount as delay_ok_count,
                ldr3.noCount as delay_no_count
            from
                law_service_record as lsr
            left join(select ldr.service_id, count(ldr.delay_id) as count, max(ldr.create_time) as create_time from law_delay_record as ldr where ldr.del_flag = 0 group by ldr.service_id) as ldr1 on ldr1.service_id = lsr.service_id
            left join(select ldr.service_id, count(ldr.delay_id) as okCount from law_delay_record as ldr where ldr.del_flag = 0 and ldr.audit_status = 'OK' group by ldr.service_id) as ldr2 on ldr2.service_id = lsr.service_id
            left join(select ldr.service_id, count(ldr.delay_id) as noCount from law_delay_record as ldr where ldr.del_flag = 0 and ldr.audit_status = 'NO' group by ldr.service_id) as ldr3 on ldr3.service_id = lsr.service_id
            left join(select ldr.service_id, max(ldr.create_time) as create_time from law_delay_record as ldr where ldr.del_flag = 0 group by ldr.service_id) as ldr4 on ldr4.service_id = lsr.service_id
            left join law_customer as lc on lsr.customer_id = lc.customer_id
            where
                lsr.delivery_status != 'ALLPAY'
            and lsr.service_status = 'START'
            and lsr.del_flag = 0
            and ldr1.count is not null
            and ldr4.create_time like concat('%%',DATE_SUB(DATE_FORMAT(NOW(), '%%Y-%%m-%%d'),INTERVAL %s day), '%%')
            order by ldr4.create_time desc
        """
        cursor.execute(query_sql, (view_data["delayDate"]))
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'service_id': row[0],
            'company_name': row[1],
            'law_name': row[2],
            'service_name': row[3],
            'item_name': row[4],
            'plan_time': row[5],
            'new_delay_date': row[6],
            'delay_count': row[7],
            'delay_ok_count': row[8],
            'delay_no_count': row[9]
        } for row in result]

    """获取指定日期的暂停事项"""
    def get_pause_service(self, view_data):
        cursor = self.connection.cursor()
        query_sql = """
            select
                lsr.service_id as service_id,
                lc.company_name as company_name,
                REGEXP_REPLACE(JSON_EXTRACT(lc.lawers, '$[0].lawName'), '"', '') as law_name,
                lsr.service_name as service_name,
                lsr.item_name as item_name,
                DATE_FORMAT(lar4.create_time,'%%Y-%%m-%%d %%H:%%i:%%s') as new_pause_date,
                lar1.count as pause_count,
                lar2.okCount as pause_ok_count,
                lar3.noCount as pause_not_count,
                lar5.noCount as pause_wait_count
            from
                law_service_record as lsr
            left join law_customer as lc on lsr.customer_id = lc.customer_id
            left join (select lar.service_id, count(audit_id) as count from law_audit_record as lar where lar.del_flag = 0 and lar.audit_type = 'STOP' group by lar.service_id) as lar1 on lar1.service_id = lsr.service_id
            left join (select lar.service_id, count(audit_id) as okCount from law_audit_record as lar where lar.del_flag = 0 and lar.audit_type = 'STOP' and audit_status = 'OK' group by lar.service_id) as lar2 on lar2.service_id = lsr.service_id
            left join (select lar.service_id, count(audit_id) as noCount from law_audit_record as lar where lar.del_flag = 0 and lar.audit_type = 'STOP' and audit_status = 'NO' group by lar.service_id) as lar3 on lar3.service_id = lsr.service_id
            left join (select lar.service_id, count(audit_id) as noCount from law_audit_record as lar where lar.del_flag = 0 and lar.audit_type = 'STOP' and audit_status = 'WAIT' and lar.create_time like concat('%%',DATE_SUB(DATE_FORMAT(NOW(), '%%Y-%%m-%%d'),INTERVAL %s day), '%%') group by lar.service_id) as lar5 on lar5.service_id = lsr.service_id
            left join (select lar.service_id, max(lar.create_time) as create_time from law_audit_record as lar where lar.del_flag = 0 and lar.audit_type = 'STOP' group by lar.service_id) as lar4 on lar4.service_id = lsr.service_id
            where
                lsr.delivery_status != 'ALLPAY'
            and lsr.del_flag = 0
            and lar1.count is not null
            and lar4.create_time like concat('%%',DATE_SUB(DATE_FORMAT(NOW(), '%%Y-%%m-%%d'),INTERVAL %s day), '%%')
            order by lar4.create_time desc
        """

        cursor.execute(query_sql, (view_data["pauseDate"],view_data["pauseDate"]))
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'service_id': row[0],
            'company_name': row[1],
            'law_name': row[2],
            'service_name': row[3],
            'item_name': row[4],
            'new_pause_date': row[5],
            'pause_count': row[6],
            'pause_ok_count': row[7],
            'pause_not_count': row[8],
            'pause_wait_count': row[9]
        } for row in result]

    def get_law_delivery_list(self, laws, delivery_type, start_time, end_time, level):
        cursor = self.connection.cursor()
        # 拼接占位符
        placeholders = ' or '.join(["lsr.lawers like concat('%%', %s, '%%')" for _ in laws])

        if level == "new":
            query_sql = f"""
            select
                lsr.service_id,
                lsr.customer_id,
                lsr.company_name,
                del.file_url,
                DATE_FORMAT(del.delivery_time, '%%Y-%%m-%%d %%H:%%i') as delivery_time,
                REGEXP_REPLACE(JSON_EXTRACT(lc.lawers, '$[0].lawName'), '"', '') as lawers,
                lsr.service_name
            from
                law_service_record as lsr 
            left join (
                select 
                    ld.service_id,
                    MAX(ld.file_url) as file_url,
                    MAX(ld.delivery_time) as delivery_time
                from
                    law_delivery as ld
                where
                    ld.del_flag = 0
                and ld.is_final = 1
                group by ld.service_id
            ) as del on lsr.service_id = del.service_id
            left join law_customer as lc on lc.customer_id = lsr.customer_id
            where
                lsr.del_flag = 0
            and lsr.item_name like concat('%%', %s, '%%')
            and lsr.delivery_time between %s and %s
            and (
                {placeholders}
            )
            order by lsr.delivery_time
        """
        else:
            query_sql = f"""
                        select
                            lsr.service_id,
                            lsr.customer_id,
                            lsr.company_name,
                            del.file_url,
                            DATE_FORMAT(del.delivery_time, '%%Y-%%m-%%d %%H:%%i') as delivery_time,
                            REGEXP_REPLACE(JSON_EXTRACT(lc.lawers, '$[0].lawName'), '"', '') as lawers,
                            lsr.service_name
                        from
                            law_service_record as lsr 
                        left join (
                            select 
                                ld.service_id,
                                ld.file_url as file_url,
                                ld.delivery_time as delivery_time
                            from
                                law_delivery as ld
                            where
                                ld.del_flag = 0
                        ) as del on lsr.service_id = del.service_id
                        left join law_customer as lc on lc.customer_id = lsr.customer_id
                        where
                            lsr.del_flag = 0
                        and lsr.item_name like concat('%%', %s, '%%')
                        and lsr.delivery_time between %s and %s
                        and (
                            {placeholders}
                        )
                        order by lsr.delivery_time
                    """

        cursor.execute(query_sql, [delivery_type, start_time, end_time] + laws)
        result = cursor.fetchall()
        self.connection.close()

        return [{
            'service_id': row[0],
            'customer_id': row[1],
            'company_name': row[2],
            'file_url': row[3],
            'delivery_time': row[4],
            'lawers': row[5],
            'service_name': row[6]
        } for row in result]

    """获取是"""
    def get_customer_lawsuit_init_count(self, customer_ids):
        cursor = self.connection.cursor()
        # 拼接占位符
        placeholders = ', '.join(['%s' for _ in customer_ids])

        query_sql = f"""
            select
                lc1.customer_id,
                lc1.item_name as item_name,
                lc1.init_item_count as count
            from
              law_contract as lc1
            where
                lc1.customer_id in ({placeholders})
            and lc1.del_flag = 0
            and lc1.item_name is not null
            and lc1.init_item_count > 0
            and lc1.item_name like concat('%%', '指导立案', '%%')
            
            UNION ALL
            
            select
                lc2.customer_id,
                lc2.thali_name as item_name,
                lc2.init_thali_count as count
            from
              law_contract as lc2
            where
                lc2.customer_id in ({placeholders})
            and lc2.del_flag = 0
            and lc2.thali_name is not null
            and lc2.init_item_count > 0
            and lc2.thali_name like concat('%%', '指导立案', '%%')
        """
        cursor.execute(query_sql, customer_ids * 2)
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'customer_id': row[0],
            'item_name': row[1],
            'count': row[2],
        } for row in result]

    """获取客户过程中加选金额"""
    def get_customer_add_money(self, customer_ids):
        cursor = self.connection.cursor()
        # 拼接占位符
        placeholders = ', '.join(['%s' for _ in customer_ids])

        query_sql = f"""
            select
                lcao.customer_add_on_id,
                lcao.customer_id,
                lcao.accounting_date,
                lcao.receive_money,
                res.item_meal
            from
                law_customer_add_on as lcao
            left join (
                select 
                    group_concat(lc.item_meal) as item_meal, 
                    lc.customer_add_on_id 
                from law_contract as lc 
                where 
                    lc.customer_add_on_id is not null 
                and lc.del_flag = 0 
                group by lc.customer_add_on_id
            ) as res on res.customer_add_on_id = lcao.customer_add_on_id
            where
                lcao.customer_id in({placeholders})
            and lcao.del_flag = 0
            and lcao.finance_audit = 'OK'
            and lcao.quality_audit = 'OK'
        """

        cursor.execute(query_sql, customer_ids)
        result = cursor.fetchall()
        self.connection.close()
        return [{
            'customer_add_on_id' : row[0],
            'customer_id' : row[1],
            'accounting_date' : row[2],
            'receive_money' : row[3],
            'item_meal': row[4]
        } for row in result]

    """获取待审核的延期数据"""
    def get_await_audit_postpone_list(self):
        # 当前时间
        now_date = datetime.datetime.today().strftime("%Y-%m-%d")

        cursor = self.connection.cursor()
        query_sql = """
            select
                lsr.company_name,
                lsr.service_name,
                lsr.item_name,
                ldr.first_time,
                ldr.new_time,
                ldr.delay_reason,
                ldr.create_time,
                ldr.delay_id,
                lsr.service_id,
                ldr.create_by
            from 
                law_delay_record as ldr 
            left join law_service_record as lsr on ldr.service_id = lsr.service_id
            where 
                ldr.audit_status = 'WAIT' and lsr.service_status = 'START' and ldr.create_time like %s
            order by ldr.create_by, ldr.create_time desc
        """
        now_date = f'%{now_date}%'
        cursor.execute(query_sql, [now_date])
        result = cursor.fetchall()
        self.connection.close()
        return [
            {
                "company_name": row[0],
                "service_name": row[1],
                "item_name": row[2],
                "first_time": format(row[3], "%Y-%m-%d"),
                "new_time": format(row[4], "%Y-%m-%d"),
                "delay_reason": row[5],
                "create_time": format(row[6], "%Y-%m-%d %H:%M:%S"),
                "delay_id": row[7],
                "service_id": row[8],
                "create_by": row[9]
            } for row in result
        ]

    """获取指定时间内未分配管家的客户数据"""
    def get_not_steward_list(self, start_time, end_time):
        cursor = self.connection.cursor()
        query_sql = """
            SELECT
                lc.company_name as 'company_name',
                lc.salesman_company as 'salesman_company',
                case
                (select GROUP_CONCAT(DISTINCT lct.item_meal) from law_contract as lct where lct.customer_id = lc.customer_id group by lct.customer_id )
                when 'ONEYEAR' then '一年会员'
                when 'NON,ONEYEAR' then '一年会员+加选'
                when 'TWOYEAR' then '二年会员'
                when 'NON,TWOYEAR' then '二年会员+加选'
                when 'THREEYEAR' then '三年会员'
                when 'NON,THREEYEAR' then '三年会员+加选'
                when 'MEDIATION' then '调解套餐'
                when 'REPO' then '回购'
                when 'NON,REPO' then '回购'
                else '其它' end as 'item_name'
            FROM
                law_customer as lc
            WHERE
                lc.quality_audit = 'OK' 
                AND lc.finance_audit = 'OK' 
                AND lc.audit_pass_time BETWEEN %s AND %s 
                AND lc.steward_id IS NULL 
                AND lc.salesman_company not in('武汉','咸阳法益网','肇庆法证衡商务服务','庐江分公司','凉山法益网')
                AND lc.customer_id not in('32765')
            ORDER BY
                lc.salesman_company
        """
        cursor.execute(query_sql, [start_time, end_time])
        result = cursor.fetchall()
        self.connection.close()
        return [
            {
                "company_name": row[0],
                "salesman_company": row[1],
                "item_name": row[2]
            } for row in result
        ]

    """根据时间区间，获取区间内的交付数据"""
    def get_salesman_delivery(self, start_time, end_time):
        cursor = self.connection.cursor()
        query_sql = """
            select
                ld.customer_id as customerId,
                ld.secondary_name as secondaryName,
                lc.salesman_company as salesmanCompany,
                lsr.item_name as itemName
            from law_delivery  as ld
            left join law_service_record as lsr on ld.service_id = lsr.service_id
            left join law_customer as lc on lsr.customer_id = lc.customer_id
            where
                ld.del_flag = 0
              and ld.is_final = 1
              and lsr.confirm_date between %s and %s
            group by ld.service_id, ld.delivery_id order by ld.create_time desc
        """

        cursor.execute(query_sql, [start_time, end_time])
        result = cursor.fetchall()
        self.connection.close()
        return [
            {
                "customer_id": row[0],
                "secondary_name": row[1],
                "salesman_company": row[2],
                "item_name": row[3]
            } for row in result
        ]

    """
    根据客户id查询客户数据
    """
    def query_customer_by_ids(self, ids):
        # 拼接占位符
        placeholders = ', '.join(['%s' for _ in ids])
        # 处理查询
        cursor = self.connection.cursor()
        query_sql = f""" 
            select
                customer_id,
                company_name,
                contact_phone,
                room_id,
                associated_person,
                enterprise_name,
                salesman_company,
                steward_name,
                steward_id,
                serve_name,
                lawers,
                consultant_name,
                performance_company,
                code,
                ok_num, 
                no_num,
                payee_name,
                industry_type,
                contact,
                receive_money
            from
                law_customer
            where del_flag = 0
            and finance_audit = "OK"
            and quality_audit = "OK" and customer_id in ({placeholders})
        """
        cursor.execute(query_sql, ids)
        result = cursor.fetchall()
        self.connection.close()
        return [Customer(*row) for row in result]

    """
    查询账号信息
    """
    def query_sys_user_list(self, ids):
        # 拼接占位符
        placeholders = ', '.join(['%s' for _ in ids])
        # 处理查询
        cursor = self.connection.cursor()
        cursor.execute(f'select user_id, user_name, nick_name, role_id from sys_user where user_id in ({placeholders})', ids)
        result = cursor.fetchall()
        self.connection.close()
        return [SysUser(*row) for row in result]

    """
    根据ids获取客户的合同信息
    """
    def query_customer_contract_list(self, ids):
        # 拼接占位符
        placeholders = ', '.join(['%s' for _ in ids])
        # 处理查询
        year = "YEAR"
        cursor = self.connection.cursor()

        # 查询语句
        sql = f"""
                          SELECT lct.customer_id                                                                              AS customerId, \
                                 MIN(CASE \
                                         WHEN (lc1.item_meal LIKE %s OR lc1.item_meal = 'MEDIATION') \
                                             THEN lc1.start_time END)                                                         AS yearStartTime, \
                                 MIN(CASE \
                                         WHEN (lc1.item_meal NOT LIKE %s AND lc1.item_meal != 'MEDIATION' OR lc1.item_meal IS NULL) \
                                             THEN lc1.start_time END)                                                         AS nonStartTime, \
                                 MIN(CASE \
                                         WHEN (lc1.item_meal LIKE %s OR lc1.item_meal = 'MEDIATION') \
                                             THEN lc1.end_time END)                                                           AS yearEndTime, \
                                 MAX(CASE \
                                         WHEN (lc1.item_meal NOT LIKE %s AND lc1.item_meal != 'MEDIATION' OR lc1.item_meal IS NULL) \
                                             THEN lc1.end_time END)                                                           AS nonEndTime, \
                                 GROUP_CONCAT(DISTINCT lc1.item_meal)                                                         as itemMeal, \
                                 IF(GROUP_CONCAT(DISTINCT lc1.thali_id) IS NULL, '无', '加选')                                AS thaliId
                          FROM law_contract as lct
                                   LEFT JOIN law_contract as lc1 ON lc1.customer_id = lct.customer_id AND lc1.del_flag = 0
                          WHERE lct.del_flag = 0
                            AND lct.customer_id IN ({placeholders})
                          GROUP BY lct.customer_id \
                          """

        # 构建参数列表：4个LIKE参数 + IDs参数
        like_pattern = f'%{year}%'
        params = [like_pattern, like_pattern, like_pattern, like_pattern] + list(ids)

        cursor.execute(sql, params)
        result = cursor.fetchall()
        self.connection.close()
        return [Contract(*row) for row in result]

    """
    获取客户的顾问分配记录
    """
    def query_counselor_log_list(self):
        # 查询语句
        sql = "select counselor_log_id, customer_id, create_time from law_counselor_log where (new_serve_name is not null or new_law_name is not null) and del_flag = 0 order by counselor_log_id"
        cursor = self.connection.cursor()
        # 查询
        cursor.execute(sql)
        result = cursor.fetchall()
        self.connection.close()
        return [CounselorLog(*row) for row in result]

    """
    获取已经计提的交付数据
    """
    def query_service_record_confirm_list(self, ids):
        # 拼接占位符
        placeholders = ', '.join(['%s' for _ in ids])
        # 查询语句
        sql = (f"select "
               f"service_id, "
               f"customer_id, "
               f"company_name, "
               f"service_name, "
               f"item_name, "
               f"serve_id, "
               f"lawers, "
               f"confirm_date "
               f"from law_service_record where del_flag = 0 and is_accrue = 1 and customer_id IN ({placeholders})")
        cursor = self.connection.cursor()
        # 查询
        cursor.execute(sql, ids)
        result = cursor.fetchall()
        self.connection.close()
        return [ServiceRecord(*row) for row in result]

    """
    获取法律及服务顾问账号（全集）
    """
    def query_law_server_sys_user_list(self, ids):
        # 拼接占位符
        placeholders = ', '.join(['%s' for _ in ids])
        # 一些参数
        str_1 = 'TERMINAL_BIZ'
        like_param = f'{str_1}'
        # 查询语句
        sql = (f"select "
               f"user_id, "
               f"user_name, "
               f"nick_name,"
               f"role_id "
               f"from sys_user where terminal_type = %s and role_id IN ({placeholders})")
        cursor = self.connection.cursor()
        # 参数
        param = [like_param] + list(ids)
        # 查询
        cursor.execute(sql, param)
        result = cursor.fetchall()
        self.connection.close()
        return [SysUser(*row) for row in result]

    """获取法律、服务顾问两岗还在职的账号"""
    def query_law_server_sys_user_list_during(self, ids):
        # 拼接占位符
        placeholders = ', '.join(['%s' for _ in ids])
        # 一些参数
        str_1 = 'TERMINAL_BIZ'
        like_param = f'{str_1}'
        # 查询语句
        sql = (f"select "
               f"user_id, "
               f"user_name, "
               f"nick_name,"
               f"role_id "
               f"from sys_user where del_flag = 0 and status = 0 and terminal_type = %s and role_id IN ({placeholders})")
        cursor = self.connection.cursor()
        # 参数
        param = [like_param] + list(ids)
        # 查询
        cursor.execute(sql, param)
        result = cursor.fetchall()
        self.connection.close()
        return [SysUser(*row) for row in result]

    """
    获取数据字典
    """
    def query_sys_dict_data_list(self, dict_type):
        sql = (f"select "
               f"dict_label, "
               f"dict_value "
               f"from sys_dict_data where dict_type = %s")
        cursor = self.connection.cursor()
        # 查询
        cursor.execute(sql, dict_type)
        result = cursor.fetchall()
        self.connection.close()
        return [SysDictData(*row) for row in result]