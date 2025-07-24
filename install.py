#!/usr/bin/env python3
"""
ChatBI 自动安装脚本
自动检查和安装所需的依赖
"""
import subprocess
import sys
import os

def run_command(command, description):
    """运行命令并处理错误"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败:")
        print(f"错误信息: {e.stderr}")
        return False

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"🐍 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return False
    
    print("✅ Python 版本符合要求")
    return True

def check_pip():
    """检查 pip 是否可用"""
    try:
        import pip
        print("✅ pip 已安装")
        return True
    except ImportError:
        print("❌ pip 未安装")
        return False

def install_dependencies():
    """安装依赖"""
    print("\n📦 开始安装依赖...")
    
    # 升级 pip
    if not run_command("python -m pip install --upgrade pip", "升级 pip"):
        return False
    
    # 安装核心依赖
    core_packages = [
        "agently>=4.0.0",
        "flask==3.0.0", 
        "flask-cors==4.0.0",
        "flask-socketio==5.3.0",
        "sqlalchemy==2.0.23",
        "pandas==2.1.4",
        "numpy==1.24.4",
        "redis==5.0.1",
        "python-dotenv==1.0.0",
        "loguru==0.7.2"
    ]
    
    print("\n安装核心依赖包...")
    for package in core_packages:
        if not run_command(f"pip install {package}", f"安装 {package}"):
            print(f"⚠️  {package} 安装失败，继续安装其他包...")
    
    # 安装 AI 模型依赖
    ai_packages = [
        "openai==1.3.8",
        "dashscope==1.17.0"
    ]
    
    print("\n安装 AI 模型依赖...")
    for package in ai_packages:
        if not run_command(f"pip install {package}", f"安装 {package}"):
            print(f"⚠️  {package} 安装失败，继续安装其他包...")
    
    # 安装数据库连接器 (可选)
    db_packages = [
        "psycopg2-binary==2.9.9",  # PostgreSQL
        "pymysql==1.1.0"          # MySQL
    ]
    
    print("\n安装数据库连接器 (可选)...")
    for package in db_packages:
        if not run_command(f"pip install {package}", f"安装 {package}"):
            print(f"⚠️  {package} 安装失败，如果不使用对应数据库可以忽略")

def verify_installation():
    """验证安装"""
    print("\n🔍 验证关键依赖安装...")
    
    critical_modules = [
        "agently",
        "flask", 
        "flask_cors",
        "flask_socketio",
        "sqlalchemy",
        "pandas",
        "redis",
        "dotenv",
        "loguru"
    ]
    
    failed_modules = []
    
    for module in critical_modules:
        try:
            __import__(module)
            print(f"✅ {module} 导入成功")
        except ImportError as e:
            print(f"❌ {module} 导入失败: {e}")
            failed_modules.append(module)
    
    if failed_modules:
        print(f"\n⚠️  以下模块导入失败: {', '.join(failed_modules)}")
        print("请手动安装这些依赖:")
        for module in failed_modules:
            print(f"  pip install {module}")
        return False
    
    print("\n✅ 所有关键依赖验证通过！")
    return True

def create_env_file():
    """创建示例环境变量文件"""
    env_content = """# ChatBI 环境变量配置
# 请填写实际的配置值

# 通义千问 API 密钥 (必需)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 数据库连接
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=data_warehouse
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_URL=postgresql://your_db_user:your_db_password@localhost:5432/data_warehouse

# Flask 配置
FLASK_SECRET_KEY=chatbi-secret-key-please-change
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Redis 配置 (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ 已创建 .env 配置文件模板")
        print("请编辑 .env 文件，填写实际的配置值")
    else:
        print("📄 .env 文件已存在，跳过创建")

def main():
    """主函数"""
    print("🚀 ChatBI 自动安装脚本")
    print("=" * 50)
    
    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查 pip
    if not check_pip():
        print("请先安装 pip: https://pip.pypa.io/en/stable/installation/")
        sys.exit(1)
    
    # 安装依赖
    install_dependencies()
    
    # 验证安装
    if not verify_installation():
        print("\n❌ 安装验证失败，请检查错误信息")
        sys.exit(1)
    
    # 创建配置文件
    create_env_file()
    
    print("\n🎉 ChatBI 安装完成！")
    print("\n下一步:")
    print("1. 编辑 .env 文件，配置数据库和 API 密钥")
    print("2. 运行 'python main.py --check' 检查配置")
    print("3. 运行 'python main.py' 启动应用")

if __name__ == "__main__":
    main() 