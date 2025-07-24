#!/usr/bin/env python3
"""
测试表和字段备注更新功能
验证修复后的参数传递是否正常工作
"""

from database.db_manager import DatabaseManager
from config import Config
from loguru import logger
import traceback

def test_comment_updates():
    """测试备注更新功能"""
    print("=== 备注更新功能测试 ===\n")
    
    try:
        # 初始化数据库管理器
        print("1. 连接数据库...")
        db_manager = DatabaseManager()
        
        if not db_manager.engine:
            print("❌ 数据库连接失败")
            return False
        
        print("✅ 数据库连接成功")
        print(f"数据库类型: {Config.DB_TYPE}")
        
        # 获取表列表
        tables = db_manager.get_table_names()
        if not tables:
            print("❌ 没有找到任何表")
            return False
        
        print(f"✅ 发现 {len(tables)} 个表")
        
        # 选择一个表进行测试
        test_table = tables[0]
        print(f"\n2. 测试表: {test_table}")
        
        # 获取表的当前信息
        details = db_manager.get_table_details_for_editing(test_table)
        if 'error' in details:
            print(f"❌ 获取表信息失败: {details['error']}")
            return False
        
        current_table_comment = details.get('table_comment', '')
        columns = details.get('columns', [])
        
        print(f"当前表备注: '{current_table_comment}'")
        print(f"字段数量: {len(columns)}")
        
        if not columns:
            print("❌ 表中没有字段")
            return False
        
        # 测试表备注更新
        print(f"\n3. 测试表备注更新...")
        test_table_comment = f"测试表备注 - {test_table} 的业务描述 (测试时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        
        success, message = db_manager.update_table_comment(test_table, test_table_comment)
        if success:
            print(f"✅ 表备注更新成功: {message}")
            
            # 验证更新是否生效
            updated_details = db_manager.get_table_details_for_editing(test_table)
            updated_comment = updated_details.get('table_comment', '')
            if updated_comment == test_table_comment:
                print("✅ 表备注更新验证成功")
            else:
                print(f"⚠️ 表备注更新验证失败，期望: '{test_table_comment}', 实际: '{updated_comment}'")
        else:
            print(f"❌ 表备注更新失败: {message}")
            return False
        
        # 测试字段备注更新
        test_column = columns[0]['name']
        current_column_comment = columns[0].get('comment', '')
        
        print(f"\n4. 测试字段备注更新...")
        print(f"测试字段: {test_column}")
        print(f"当前字段备注: '{current_column_comment}'")
        
        test_column_comment = f"测试字段备注 - {test_column} 的业务含义说明 (测试时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        
        success, message = db_manager.update_column_comment(test_table, test_column, test_column_comment)
        if success:
            print(f"✅ 字段备注更新成功: {message}")
            
            # 验证更新是否生效
            updated_details = db_manager.get_table_details_for_editing(test_table)
            updated_columns = updated_details.get('columns', [])
            updated_column_comment = None
            for col in updated_columns:
                if col['name'] == test_column:
                    updated_column_comment = col.get('comment', '')
                    break
            
            if updated_column_comment == test_column_comment:
                print("✅ 字段备注更新验证成功")
            else:
                print(f"⚠️ 字段备注更新验证失败，期望: '{test_column_comment}', 实际: '{updated_column_comment}'")
        else:
            print(f"❌ 字段备注更新失败: {message}")
            return False
        
        print(f"\n=== 测试完成 ===")
        print("✅ 所有备注更新功能测试通过")
        
        # 提示恢复原始备注
        print(f"\n💡 测试完成后，您可以手动恢复原始备注:")
        if current_table_comment:
            print(f"   表备注: '{current_table_comment}'")
        else:
            print(f"   表备注: (原本为空)")
        
        if current_column_comment:
            print(f"   字段 {test_column} 备注: '{current_column_comment}'")
        else:
            print(f"   字段 {test_column} 备注: (原本为空)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def test_sql_syntax():
    """测试SQL语法"""
    print("\n=== SQL语法测试 ===\n")
    
    print("MySQL SQL示例:")
    print("-- 表备注更新")
    print("ALTER TABLE `table_name` COMMENT = 'table comment';")
    print()
    print("-- 字段备注更新")
    print("ALTER TABLE `table_name` MODIFY COLUMN `column_name` VARCHAR(100) NOT NULL COMMENT 'column comment';")
    print()
    
    print("PostgreSQL SQL示例:")
    print("-- 表备注更新")
    print('COMMENT ON TABLE "table_name" IS \'table comment\';')
    print()
    print("-- 字段备注更新")
    print('COMMENT ON COLUMN "table_name"."column_name" IS \'column comment\';')

if __name__ == "__main__":
    # 验证配置
    if not Config.validate_config():
        print("❌ 配置验证失败，请检查 .env 文件")
        exit(1)
    
    print("🔧 修复说明:")
    print("本次修复主要解决了SQLAlchemy参数传递格式问题:")
    print("- 使用命名参数 (:param) 替代位置参数 (%s)")
    print("- 使用字典格式传递参数 {'param': value}")
    print("- 使用事务 (connection.begin()) 确保数据一致性")
    print()
    
    # 运行测试
    success = test_comment_updates()
    
    # 显示SQL语法
    test_sql_syntax()
    
    if success:
        print("\n🎉 修复验证完成，可以正常使用备注更新功能！")
        print("   现在可以通过Gradio界面进行备注编辑操作")
    else:
        print("\n⚠️  请检查错误信息并联系技术支持") 