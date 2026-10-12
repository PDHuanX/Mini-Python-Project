import json
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, cast
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtCore import QUrl, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QShortcut, QDialog

from src.service.await_audit_postpone_service import public_get_await_audit_postpone, public_submit_batch_audit_postpone
from src.service.batch_insert_customer_service import public_batch_insert, public_get_user_list
from src.service.get_not_steward_service import public_get_not_steward
from src.service.get_salesman_delivery_service import public_get_salesman_delivery_main
from src.service.batch_insert_refound_service import public_batch_insert_refound
from src.service.sync_service import public_sync_main
from src.utils.dict_result import DictResult
from src.utils.logging_utils import loggings_info, loggings_error
from src.utils.paths_utils import get_resource_path
from src.service.batch_insert_mediate_upgrade_service import public_batch_insert_mediate_upgrade
from src.service.get_steward_server_during_service import public_get_steward_server_during_data_to_excel
from src.service.get_server_during_service import public_get_server_during_data
from src.service.get_law_during_service import public_get_law_during_data
from src.service.get_law_out_service import public_get_law_out_date_data
from src.service.get_server_out_service import public_get_server_out_date_data
from src.service.get_salesman_company_during_service import public_get_salesman_company_during_data
from src.service.get_two_job_during_and_out_customer_service import public_get_two_job_during_and_out_customer
from src.service.get_delivery_url_service import public_get_delivery_url_data
from src.service.get_register_data_service import public_get_register_data
from src.service.get_steward_server_during_new_service import public_get_steward_server_during_data_to_excel_new
from src.service.sys_role_service import public_add_role, public_get_role_list, public_update_role
from src.service.sys_function_service import public_get_fun_list, public_add_function, public_update_function
from src.service.sys_user_service import public_get_sys_user_list, public_update_sys_user, public_add_sys_user
from src.login.login_dialog import LoginDialog
from src.utils.session_utils import load_session
from src.service.rollback_status_service import public_rollback_status
from src.service.get_pause_service import public_get_pause_service
from src.service.get_delay_service import public_get_delay_service
from src.service.get_warning_service import public_get_warning_service
from src.service.get_overdue_service import public_get_overdue_service
from src.service.get_shelve_case_register_service import public_get_shelve_case_register_service
from src.service.get_submit_case_register_service import public_get_submit_case_register_service
from src.service.get_server_month_add_service import public_get_server_month_add_service


# 常量定义
class WhiteList:
    WHITE_LIST = {
        "get_my_functions"
    }

class MessageType:
    SYNC_DATA_INFO = 'sync_data_info'
    GET_USER_LIST = 'get_user_list'
    BATCH_INSERT = 'batch_insert'
    GET_SALESMAN_DELIVERY = 'get_salesman_delivery'
    GET_NOT_STEWARD_LIST = 'get_not_steward_list'
    GET_AWAIT_AUDIT_POSTPONE = 'get_await_audit_postpone'
    SUBMIT_BATCH_AUDIT_POSTPONE = 'submit_batch_audit_postpone'
    BATCH_INSERT_REFOUND = 'batch_insert_refound'
    BATCH_INSERT_MEDIATE_UPGRADE = 'batch_insert_mediate_upgrade'
    GET_STEWARD_SERVER_DURING_DATA_TO_EXCEL = 'get_steward_server_during_data_to_excel'
    SUBMIT_GET_SERVER_DURING_DATA = 'submit_get_server_during_data'
    SUBMIT_GET_LAW_DURING_DATA = 'submit_get_law_during_data'
    SUBMIT_GET_LAW_OUT_DATE_DATA = 'submit_get_law_out_date_data'
    SUBMIT_GET_SERVER_OUT_DATE_DATA = 'submit_get_server_out_date_data'
    SUBMIT_GET_SALESMAN_COMPANY_DURING_DATA = 'submit_get_salesman_company_during_data'
    SUBMIT_TWO_JOB_DURING_AND_OUT_CUSTOMER_DATA = 'submit_get_two_job_during_and_out_customer_data'
    SUBMIT_GET_DELIVERY_URL_DATA = "submit_get_delivery_url_data"
    SUBMIT_GET_REGISTER_DAY_ZERO_DATA = "submit_get_register_day_zero_data"
    GET_STEWARD_SERVER_DURING_DATA_TO_EXCEL_NEW = "get_steward_server_during_data_to_excel_new"
    ADD_ROLE = "add_role"
    GET_ROLE_LIST = "get_role_list"
    UPDATE_ROLE = "update_role"
    GET_FUN_LIST = "get_fun_list"
    ADD_FUNCTION = "add_function"
    UPDATE_FUNCTION = "update_function"
    GET_SYS_USER_LIST = "get_sys_user_list"
    ADD_SYS_USER = "add_sys_user"
    UPDATE_SYS_USER = "update_sys_user"
    GET_MY_FUNCTIONS = "get_my_functions"
    ROLLBACK_STATUS = "rollback_status",
    GET_PAUSE_SERVICE = "get_pause_service"
    GET_DELAY_SERVICE = "get_delay_service"
    GET_WARNING_SERVICE = "get_warning_service"
    GET_OVERDUE_SERVICE = "get_overdue_service"
    GET_SHELVE_CASE_REGISTER_SERVICE = "get_shelve_case_register_service"
    GET_SUBMIT_CASE_REGISTER_SERVICE = "get_submit_case_register_service"
    GET_SERVER_MONTH_ADD_SERVICE = "get_server_month_add_service"

