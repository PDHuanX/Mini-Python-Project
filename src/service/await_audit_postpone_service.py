from src.mapper.online.db_query_impl import MysqlDatabase as QueryMysqlDatabase
from src.mapper.online.db_update_impl import MysqlDatabase as UpdateMysqlDatabase
from src.utils.dict_result import DictResult

"""批量处理待审批数据"""
def public_submit_batch_audit_postpone(data):
    # 先获取主要参数
    change_dict = data["changeData"]

    # 然后获取所有的key，这个key是延期交付记录表的主键，用于修改审核状态
    delay_ids = list(change_dict.keys())

    # 对延期交付记录表执行修改
    UpdateMysqlDatabase().update_delay_record_by_delay_ids(delay_ids= delay_ids, audit_status= data['auditStatus'])

    if 'OK' == data['auditStatus'] or 'ok' == data['auditStatus']:
        # 修改完审核表后，且必须是同意，需要对服务项目记录表的计划完成时间进行修改
        UpdateMysqlDatabase().update_service_record_by_service_ids(data=data)

    return DictResult.success_response(status_code= 200, message=f"批量处理待审批{len(delay_ids)}条数据成功", types="submit_batch_audit_postpone", data=None)

"""获取待审核列表"""
def public_get_await_audit_postpone():
    result = QueryMysqlDatabase().get_await_audit_postpone_list()
    return DictResult.success_response(status_code= 200, message="获取待审核列表成功", types="get_await_audit_postpone", data=result)
