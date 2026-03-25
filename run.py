# 创建run.py
from VerilogCommenter import VerilogCommentGenerator
import config
from pathlib import Path
from collections import defaultdict
import time

def check_verilog_files(directory, extensions):
    """检查目录中是否有Verilog文件"""
    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"❌ 输入目录不存在: {directory}")
        print(f"   绝对路径: {dir_path.absolute()}")
        return False, []

    verilog_files = []
    for ext in extensions:
        verilog_files.extend(dir_path.rglob(f"*{ext}"))

    if not verilog_files:
        print(f"⚠️  在目录 {directory} 中未找到Verilog文件")
        print(f"   支持的文件扩展名: {', '.join(extensions)}")

        # 显示目录内容
        all_files = list(dir_path.rglob("*"))
        text_files = [f for f in all_files if f.is_file() and f.suffix in ['.txt', '.v']]
        if text_files:
            print(f"\n   目录中的文件:")
            for f in text_files[:10]:  # 只显示前10个
                print(f"     - {f.relative_to(dir_path)}")

        return False, []

    print(f"✅ 找到 {len(verilog_files)} 个Verilog文件:")
    for f in verilog_files[:5]:  # 显示前5个
        print(f"   - {f.relative_to(dir_path)}")
    if len(verilog_files) > 5:
        print(f"   ... 还有 {len(verilog_files) - 5} 个文件")

    return True, verilog_files


def save_failed_files_log(failed_files, output_file="failed_files.txt"):
    """保存失败文件列表到文件"""
    if not failed_files:
        return

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("Verilog注释失败文件列表\n")
            # f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"失败文件总数: {len(failed_files)}\n")
            f.write("=" * 80 + "\n\n")

            # 按目录分组显示
            failed_by_dir = defaultdict(list)
            for failed_file in failed_files:
                failed_by_dir[failed_file['directory']].append(failed_file)

            for directory, files in sorted(failed_by_dir.items()):
                f.write(f"\n📁 目录: {directory}\n")
                f.write(f"   失败文件数: {len(files)}\n")
                f.write("-" * 40 + "\n")
                for file_info in files:
                    f.write(f"   文件名: {file_info['filename']}\n")
                    f.write(f"   完整路径: {file_info['file']}\n")
                    f.write(f"   相对路径: {file_info['relative_path']}\n")
                    if 'error' in file_info:
                        f.write(f"   错误原因: {file_info['error']}\n")
                    f.write("\n")

        print(f"\n💾 失败文件列表已保存到: {output_file}")
    except Exception as e:
        print(f"\n⚠️  保存失败文件列表时出错: {e}")


def print_failed_files_detail(failed_files):
    """打印失败文件的详细信息"""
    if not failed_files:
        return

    print("\n" + "=" * 60)
    print(f"❌ 失败文件详情 (共 {len(failed_files)} 个):")
    print("=" * 60)

    # 按目录分组显示失败文件
    failed_by_dir = defaultdict(list)
    for failed_file in failed_files:
        failed_by_dir[failed_file['directory']].append(failed_file)

    for directory, files in sorted(failed_by_dir.items()):
        print(f"\n📁 目录: {directory}")
        print(f"   失败文件数: {len(files)}")
        for file_info in files:
            print(f"   ❌ {file_info['filename']}")
            print(f"      完整路径: {file_info['file']}")
            # print(f"      相对路径: {file_info['relative_path']}")
            if 'error' in file_info:
                print(f"      错误原因: {file_info['error']}")
def main():
    # 检查Verilog文件
    has_files, verilog_files = check_verilog_files(
        config.INPUT_DIR,
        config.FILE_EXTENSIONS
    )

    if not has_files:
        print("\n💡 建议:")
        print("   1. 确认Verilog文件扩展名是否正确 (.v, .sv, .vh, .svh)")
        print("   2. 检查文件是否在正确的目录中")
        print("   3. 尝试使用绝对路径而不是相对路径")
        print("   4. 运行 python check_files.py 进行详细诊断")
    #初始化DeepSeek注释生成器
    generator = VerilogCommentGenerator(
            api_key=config.DEEPSEEK_API_KEY,
            model=config.DEEPSEEK_MODEL,
            timeout= config.API_TIMEOUT
        )
    stats = generator.process_directory(
        root_dir=config.INPUT_DIR,
        output_dir=config.OUTPUT_DIR,
        extensions=config.FILE_EXTENSIONS,
        recursive=config.RECURSIVE,
        include_code=config.INCLUDE_CODE,
        delay=config.API_DELAY)
    #打印统计信息
    print("\n" + "=" * 60)
    print("📊 处理完成统计:")
    print(f"   总文件数: {stats['total']}")
    print(f"   ✅ 成功: {stats['success']}")
    print(f"   ❌ 失败: {stats['failed']}")
    # 如果有失败的文件，打印详细信息
    if stats['failed'] > 0 and 'failed_files' in stats:
        # 打印失败文件详情
        print_failed_files_detail(stats['failed_files'])
        # 保存失败文件列表到文件
        save_failed_files_log(stats['failed_files'], "failed_files.txt")

if __name__ == "__main__":
    main()


