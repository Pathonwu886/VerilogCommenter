# config.py
# 配置文件示例
import os
from pathlib import Path
# DeepSeek API配置
DEEPSEEK_API_KEY = "add your api_key here"
DEEPSEEK_MODEL = "deepseek-chat"

# 处理配置
INPUT_DIR = "./rc4"      # Verilog源码目录
OUTPUT_DIR = "./rc4"     # 输出文档目录
# 确保路径存在
if not os.path.exists(INPUT_DIR):
    print(f"⚠️  警告: 输入目录不存在: {INPUT_DIR}")
    print(f"   当前工作目录: {os.getcwd()}")
    print(f"   请检查路径是否正确")
FILE_EXTENSIONS = ['.v', '.sv']  # 支持的文件扩展名
RECURSIVE = True                  # 是否递归处理子目录
INCLUDE_CODE = True               # 是否在注释中包含原始代码
API_DELAY = 2.0                   # API调用间隔（秒）
#其他配置
API_TIMEOUT = 60                 # 服务器响应超时时间（秒）
OVERWRITE = False                #是否覆盖描述文件，默认否
