"""
关键单元格的下标，sheet.cell(column)是从1开始算
"""
# 20260306，在客户ID后新增一列旧单ID，后面的列下标+1
ADD_INDEX_ONE_20260306 = 1
# 20260320，在服务总次数列后，新增一列立案总次数，后面的列下标+1
ADD_INDEX_TOW_20260320 = 1
# 20260730，在分配顾问时间后面，新增一列调解户调解到期时间，后面的列下标+1
ADD_INDEX_THREE_20260730 = 1

class ColumnIndex:
    # 客户id
    CUSTOMER_ID = 1
    # 旧单ID,20260306新增
    OLD_CUSTOMER_ID = 2
    # 套餐次数
    SUM_COUNT = 2 + ADD_INDEX_ONE_20260306
    # 客户初始立案次数，20260320新增
    LAWSUIT_COUNT = 4
    # 剩余次数
    SURPLUS_COUNT = 3 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 客户名称
    COMPANY_NAME = 4 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 合同开始时间
    START_TIME = 5 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 合同结束时间
    END_TIME = 6 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 加选最长结束时间
    ADD_END_TIME = 7 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 套餐类型
    ITEM_MEAL = 8 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 行业分类
    INDUSTRY_TYPE = 9 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 联系人
    CONTACT = 10 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 联系方式
    CONTACT_PHONE = 11 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 是否建群
    IS_GROUP = 12 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 群ID
    ROOM_ID = 13 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 关联自然人、企业
    ASSOCIATED_PERSON = 14 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    ENTERPRISE_NAME = 15 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 谈单方式
    METHODS = 16 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 分公司名称
    SALESMAN_COMPANY = 17 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 债权（客服）
    STEWARD_NAME = 18 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 服务顾问
    SERVE_NAME = 19 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 法律顾问
    LAWERS = 20 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 合同顾问
    CONSULTANT_NAME = 21 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 销售
    SALESMAN_NAME = 22 + ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 到账时间
    ACCOUNTING_TIME = 23 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 收款金额
    RECEIVE_MONEY = 24 + ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 服务过程中加选金额
    ADD_ON_MONEY = 25 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 回购
    REPO = 26 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 单项
    SINGLE = 27 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 续费
    RENEWAL = 28 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 升级会员
    UPGRADE = 29 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 历史共计收款金额
    OLD_MONEY_COUNT = 30 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 收款大于等于10000元
    MORE_THAN_10000 = 31 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 我方收款公司
    PAYEE_NAME = 32 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 社会代码或身份证号
    CODE = 33 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 是否是续费
    IS_RENEWAL = 37 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 质检审核时间
    QUALITY_AUDIT_DATE = 44 + ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 签约主体
    PAYEE_OBJ = 45 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 分配顾问时间
    AFTER_TIME = 46 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320
    # 调解户调解到期时间（半年）
    MEMBER_END_TIME = 49
    # 是否在期
    IS_DURING = 47 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 是否已分配顾问
    IS_EXIST_LAW_SERVER = 48 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 交付次数
    HJ_COUNT = 49 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 起诉状
    QSZ = 50 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 指导立案
    ZDLA = 51 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 律师函
    LSH = 52 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 催款函
    CKH = 53 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 强制执行
    QZZX = 54 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 财产保全
    BQ = 55 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 答辩状
    DBZ = 56 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 合同起草与审核
    HTWS = 57 +  ADD_INDEX_ONE_20260306 + ADD_INDEX_TOW_20260320 + ADD_INDEX_THREE_20260730
    # 是否退款
    IS_REFUND = 61

"""程序2所需单元格下标，row[column].value因坐标从0开始故需要在ColumnIndex对应单元格坐标的基础上减1"""
"""这里是因为程序1和程序2的写法差异导致的过度设计，且程序2即便有备注说明作者也不敢轻易重构，另外这是自用，所以作者就干脆维护两套坐标了"""
class ColumnIndexTow:
    # 程序2获取的单元格需要减1
    @staticmethod
    def _procedure_tow_col_default_minus(column_index):
        return column_index - 1

    # 客户ID
    CUSTOMER_ID = _procedure_tow_col_default_minus(ColumnIndex.CUSTOMER_ID)
    # 续费旧单客户ID
    OLD_CUSTOMER_ID = _procedure_tow_col_default_minus(ColumnIndex.OLD_CUSTOMER_ID)
    # 公司名称
    COMPANY_NAME = _procedure_tow_col_default_minus(ColumnIndex.COMPANY_NAME)
    # 身份证号或统一信用号
    CODE = _procedure_tow_col_default_minus(ColumnIndex.CODE)
    # 联系方式
    CONTACT_PHONE = _procedure_tow_col_default_minus(ColumnIndex.CONTACT_PHONE)
    # 到账时间
    ACCOUNTING_TIME = _procedure_tow_col_default_minus(ColumnIndex.ACCOUNTING_TIME)
    # 服务顾问
    SERVE_NAME = _procedure_tow_col_default_minus(ColumnIndex.SERVE_NAME)
    # 法律顾问
    LAWERS = _procedure_tow_col_default_minus(ColumnIndex.LAWERS)
    # 套餐类型
    MEMBER_TYPE = _procedure_tow_col_default_minus(ColumnIndex.ITEM_MEAL)
    # 是否是续费
    IS_RENEWAL = _procedure_tow_col_default_minus(ColumnIndex.IS_RENEWAL)
    # 合同开始时间
    START_TIME = _procedure_tow_col_default_minus(ColumnIndex.START_TIME)
    # 合同结束时间
    END_TIME = _procedure_tow_col_default_minus(ColumnIndex.END_TIME)
    # 加选最长结束时间
    ADD_END_TIME = _procedure_tow_col_default_minus(ColumnIndex.ADD_END_TIME)
    # 收款金额
    RECEIVE_MONEY = _procedure_tow_col_default_minus(ColumnIndex.RECEIVE_MONEY)
    # 历史金额合计
    OLD_MONEY_COUNT = _procedure_tow_col_default_minus(ColumnIndex.OLD_MONEY_COUNT)
    # 续费
    RENEWAL = _procedure_tow_col_default_minus(ColumnIndex.RENEWAL)
    # 回购
    REPO = _procedure_tow_col_default_minus(ColumnIndex.REPO)
    # 签约公司
    SALESMAN_COMPANY = _procedure_tow_col_default_minus(ColumnIndex.SALESMAN_COMPANY)
    # 管家
    STEWARD_NAME = _procedure_tow_col_default_minus(ColumnIndex.STEWARD_NAME)
    # 销售
    SALESMAN_NAME = _procedure_tow_col_default_minus(ColumnIndex.SALESMAN_NAME)
    # 调解户调解到期时间（半年）
    MEMBER_END_TIME = _procedure_tow_col_default_minus(ColumnIndex.MEMBER_END_TIME)
    # 是否退款
    IS_REFUND = _procedure_tow_col_default_minus(ColumnIndex.IS_REFUND)
    # 质检审核时间
    QUALITY_AUDIT_DATE = _procedure_tow_col_default_minus(ColumnIndex.QUALITY_AUDIT_DATE)