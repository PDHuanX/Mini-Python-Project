import os
import sys
from pathlib import Path

"""
获取资源路径，如果当前.py文件向下迁移一个目录，相应的路径就要加上一个parent
"""
def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        # 打包后的环境（单目录环境）
        base_path = os.path.join(Path(sys.executable).parent, "_internal")
    else :
        # 系统根目录
        base_path = Path(__file__).parent.parent.parent

    data_dir = os.path.join(base_path, relative_path)
    # 判断路径是否存在
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f'目录不存在：{data_dir}')

    return data_dir