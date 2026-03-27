#!/usr/bin/env python3
"""
Verilog源码批量注释工具
使用DeepSeek API对Verilog文件进行注释，生成Markdown文档
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import requests


class VerilogCommentGenerator:
    def __init__(self, api_key: str, model: str = "deepseek-chat", timeout: int =60, base_url: str = "https://api.deepseek.com"):
        """
        初始化注释生成器

        Args:
            api_key: DeepSeek API密钥
            model: 使用的模型名称
            base_url: API基础URL
            timeout: 服务器响应超时时间
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def read_verilog_file(file_path: str) -> str:
        """读取Verilog文件内容，尝试多种编码"""
        # 常见编码列表
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # 如果成功读取，打印使用的编码并返回
                    if encoding != encodings[0]:  # 如果不是默认编码，打印提示
                        print(f"   📖 使用编码: {encoding}")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"❌ 读取文件失败 {file_path}: {e}")
                return ""

    def generate_comment(self, verilog_code: str, file_name: str) -> str:
        """
        调用DeepSeek API生成代码注释

        Args:
            verilog_code: Verilog代码内容
            file_name: 文件名

        Returns:
            生成的Markdown格式注释文档
        """
        prompt = f"""请为以下Verilog代码生成详细的注释文档，输出格式为Markdown。

        文件名：{file_name}
        
        要求：
        1. 包含模块/顶层设计的整体功能描述
        2. 详细代码段注释
        3. 采用Markdown格式，包含适当的标题、列表、代码块等
        
        Verilog代码：
        ```verilog
        {verilog_code}
        请生成完整的注释文档（Markdown格式）："""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的硬件设计工程师，擅长Verilog代码分析和文档编写。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ API调用失败: {e}")
            return f"#生成失败：{str(e)}"

    def save_markdown(self, content: str, output_path: Path) -> bool:
        """保存Markdown文件"""

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ 保存文件失败 {output_path}: {e}")
            return False

    def process_file(self, verilog_path: str, output_dir: Path, include_code: bool = True) -> tuple:
        """
        处理单个Verilog文件

        Args:
        verilog_path: Verilog文件路径
        output_dir: 输出目录（Path对象）
        include_code: 是否在注释中包含源代码

        Returns:
        是否处理成功及错误信息:tuple: (success, error_message)
        """

        print(f"📝 处理文件: {verilog_path}")
        #读取Verilog代码
        verilog_code = self.read_verilog_file(verilog_path)
        if not verilog_code:
            return False,"读取文件失败"
        # 检查文件大小
        code_size = len(verilog_code)
        if code_size > 100000:  # 超过10万字符
            return False, f"文件过大 ({code_size} 字符)"

        #获取文件名（不含扩展名）
        file_name = Path(verilog_path).stem
        output_file = output_dir / f"{file_name}.md"

        #生成注释
        print(f" 🤖 调用DeepSeek API生成注释...")
        markdown_content = self.generate_comment(verilog_code, file_name)
        # 检查是否生成失败
        if "生成失败" in markdown_content or "失败" in markdown_content:
            return False, markdown_content

        #如果需要包含源代码
        if include_code:
            markdown_content += f"\n\n## 原始代码\n\nverilog\n{verilog_code}\n\n"

        #保存文件
        if self.save_markdown(markdown_content, output_file):
            print(f" ✅ 已保存: {output_file}")
            return True,None
        else:
            return False,"保存文件失败"

    def process_directory(self, root_dir: str, output_dir: str, extensions: List[str] = None,
                          recursive: bool = True, include_code: bool = True, delay: float = 1.0, overwrite: bool = False) -> Dict:
        """
        批量处理目录中的所有Verilog文件

        Args:
        root_dir: 根目录
        output_dir: 输出目录
        extensions: 文件扩展名列表
        recursive: 是否递归处理子目录
        include_code: 是否在注释中包含源代码
        delay: API调用之间的延迟（秒）
        overwrite: 是否覆盖已有文件写入

        Returns:
        处理结果统计
        """

        if extensions is None:
            extensions = ['.v', '.sv']

        root_path = Path(root_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        #收集所有Verilog文件
        verilog_files = []
        if recursive:
            for ext in extensions:
                verilog_files.extend(root_path.rglob(f"*{ext}"))
        else:
            for ext in extensions:
                verilog_files.extend(root_path.glob(f"*{ext}"))

        if not verilog_files:
            print("⚠️ 未找到Verilog文件")
            return {'total': 0, 'success': 0, 'failed': 0, 'files': []}

        print(f"📂 找到 {len(verilog_files)} 个Verilog文件")
        print("=" * 60)

        #处理统计
        stats = {
            'total': len(verilog_files),
            'success': 0,
            'failed': 0,  #失败的文件计数
            'skipped': 0,  #跳过的文件计数
            # 'success_files': [],  # 成功处理的文件列表
            'failed_files': [],    # 失败的文件详细信息列表
            # 'skipped_files': []   #跳过的文件列表
        }

        #处理每个文件
        for i, v_file in enumerate(verilog_files, 1):
            print(f"\n[{i}/{len(verilog_files)}]")

            #保持目录结构
            rel_path = v_file.relative_to(root_path)  #获取源文件的相对路径
            target_dir = output_path / rel_path.parent / "Readme"  #构建输出目录的完整路径：rel_path.parent获取父目录（去除文件名）
            target_dir.mkdir(parents=True, exist_ok=True)

            # 检查输出文件是否已存在
            output_file = target_dir / f"{v_file.stem}.md"
            if not overwrite and output_file.exists():
                print(f"   ⏭️  跳过已存在的文件: {output_file}")
                stats['skipped'] += 1
                # stats['skipped_files'].append({
                #     'file': str(v_file),
                #     # 'relative_path': str(rel_path),
                #     'directory': str(v_file.parent),
                #     'filename': v_file.name,
                #     'reason': '描述文件已存在'
                # })
                continue  # 跳过此文件

            #处理文件
            success, error_msg = self.process_file(str(v_file), target_dir, include_code)
            if success:
                stats['success'] += 1
                # stats['success_files'].append({'file': str(v_file)})
            else:
                stats['failed'] += 1
                stats['failed_files'].append({
                    'file': str(v_file),
                    # 'relative_path': str(rel_path),
                    'directory': str(v_file.parent),
                    'filename': v_file.name,
                    'error': error_msg or '未知错误'})

            #避免API限流
            if i < len(verilog_files):
                time.sleep(delay)  #等到delay后再访问服务器注释下一个文件

        return stats
def main():
    parser = argparse.ArgumentParser(description='使用DeepSeek API批量注释Verilog代码')
    parser.add_argument('input_dir', help='输入目录（包含Verilog源码）')
    parser.add_argument('output_dir', help='输出目录（存放Markdown注释文件）')
    parser.add_argument('--api-key', required=True, help='DeepSeek API密钥')
    parser.add_argument('--model', default='deepseek-chat', help='使用的模型名称')
    parser.add_argument('--extensions', nargs='+', default=['.v', '.sv', '.vh', '.svh'],
    help='Verilog文件扩展名')
    parser.add_argument('--no-recursive', action='store_true', help='不递归处理子目录')
    parser.add_argument('--no-code', action='store_true', help='不在注释中包含原始代码')
    parser.add_argument('--delay', type=float, default=1.0, help='API调用间隔（秒）')

    args = parser.parse_args()

    #创建生成器
    generator = VerilogCommentGenerator(
    api_key=args.api_key,
    model=args.model
    )

    #处理目录
    print("🚀 开始批量注释Verilog代码")
    print(f"📁 输入目录: {args.input_dir}")
    print(f"📁 输出目录: {args.output_dir}")
    print("=" * 60)

    stats = generator.process_directory(
    root_dir=args.input_dir,
    output_dir=args.output_dir,
    extensions=args.extensions,
    recursive=not args.no_recursive,
    include_code=not args.no_code,
    delay=args.delay
    )

    #输出统计信息

    print("\n" + "=" * 60)
    print("📊 处理完成统计:")
    print(f" 总文件数: {stats['total']}")
    print(f" 成功: {stats['success']}")
    print(f" 失败: {stats['failed']}")

    if stats['failed'] > 0:
        print("\n❌ 失败的文件:")
        for file_info in stats['files']:
            if file_info['status'] == 'failed':
                print(f" - {file_info['file']}")
if __name__ == "__main__":
        main()
