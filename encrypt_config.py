import base64
import secrets

from src.config.config_crypto import ConfigCrypto
from src.utils.paths_utils import get_resource_path


# 生成 base64 编码的密钥（便于存储）
def generate_base64_key(length=32):
    """生成 base64 编码的密钥"""
    key_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(key_bytes).decode('utf-8')

def main():
    # 需要加密的配置文件路径
    config_path = get_resource_path("resources/config.ini")
    # 密钥输出文件路径
    secret_key_path = get_resource_path("resources/secret.key")

    # 先生成一个key，保证每次程序用的都是新的
    secret_key = generate_base64_key()

    # 直接写，不需要额外参数
    with open(secret_key_path, 'w', encoding='utf-8') as f:
        f.write(secret_key)

    # 读取配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()

    # 加密配置文件
    crypto = ConfigCrypto(secret_key)
    crypto.encrypt_config(config_content, "resources/config.encrypted")

if __name__ == '__main__':
    main()