class ErrorMessages:
    UNKNOWN_MESSAGE_TYPE = "未知类型"
    JSON_PARSE_ERROR = "JSON解析失败"
    FILE_NOT_FOUND = "HTML文件未找到"
    UNKNOWN_ERROR = "未知错误"
    NOT_SESSION = "会话已失效，请重新登录"
    NOT_AUTHORIZATION = "无权限执行此操作"

"""桥接类 - 处理前后端通信"""
class Bridge(QObject):
    # 定义信号用于向前端发送响应
    jsMessageResponse = pyqtSignal(str)

    # 错误响应模板
    ERROR_RESPONSE = DictResult.error_response(
        message=ErrorMessages.UNKNOWN_MESSAGE_TYPE,
        status_code=500,
        types="404 Not Found",
        data=None
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._message_handlers = {
            MessageType.SYNC_DATA_INFO: self._handle_sync_data,
            MessageType.GET_USER_LIST: self._handle_get_user_list,
            MessageType.BATCH_INSERT: self._handle_batch_insert,
            MessageType.GET_SALESMAN_DELIVERY: self._handle_salesman_delivery,
            MessageType.GET_NOT_STEWARD_LIST: self._handle_not_steward,
            MessageType.GET_AWAIT_AUDIT_POSTPONE: self._handle_get_await_audit_postpone,
            MessageType.SUBMIT_BATCH_AUDIT_POSTPONE: self._handle_submit_batch_audit_postpone,
            MessageType.BATCH_INSERT_REFOUND: self._handle_batch_insert_refound,
            MessageType.BATCH_INSERT_MEDIATE_UPGRADE: self._handle_batch_insert_mediate_upgrade,
            MessageType.GET_STEWARD_SERVER_DURING_DATA_TO_EXCEL: self._handle_get_steward_server_during_data_to_excel,
            MessageType.SUBMIT_GET_SERVER_DURING_DATA: self._handle_get_server_during_data,
            MessageType.SUBMIT_GET_LAW_DURING_DATA: self._handle_get_law_during_data,
            MessageType.SUBMIT_GET_LAW_OUT_DATE_DATA: self._handle_get_law_out_date_data,
            MessageType.SUBMIT_GET_SERVER_OUT_DATE_DATA: self._handle_get_server_out_date_data,
            MessageType.SUBMIT_GET_SALESMAN_COMPANY_DURING_DATA: self._handle_get_salesman_company_during_data,
            MessageType.SUBMIT_TWO_JOB_DURING_AND_OUT_CUSTOMER_DATA: self._handle_get_two_job_during_and_out_customer_data,
            MessageType.SUBMIT_GET_DELIVERY_URL_DATA: self._handle_get_delivery_url_data,
            MessageType.SUBMIT_GET_REGISTER_DAY_ZERO_DATA: self._handle_get_register_day_zero_data,
            MessageType.GET_STEWARD_SERVER_DURING_DATA_TO_EXCEL_NEW: self._handle_get_steward_server_during_data_to_excel_new,
            MessageType.ADD_ROLE: self._handle_add_role_,
            MessageType.GET_ROLE_LIST: self._handle_get_role_list_,
            MessageType.UPDATE_ROLE: self._handle_update_role_,
            MessageType.GET_FUN_LIST: self._handle_get_fun_list_,
            MessageType.ADD_FUNCTION: self._handle_add_function_,
            MessageType.UPDATE_FUNCTION: self._handle_update_function_,
            MessageType.GET_SYS_USER_LIST: self._handle_get_sys_user_list_,
            MessageType.ADD_SYS_USER: self._handle_add_sys_user_,
            MessageType.UPDATE_SYS_USER: self._handle_update_sys_user_,
            MessageType.GET_MY_FUNCTIONS: self._handle_get_my_functions,
            MessageType.ROLLBACK_STATUS: self._handle_rollback_status,
            MessageType.GET_PAUSE_SERVICE: self._handle_get_pause_service,
            MessageType.GET_DELAY_SERVICE: self._handle_get_delay_service,
            MessageType.GET_WARNING_SERVICE: self._handle_get_warning_service,
            MessageType.GET_OVERDUE_SERVICE: self._handle_get_overdue_service,
            MessageType.GET_SHELVE_CASE_REGISTER_SERVICE: self._handle_get_shelve_case_register_service,
            MessageType.GET_SUBMIT_CASE_REGISTER_SERVICE: self._handle_get_submit_case_register_service,
            MessageType.GET_SERVER_MONTH_ADD_SERVICE: self._handle_get_server_month_add_service,
        }
        self.jsMessageResponse = cast(pyqtSignal, self.jsMessageResponse)

    """程序分支，对页面唯一接口"""
    @pyqtSlot(str)
    def handle_js_message(self, view_data: str) -> str:
        """处理来自JavaScript的消息"""
        loggings_info(f"收到来自JavaScript的消息: {view_data}")

        session = load_session()
        if not session:
            # 理论上不会走到这里，但作为兜底
            res = DictResult.error_response(
                message= ErrorMessages.NOT_SESSION,
                status_code=401,
                types="unauthorized",
                data=None
            )
            self.jsMessageResponse.emit(json.dumps(res.to_dict()))
            return ""

        data = json.loads(view_data)
        message_type = data.get('type')

        # 获取当前账号的信息，关键的参数在function_keys
        handler_function = self._message_handlers.get("get_my_functions")
        json_result = handler_function(self=self, data=data)
        function_keys = []
        if json_result.data and "function_keys" in json_result.data:
            for role_dict in json_result.data.get("function_keys"):
                function_keys.append(role_dict.get("function_key"))
                # 这里要判断后续按钮的权限
                if role_dict.get("function_button"):
                    function_keys.extend(role_dict.get("function_button").split(','))

        # 权限校验：检查请求的函数接口message_type是否存在function_keys中
        if message_type not in function_keys and message_type not in WhiteList.WHITE_LIST:
            res = DictResult.error_response(
                message= ErrorMessages.NOT_AUTHORIZATION,
                status_code=403,
                types="Not Authorized",
                data=None
            )
            self.jsMessageResponse.emit(json.dumps(res.to_dict()))
            return ""

        try:
            # 查找对应的处理器
            handler = self._message_handlers.get(message_type)
            if handler:
                res = handler(self=self, data=data)
            else:
                res = self.ERROR_RESPONSE

            loggings_info(res.to_dict())
            # 发送响应信号
            self.jsMessageResponse.emit(json.dumps(res.to_dict()))

        except json.JSONDecodeError as e:
            error_response = DictResult.error_response(
                message=f"{ErrorMessages.JSON_PARSE_ERROR}: {str(e)}",
                status_code=400,
                types="JSON Parse Error",
                data=None
            )
            loggings_error(f"原始请求: {view_data}")
            loggings_error(error_response.to_dict())
            loggings_error(traceback.format_exc())
            self.jsMessageResponse.emit(json.dumps(error_response.to_dict()))
        except Exception as e:
            error_response = DictResult.error_response(
                message=f"{ErrorMessages.UNKNOWN_ERROR}: {str(e)}",
                status_code=500,
                types="Internal Server Error",
                data=None
            )
            loggings_error(f"原始请求: {view_data}")
            loggings_error(f"消息类型: {data.get('type') if isinstance(data, dict) else '未知'}")
            loggings_error(error_response.to_dict())
            loggings_error(traceback.format_exc())
            self.jsMessageResponse.emit(json.dumps(error_response.to_dict()))

        return ""

    @staticmethod
    def _handle_get_server_month_add_service(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_server_month_add_service(data)

    @staticmethod
    def _handle_get_submit_case_register_service(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_submit_case_register_service(data)

    @staticmethod
    def _handle_get_shelve_case_register_service(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        _ = data
        return public_get_shelve_case_register_service()

    @staticmethod
    def _handle_get_overdue_service(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_overdue_service(data)

    @staticmethod
    def _handle_get_warning_service(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        _ = data
        return public_get_warning_service()

    @staticmethod
    def _handle_get_delay_service(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_delay_service(data)

    @staticmethod
    def _handle_get_pause_service(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_pause_service(data)

    @staticmethod
    def _handle_rollback_status(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_rollback_status(data)

    @staticmethod
    def _handle_update_sys_user_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_update_sys_user(data)

    @staticmethod
    def _handle_add_sys_user_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_add_sys_user(data)

    @staticmethod
    def _handle_get_sys_user_list_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        _ = data
        return public_get_sys_user_list()

    @staticmethod
    def _handle_update_function_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_update_function(data)

    @staticmethod
    def _handle_add_function_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_add_function(data)

    @staticmethod
    def _handle_get_fun_list_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_fun_list(data)

    @staticmethod
    def _handle_update_role_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_update_role(data)

    @staticmethod
    def _handle_add_role_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_add_role(data)

    @staticmethod
    def _handle_get_role_list_(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_role_list(data)

    @staticmethod
    def _handle_sync_data(self, data: Dict[str, Any]) -> DictResult:
        """因为调用方式，需要保持函数入参一致性，但右上角警告挺烦的，所以忽略"""
        _ = self
        return public_sync_main(
            main_file_name=data.get('oldFileName'),
            out_file_name=data.get('newFileName')
        )

    @staticmethod
    def _handle_get_user_list(self, data: Dict[str, Any]) -> DictResult:
        """因为调用方式，需要保持函数入参一致性，但右上角警告挺烦的，所以忽略"""
        _ = self
        _ = data
        return public_get_user_list()

    @staticmethod
    def _handle_batch_insert(self, data: Dict[str, Any]) -> DictResult:
        """因为调用方式，需要保持函数入参一致性，但右上角警告挺烦的，所以忽略"""
        _ = self
        return public_batch_insert(data)

    @staticmethod
    def _handle_salesman_delivery(self, data: Dict[str, Any]) -> DictResult:
        """因为调用方式，需要保持函数入参一致性，但右上角警告挺烦的，所以忽略"""
        _ = self
        return public_get_salesman_delivery_main(data)

    @staticmethod
    def _handle_not_steward(self, data: Dict[str, Any]) -> DictResult:
        """因为调用方式，需要保持函数入参一致性，但右上角警告挺烦的，所以忽略"""
        _ = self
        return public_get_not_steward(data)

    @staticmethod
    def _handle_get_await_audit_postpone(self, data: Dict[str, Any]) -> DictResult:
        """因为调用方式，需要保持函数入参一致性，但右上角警告挺烦的，所以忽略"""
        _ = self
        _ = data
        return public_get_await_audit_postpone()

    @staticmethod
    def _handle_submit_batch_audit_postpone(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_submit_batch_audit_postpone(data)

    @staticmethod
    def _handle_batch_insert_refound(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_batch_insert_refound(data)

    @staticmethod
    def _handle_batch_insert_mediate_upgrade(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_batch_insert_mediate_upgrade(data)

    @staticmethod
    def _handle_get_steward_server_during_data_to_excel_new(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_steward_server_during_data_to_excel_new(data)

    @staticmethod
    def _handle_get_steward_server_during_data_to_excel(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_steward_server_during_data_to_excel(data)

    @staticmethod
    def _handle_get_server_during_data(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_server_during_data(data)

    @staticmethod
    def _handle_get_law_during_data(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_law_during_data(data)

    @staticmethod
    def _handle_get_law_out_date_data(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_law_out_date_data(data)

    @staticmethod
    def _handle_get_server_out_date_data(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_server_out_date_data(data)

    @staticmethod
    def _handle_get_salesman_company_during_data(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_salesman_company_during_data(data)

    @staticmethod
    def _handle_get_two_job_during_and_out_customer_data(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_two_job_during_and_out_customer(data)

    @staticmethod
    def _handle_get_delivery_url_data(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        return public_get_delivery_url_data(data)

    @staticmethod
    def _handle_get_register_day_zero_data(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        _ = data
        return public_get_register_data()

    @staticmethod
    def _handle_get_my_functions(self, data: Dict[str, Any]) -> DictResult:
        _ = self
        _ = data
        session = load_session()
        if not session:
            return DictResult.error_response("未登录", 401, "get_my_functions", None)
        return DictResult.success_response(
            message="获取成功",
            status_code=200,
            types="get_my_functions",
            data={
                "sys_user_id": session["sys_user_id"],
                "sys_user_name": session["sys_user_name"],
                "sys_user_nick_name": session["sys_user_nick_name"],
                "function_keys": session["function_keys"]
            }
        )

"""主窗口类"""
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._setup_web_view()
        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        """设置快捷键"""
        reload_shortcut = QShortcut(QKeySequence("F5"), self)
        reload_shortcut.activated.connect(self.web_view.reload)

    def _init_ui(self) -> None:
        """初始化UI界面"""
        self.setWindowTitle("功能窗口")
        self.setGeometry(50, 50, 1000, 900)

        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

    def _setup_web_view(self) -> None:
        """设置Web视图"""
        # 创建Web视图
        self.web_view = QWebEngineView()

        # 创建并配置WebChannel
        self._setup_web_channel()

        # 加载HTML内容
        self._load_html_content()

        # 添加到布局
        self.layout.addWidget(self.web_view)

    def _setup_web_channel(self) -> None:
        """配置WebChannel通信"""
        self.channel = QWebChannel()
        self.bridge = Bridge()

        # 将桥接对象注册到WebChannel
        self.channel.registerObject("bridge", self.bridge)

        # 将WebChannel设置到页面
        self.web_view.page().setWebChannel(self.channel)

    def _load_html_content(self) -> None:
        """加载HTML内容"""
        html_path = get_resource_path("html")
        html_file = Path(html_path) / "view.html"

        if not html_file.exists():
            loggings_error(f"错误: {ErrorMessages.FILE_NOT_FOUND}")
            self.web_view.setHtml("<h1>页面加载失败</h1>")
            return

        # 用 load() 加载本地文件，保留真实 URL
        self.web_view.load(QUrl.fromLocalFile(str(html_file.resolve())))

    @staticmethod
    def _read_html_file() -> str:
        """读取HTML文件内容"""
        html_path = get_resource_path("html")
        html_file = Path(html_path) / "view.html"

        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()

def main() -> None:
    """主函数"""
    import os
    os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

    """主函数"""
    app = QApplication(sys.argv)

    # 清楚缓存，避免二次打开失败
    QWebEngineProfile.defaultProfile().setHttpCacheType(
        QWebEngineProfile.HttpCacheType.NoCache
    )

    # 先弹登录
    login_dialog = LoginDialog()
    if login_dialog.exec_() != QDialog.Accepted:
        sys.exit(0)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 执行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()