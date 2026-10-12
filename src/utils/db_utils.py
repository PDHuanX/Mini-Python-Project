import configparser
import sys

import pymysql
from dbutils.pooled_db import PooledDB

from src.config.config_crypto import ConfigCrypto
from src.utils import paths_utils as paths


# 获取配置文件
def create_connection_pymysql():
    # 获取文件路径
    base_dir = paths.get_resource_path("resources")

    config = configparser.ConfigParser()
    if getattr(sys, 'frozen', False):
        # 打包后环境，读取配置文件前，先读取密钥文件获取密钥
        with open(f"{base_dir}/secret.key", 'r', encoding='utf-8') as f:
            secret_key = f.read()

        # 读取密钥后创建对象
        crypto = ConfigCrypto(secret_key)
        # 进行配置文件解密，这里大概率返回的是文本，所以只当文本处理
        text = crypto.decrypt_config(f"{base_dir}/config.encrypted")
        config.read_string(text)
    else :
        # 开发环境，直接读取配置文件
        config.read(f"{base_dir}/config.ini")

    config_data = {
        'host': config.get('database', 'host'),
        'port': config.getint('database', 'port'),
        'user': config.get('database', 'user'),
        'password': config.get('database', 'password'),
        'database': config.get('database', 'database'),
    }

    # 使用链接池
    pooled_db = PooledDB(
        creator=pymysql,
        maxconnections=config.getint('database', 'pool_size', fallback=10),
        mincached=2,
        maxcached=5,
        maxshared=3,
        blocking=True,
        maxusage=None,
        setsession=[],
        ping=0,
        **config_data
    )

    return pooled_db