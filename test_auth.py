#!/usr/bin/env python3
"""
认证功能测试脚本
测试用户注册、登录、密码验证等功能
"""

from auth_config import auth_config
from config import Config
from loguru import logger
import traceback

def test_password_validation():
    """测试密码验证功能"""
    print("=== 密码验证测试 ===")
    
    test_cases = [
        ("123", False, "密码长度至少6位"),
        ("password", False, "密码必须包含大写字母"),
        ("PASSWORD", False, "密码必须包含小写字母"),
        ("Password", False, "密码必须包含符号"),
        ("Pass@123", True, "密码符合要求"),
        ("MySecure!Pass", True, "密码符合要求"),
    ]
    
    for password, expected_valid, expected_msg in test_cases:
        valid, msg = auth_config.validate_password(password)
        status = "✅" if valid == expected_valid else "❌"
        print(f"{status} 密码: '{password}' -> {msg}")
        
        if valid != expected_valid:
            print(f"   期望: {expected_valid}, 实际: {valid}")

def test_allowed_employees():
    """测试允许注册的工号"""
    print("\n=== 允许注册工号测试 ===")
    
    allowed_employees = auth_config.get_allowed_employees()
    print(f"允许注册的工号: {allowed_employees}")
    
    test_employees = ["50992", "10001", "99999"]
    for emp_id in test_employees:
        allowed = auth_config.is_employee_allowed(emp_id)
        status = "✅" if allowed else "❌"
        print(f"{status} 工号 {emp_id}: {'允许' if allowed else '不允许'}注册")

def test_database_mapping():
    """测试数据库映射"""
    print("\n=== 数据库映射测试 ===")
    
    mapping = auth_config.get_database_mapping()
    print(f"数据库映射配置: {len(mapping)} 个工号")
    
    for emp_id, config in mapping.items():
        print(f"工号 {emp_id}: {config['database_type']}://{config['database_name']} - {config['description']}")

def test_user_registration():
    """测试用户注册"""
    print("\n=== 用户注册测试 ===")
    
    # 测试成功注册
    test_employee_id = "50992"
    test_password = "TestPass@123"
    test_name = "测试用户"
    
    success, message = auth_config.register_user(test_employee_id, test_password, test_name)
    status = "✅" if success else "❌"
    print(f"{status} 注册工号 {test_employee_id}: {message}")
    
    # 测试重复注册
    if success:
        success2, message2 = auth_config.register_user(test_employee_id, test_password, test_name)
        status2 = "❌" if not success2 else "✅"
        print(f"{status2} 重复注册测试: {message2}")
    
    # 测试不允许的工号
    success3, message3 = auth_config.register_user("99999", test_password, "非法用户")
    status3 = "❌" if not success3 else "✅"
    print(f"{status3} 非法工号注册: {message3}")

def test_user_authentication():
    """测试用户认证"""
    print("\n=== 用户认证测试 ===")
    
    test_employee_id = "50992"
    correct_password = "TestPass@123"
    wrong_password = "WrongPass@123"
    
    # 测试正确密码
    success1, user_info1 = auth_config.authenticate_user(test_employee_id, correct_password)
    status1 = "✅" if success1 else "❌"
    print(f"{status1} 正确密码登录: {'成功' if success1 else '失败'}")
    if success1:
        print(f"   用户信息: {user_info1['name']}, 数据库: {user_info1['database_config']['database_name']}")
    
    # 测试错误密码
    success2, user_info2 = auth_config.authenticate_user(test_employee_id, wrong_password)
    status2 = "❌" if not success2 else "✅"
    print(f"{status2} 错误密码登录: {'成功' if success2 else '失败'}")
    
    # 测试不存在的用户
    success3, user_info3 = auth_config.authenticate_user("99999", correct_password)
    status3 = "❌" if not success3 else "✅"
    print(f"{status3} 不存在用户登录: {'成功' if success3 else '失败'}")

