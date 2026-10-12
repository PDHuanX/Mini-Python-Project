# 内部业务数据治理与自动化桌面工具

基于 PyQt 开发的桌面端业务数据治理工具，已交付实际使用。

## 功能概览

- 数据更新与导入
- 多维度业务数据提取
- 状态流转与异常处理
- 月初定时执行模块
- 操作日志记录

## 技术栈

- Python
- PyQt
- PyMySQL
- SQLite3
- PyInstaller

## 项目结构
src/
    ├── config/ # 配置（含加密配置）
    ├── entity/ # 数据实体
    ├── login/ # 登录模块
    ├── mapper/ # 数据访问层
    ├── service/ # 业务逻辑层
    └── utils/ # 工具类
main.py # 入口
main.spec # 打包配置
build.sh # 构建脚本