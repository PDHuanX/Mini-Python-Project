from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from src.login.auth_service import login
from src.utils.session_utils import save_session

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录")
        self.setFixedSize(320, 180)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("用户名："))
        self.username_input = QLineEdit()
        user_layout.addWidget(self.username_input)
        layout.addLayout(user_layout)

        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(QLabel("密  码："))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        pwd_layout.addWidget(self.password_input)
        layout.addLayout(pwd_layout)

        self.login_btn = QPushButton("登录")
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)

        self.password_input.returnPressed.connect(self._on_login)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return

        try:
            session = login(username, password)
            save_session(session)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "登录失败", str(e))
            self.password_input.clear()
            self.password_input.setFocus()