def test_user_database_config():
    """测试用户数据库配置"""
    print("\n=== 用户数据库配置测试 ===")
    
    test_employee_id = "50992"
    db_config = auth_config.get_user_database_config(test_employee_id)
    
    if db_config:
        print(f"✅ 用户 {test_employee_id} 数据库配置:")
        print(f"   数据库名: {db_config['database_name']}")
        print(f"   描述: {db_config['description']}")
        print(f"   连接URL: {db_config['db_url']}")
    else:
        print(f"❌ 用户 {test_employee_id} 没有数据库配置")

def show_config_files():
    """显示配置文件路径"""
    print("\n=== 配置文件路径 ===")
    print(f"允许注册工号文件: {auth_config.allowed_employees_file}")
    print(f"数据库映射文件: {auth_config.database_mapping_file}")
    print(f"用户信息文件: {auth_config.users_file}")
    
    print(f"\n📝 文件状态:")
    print(f"   允许注册工号文件: {'✅ 存在' if auth_config.allowed_employees_file.exists() else '❌ 不存在'}")
    print(f"   数据库映射文件: {'✅ 存在' if auth_config.database_mapping_file.exists() else '❌ 不存在'}")
    print(f"   用户信息文件: {'✅ 存在' if auth_config.users_file.exists() else '❌ 不存在'}")

def show_usage_guide():
    """显示使用指南"""
    print("\n=== 🚀 登录功能使用指南 ===\n")
    
    print("📋 **管理员配置步骤:**")
    print("1. 编辑 allowed_employees.txt 添加允许注册的工号")
    print("2. 编辑 database_mapping.json 配置工号与数据库的映射关系")
    print("   - database_type: 数据库类型 (mysql/postgresql)")
    print("   - database_name: 数据库名称")
    print("   - description: 数据库描述")
    print("3. 在 .env 文件中配置数据库连接参数 (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)")
    print("4. 确保对应的数据库已经创建并可访问")
    print()
    
    print("👤 **用户使用步骤:**")
    print("1. 启动应用: python gradio_app.py")
    print("2. 在登录页面选择'注册'选项卡")
    print("3. 输入工号、姓名和密码（至少6位，包含大小写字母和符号）")
    print("4. 注册成功后，切换到'登录'选项卡")
    print("5. 使用工号和密码登录")
    print("6. 登录成功后，系统会自动连接到对应的数据库")
    print()
    
    print("🔐 **密码要求:**")
    print("- 长度至少6位")
    print("- 包含大写字母（A-Z）")
    print("- 包含小写字母（a-z）")
    print("- 包含符号（!@#$%^&*(),.?\":{}|<>）")
    print()
    
    print("🗃️ **数据库权限:**")
    print("- 每个工号对应一个专属数据库")
    print("- 登录后只能访问自己的数据库")
    print("- 不同用户之间数据完全隔离")
    print()
    
    print("💡 **管理提示:**")
    print("- 通过修改 allowed_employees.txt 控制注册权限")
    print("- 通过修改 database_mapping.json 配置数据库访问（只需配置类型和名称）")
    print("- 数据库连接密码安全存储在 .env 配置文件中")
    print("- 用户信息存储在 users.json 中（包含加密密码）")
    print("- 支持MySQL和PostgreSQL两种数据库类型")

def main():
    """主测试函数"""
    print("🔐 ChatBI 认证功能测试\n")
    
    try:
        # 显示配置文件状态
        show_config_files()
        
        # 运行各项测试
        test_password_validation()
        test_allowed_employees()
        test_database_mapping()
        test_user_registration()
        test_user_authentication()
        test_user_database_config()
        
        # 显示使用指南
        show_usage_guide()
        
        print("\n🎉 认证功能测试完成！")
        print("\n💡 下一步: 运行 `python gradio_app.py` 启动带登录功能的应用")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    # 验证配置
    if not Config.validate_config():
        print("❌ 配置验证失败，请检查 .env 文件")
        exit(1)
    
    main() 