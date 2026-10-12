import hashlib
import json
import os

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


class ConfigCrypto:
    def __init__(self, key=None):
        if key is None:
            key = os.getenv('CONFIG_ENCRYPTION_KEY')
        self.key = self._derive_key(key)

    @staticmethod
    def _derive_key(key):
        """从任意长度密钥派生固定长度密钥"""
        if isinstance(key, str):
            key = key.encode('utf-8')
        return hashlib.sha256(key).digest()

    def encrypt_config(self, config_data, output_path):
        """加密配置并保存到文件"""
        if isinstance(config_data, dict):
            config_str = json.dumps(config_data, ensure_ascii=False)
        else:
            config_str = str(config_data)

        # 生成随机IV
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # 加密数据
        encrypted_data = cipher.encrypt(pad(config_str.encode('utf-8'), AES.block_size))

        # 组合IV和加密数据
        result = iv + encrypted_data

        # 保存加密文件
        with open(output_path, 'wb') as f:
            f.write(result)

        print(f"配置已加密保存到: {output_path}")
        return output_path

    def decrypt_config(self, encrypted_file_path):
        """从加密文件解密配置"""
        with open(encrypted_file_path, 'rb') as f:
            data = f.read()

        # 提取IV和加密数据
        iv = data[:AES.block_size]
        encrypted_data = data[AES.block_size:]

        # 解密
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        # 尝试解析为JSON，否则返回字符串
        try:
            return json.loads(decrypted_data.decode('utf-8'))
        except json.JSONDecodeError:
            return decrypted_data.decode('utf-8')