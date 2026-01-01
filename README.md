# 一、项目说明

通过解密`ipsw`镜像文件获取运营商配置文件，按照标准格式打包`ipcc`文件进行升级  
便于不想升级系统机型进行运营商配置升级，但是部分功能存在机型要求，即使完成升级也无法启用  

# 二、操作说明

- 使用`Python`提取`ipsw`固件中的镜像文件
  - ios18 开始 Apple 对 ipsw 文件里面的 dmg 进行的加密处理
- 若为加密镜像则使用`ipsw`工具对其进行解密
- 使用`7zip`工具提取镜像内的运营商配置文件，macOS也可直接挂载镜像文件
- 按照标准格式打包`ipcc`文件，并通过`爱思助手`刷写IPCC进行升级  

---

# 三、运行环境说明

## 1. Python 环境

Python 官方下载地址：https://www.python.org/downloads/

建议使用 Python 3.8 或后续版本

## 2. 7zip 解压缩工具

7zip 官方下载地址：https://www.7-zip.org/download.html

- macOS 安装7zip工具示例  
  如果在macOS设备上使用镜像挂载功能，可不安装7zip  
  7zip在macOS中命令行工具名称是`7zz`而非`7z`  
  ```bash
  mkdir 7zz && cd 7zz && wget https://www.7-zip.org/a/7z2501-mac.tar.xz # 下载二进制安装包到指定目录，以 7-Zip 25.01（2025-08-03）版本为例
  
  tar -xJf 7z2501-mac.tar.xz # 解压到当前目录的7z文件夹下
  
  chmod +x 7zz # 赋予文件可执行权限
  
  sudo cp 7zz /usr/local/bin/ # 复制文件
  
  cd .. && rm -rf 7zz # 删除压缩包等内容
  ```
  使用命令行时会触发macOS的隐私限制，需要在设置 → 隐私与安全性 → 安全性 → 允许使用7zz


- Windows  
  官网下载 .exe 安装包进行安装并在 环境变量 → 系统 → Path 中添加 7z 的安装路径  


- Linux
  ```bash
  mkdir 7z && cd 7z && wget https://www.7-zip.org/a/7z2501-linux-x64.tar.xz # 下载二进制安装包到指定目录，以 amd64 7-Zip 25.01（2025-08-03）版本为例
  
  tar -xJf 7z2501-linux-x64.tar.xz # 解压到当前目录的7z文件夹下
  
  chmod +x 7zz 7zzs # 赋予文件可执行权限
  
  
  sudo cp 7zz /usr/local/bin/ # 复制文件
  
  cd .. && rm -rf 7z # 删除压缩包等内容
  ```

## 3. IPSW 工具（提取 ios18 及以上系统版本时需要安装）

开源项目地址：https://github.com/blacktop/ipsw

### 3.1 macOS 

- 安装 brew 

  ```
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  brew update
  ```


- 安装 ipsw

  ```
  brew install ipsw
  ```

### 3.2 Windows

- 安装 scoop

  ```
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
  ```

- 安装 ipsw

  ```
  scoop bucket add blacktop https://github.com/blacktop/scoop-bucket.git 
  scoop install blacktop/ipsw
  ```

### 3.3 Linux

- 安装 snap

  ```
  # Ubuntu 可以跳过安装
  apt install snapd
  ```

- 安装 ipsw

  ```
  snap install ipsw
  ```

---

# 四、使用方法

1. 克隆仓库地址  
    ```bash
    git clone https://github.com/m4passion/ipcc.git
    ```
2. 将`ipsw` 文件放入仓库的根目录
3. 执行脚本处理固件
   - 通过命令行运行`python3 ipcc.py`开始处理 
   - macOS使用挂载镜像功能可通过命令行运行`python3 mac.py`开始处理
4. 等待脚本执行完毕
5. 打包完成的 `ipcc` 文件将存储于 `ipcc` 目录下的 `ipsw` 固件同名文件夹中
# 五、注意
1. 如果 `ipcc` 目录下已存在 `ipsw` 固件同名文件夹则将删除目录以重新生成文件
2. 如果在脚本执行提取以及解密 aea 文件时发生错误，请检查剩余空间是否充足或再次尝试