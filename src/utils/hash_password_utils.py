import bcrypt

def hash_password(plain: str) -> str:
    """把明文密码转成哈希字符串"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode(), salt)
    return hashed.decode()

def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码和哈希是否匹配"""
    return bcrypt.checkpw(plain.encode(), hashed.encode())