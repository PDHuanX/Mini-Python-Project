from src.utils.dict_result import DictResult
from src.mapper.online.db_update_impl import MysqlDatabase as UpdateMysqlDatabase

def public_rollback_status(view_data):
    return _rollback_status(view_data)

def _rollback_status(view_data):
    UpdateMysqlDatabase().rollback_status(view_data)
    return DictResult.success_response(status_code=200, message=f"回退事项[{view_data.get('serviceId')}]交付状态完成，请前往系统手动恢复已扣减的次数", types="rollback_status", data=None)