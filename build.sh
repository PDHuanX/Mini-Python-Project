#!/bin/bash
# build.sh

# 清理之前的构建
rm -rf build/ dist/

# 加密配置文件
echo "加密配置文件中..."
python encrypt_config.py

# 打包应用
echo "打包应用中..."
pyinstaller main.spec

echo "构建完成！"