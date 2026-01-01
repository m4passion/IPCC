import glob
import multiprocessing
import os
import shutil
import sys
import subprocess
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_JOBS = int(multiprocessing.cpu_count() / 2)
work_dir = str(os.getcwd())

if sys.platform.startswith("win"):
    seven_zip_command = "7z"
else:
    seven_zip_command = "7zz"


def check_tools_usable():
    print("==== 开始依赖工具检查 ====")
    missing_tools = []

    if not shutil.which("ipsw"):
        missing_tools.append("ipsw")
    if not shutil.which(seven_zip_command):
        missing_tools.append(seven_zip_command)

    if missing_tools:
        print("[ERROR] 依赖工具检查未通过，请先安装以下依赖工具：")
        for tool in missing_tools:
            print(f"  - {tool} 工具不可用")
        sys.exit(1)

    print("==== 依赖工具检查通过 ====")


def process_ipsw(ipsw_file):
    ipsw_file_name = str(os.path.basename(ipsw_file).replace(".ipsw", ""))
    print(f"[{ipsw_file_name}] 开始处理...")

    base_detail_dir = os.path.join(work_dir, ipsw_file_name)
    ipcc_output_dir = os.path.join(work_dir, "ipcc", ipsw_file_name)

    if os.path.exists(ipcc_output_dir) and os.listdir(ipcc_output_dir):
        print(f"[WARN] [{ipsw_file_name}] 文件的输出目录中已存在处理完成的内容，将删除目录以重新生成文件")
        shutil.rmtree(ipcc_output_dir)

    os.makedirs(base_detail_dir, exist_ok=True)
    os.makedirs(ipcc_output_dir, exist_ok=True)

    try:
        print(f"[{ipsw_file_name}] 开始提取 .aea 或 .dmg 文件...")
        with zipfile.ZipFile(ipsw_file, 'r') as zip_ref:
            aea_files = [f for f in zip_ref.infolist() if f.filename.endswith('.aea')]
            if not aea_files:
                print(f"[WARN] [{ipsw_file_name}] 不存在 .aea 文件，尝试提取 .dmg 文件...")
                dmg_files = [f for f in zip_ref.infolist() if f.filename.endswith('.dmg')]
                if not dmg_files:
                    print(f"[ERROR] [{ipsw_file_name}] 不存在 .dmg 文件，结束该任务")
                    return
                largest_dmg_file = max(dmg_files, key=lambda x: x.file_size)
                try:
                    zip_ref.extract(largest_dmg_file, base_detail_dir)
                    dmg_file_name = os.path.basename(largest_dmg_file.filename)
                    dmg_file_path = os.path.join(base_detail_dir, dmg_file_name)
                except Exception as e:
                    print(f"[ERROR] [{ipsw_file_name}] 提取 .dmg 文件失败: {e}")
                    shutil.rmtree(base_detail_dir)
                    return
            else:
                largest_aea_file = max(aea_files, key=lambda x: x.file_size)
                try:
                    zip_ref.extract(largest_aea_file, base_detail_dir)
                    aea_file_name = os.path.basename(largest_aea_file.filename)
                    aea_file_path = os.path.join(base_detail_dir, aea_file_name)
                    try:
                        print(f"[{ipsw_file_name}] 开始解密 .aea 文件...")
                        subprocess.run(
                            ["ipsw", "fw", "aea", aea_file_path, "-o", base_detail_dir],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        try:
                            os.remove(aea_file_path)
                        except Exception:
                            pass
                        dmg_file_path = os.path.join(base_detail_dir, aea_file_name.replace(".aea", ""))
                    except subprocess.CalledProcessError:
                        print(f"[ERROR] [{ipsw_file_name}] .aea 文件解密失败")
                        return
                except Exception as e:
                    print(f"[ERROR] [{ipsw_file_name}] 解压 .aea 文件失败: {e}")
                    return


        if not os.path.exists(dmg_file_path):
            print(f"[{ipsw_file_name}] 提取失败，未生成或提取到 .dmg 文件")
            return

        print(f"[{ipsw_file_name}] 开始提取运营商配置文件...")
        temp_extract_dir = os.path.join(base_detail_dir, "_temp")
        os.makedirs(temp_extract_dir, exist_ok=True)

        try:
            subprocess.run(
                [
                    seven_zip_command, 'x', dmg_file_path,
                    'System/Library/Carrier Bundles/iPhone/*.bundle/*',
                    f'-o{temp_extract_dir}',
                    '-y', '-r'
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            print(f"[ERROR] [{ipsw_file_name}] 运营商配置文件提取失败")
            return


        carrier_path = os.path.join(temp_extract_dir, "System", "Library", "Carrier Bundles", "iPhone")
        if not os.path.exists(carrier_path):
            print(f"[{ipsw_file_name}] 未找到运营商配置文件目录")
            return

        for bundle_name in os.listdir(carrier_path):
            bundle_path = os.path.join(carrier_path, bundle_name)
            if not os.path.isdir(bundle_path) or not bundle_name.endswith('.bundle'):
                continue

            ipcc_file = os.path.join(ipcc_output_dir, f"{bundle_name}.ipcc")
            print(f"[{ipsw_file_name}] 生成 {bundle_name}.ipcc...")

            with tempfile.TemporaryDirectory() as temp_dir:
                payload_dir = os.path.join(temp_dir, "Payload")
                os.makedirs(payload_dir, exist_ok=True)
                shutil.copytree(bundle_path, os.path.join(payload_dir, bundle_name))

                with zipfile.ZipFile(ipcc_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arc_name)

        print(f"[{ipsw_file_name}] ipcc 文件已打包完成")
        shutil.rmtree(base_detail_dir, ignore_errors=True)
    except Exception as e:
        print(f"[{ipsw_file_name}] 处理异常: {e}")

def process_all_ipsw():
    ipsw_files = [
        os.path.join(os.getcwd(), f)
        for f in os.listdir()
        if f.lower().endswith('.ipsw')
    ]

    if not ipsw_files:
        print("[ERROR] 当前目录未找到任何 .ipsw 文件")
        sys.exit(1)

    with ThreadPoolExecutor(max_workers=MAX_JOBS) as executor:
        futures = {executor.submit(process_ipsw, f): f for f in ipsw_files}
        for future in as_completed(futures):
            file = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[{os.path.basename(file)}] 处理失败: {e}")

if __name__ == "__main__":
    try:
        check_tools_usable()
        process_all_ipsw()
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)
