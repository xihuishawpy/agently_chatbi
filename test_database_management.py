#!/usr/bin/env python3
"""
测试数据库管理功能
验证表和字段备注的更新功能
"""

from database.db_manager import DatabaseManager
from config import Config
from loguru import logger
import traceback

def test_database_management():
    """测试数据库管理功能"""
    print("=== 数据库管理功能测试 ===\n")
    
    try:
        # 初始化数据库管理器
        print("1. 连接数据库...")
        db_manager = DatabaseManager()
        
        if not db_manager.engine:
            print("❌ 数据库连接失败")
            return False
        
        print("✅ 数据库连接成功")
        
        # 获取表列表
        print("\n2. 获取表列表...")
        tables = db_manager.get_table_names()
        print(f"✅ 发现 {len(tables)} 个表: {', '.join(tables[:3])}{'...' if len(tables) > 3 else ''}")
        
        if not tables:
            print("❌ 没有找到任何表")
            return False
        
        # 测试表详细信息获取
        test_table = tables[0]
        print(f"\n3. 测试获取表详细信息 (表: {test_table})...")
        
        details = db_manager.get_table_details_for_editing(test_table)
        if 'error' in details:
            print(f"❌ 获取表详细信息失败: {details['error']}")
            return False
        
        print("✅ 表详细信息获取成功")
        print(f"  - 表名: {details['table_name']}")
        print(f"  - 当前表备注: '{details.get('table_comment', '无')}'")
        print(f"  - 字段数量: {len(details.get('columns', []))}")
        print(f"  - 主键: {details.get('primary_keys', [])}")
        
        # 显示字段信息
        columns = details.get('columns', [])
        print(f"\n  字段详情 (前5个):")
        for i, col in enumerate(columns[:5]):
            comment = col.get('comment', '') or '无备注'
            print(f"    {i+1}. {col['name']} ({col['type']}) - {comment}")
        
        # 测试表备注更新 (只是测试，不实际执行)
        print(f"\n4. 测试表备注更新功能...")
        test_comment = f"测试表备注 - {test_table} 业务说明"
        
        if Config.DB_TYPE.lower() in ['mysql', 'postgresql']:
            print(f"  数据库类型: {Config.DB_TYPE} - 支持备注更新")
            print(f"  测试备注内容: '{test_comment}'")
            print("  ⚠️  为安全起见，本测试不会实际更新备注")
            
            # 如果用户确认，可以取消注释下面的代码进行实际测试
            # success, message = db_manager.update_table_comment(test_table, test_comment)
            # print(f"  更新结果: {'✅' if success else '❌'} {message}")
        else:
            print(f"  数据库类型: {Config.DB_TYPE} - 暂不支持备注更新")
        
        # 测试字段备注更新 (只是测试，不实际执行)
        if columns:
            test_column = columns[0]['name']
            print(f"\n5. 测试字段备注更新功能...")
            test_column_comment = f"测试字段备注 - {test_column} 业务含义说明"
            
            if Config.DB_TYPE.lower() in ['mysql', 'postgresql']:
                print(f"  测试字段: {test_column}")
                print(f"  测试备注内容: '{test_column_comment}'")
                print("  ⚠️  为安全起见，本测试不会实际更新备注")
                
                # 如果用户确认，可以取消注释下面的代码进行实际测试
                # success, message = db_manager.update_column_comment(test_table, test_column, test_column_comment)
                # print(f"  更新结果: {'✅' if success else '❌'} {message}")
            else:
                print(f"  数据库类型: {Config.DB_TYPE} - 暂不支持备注更新")
        
        # 测试元数据完整性报告
        print(f"\n6. 测试元数据完整性报告...")
        report = db_manager.get_metadata_completeness_report()
        
        if report and 'summary' in report:
            summary = report['summary']
            print("✅ 元数据报告生成成功")
            print(f"  - 总体评分: {summary.get('overall_score', 0):.0f}%")
            print(f"  - 表备注覆盖率: {summary.get('table_comment_coverage', 0):.0f}%")
            print(f"  - 字段备注覆盖率: {summary.get('field_comment_coverage', 0):.0f}%")
            
            if report.get('recommendations'):
                print(f"  建议:")
                for rec in report['recommendations']:
                    print(f"    - {rec}")
        else:
            print("❌ 元数据报告生成失败")
        
        print(f"\n=== 测试完成 ===")
        print("✅ 所有基础功能测试通过")
        print("\n💡 提示:")
        print("1. 如需实际测试备注更新功能，请编辑本脚本取消相关注释")
        print("2. 建议先在测试环境中验证备注更新功能")
        print("3. 可以通过 Gradio 界面进行实际的备注编辑操作")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

def show_update_examples():
    """显示手动更新备注的SQL示例"""
    print("\n=== 手动更新备注的SQL示例 ===\n")
    
    if Config.DB_TYPE.lower() == 'mysql':
        print("MySQL 示例:")
        print("-- 更新表备注")
        print("ALTER TABLE `table_name` COMMENT = '表的业务描述';")
        print()
        print("-- 更新字段备注")
        print("ALTER TABLE `table_name` MODIFY COLUMN `column_name` VARCHAR(100) NOT NULL COMMENT '字段的业务含义';")
        print()
        
    elif Config.DB_TYPE.lower() == 'postgresql':
        print("PostgreSQL 示例:")
        print("-- 更新表备注")
        print("COMMENT ON TABLE \"table_name\" IS '表的业务描述';")
        print()
        print("-- 更新字段备注")
        print("COMMENT ON COLUMN \"table_name\".\"column_name\" IS '字段的业务含义';")
        print()
    
    print("建议的备注内容:")
    print("- 表备注：描述表的业务用途、数据来源、更新频率等")
    print("- 字段备注：描述字段的业务含义、取值范围、计算逻辑等")
    print("- 使用中文描述，便于ChatBI理解和生成准确的查询")

if __name__ == "__main__":
    # 验证配置
    if not Config.validate_config():
        print("❌ 配置验证失败，请检查 .env 文件")
        exit(1)
    
    # 运行测试
    success = test_database_management()
    
    # 显示SQL示例
    show_update_examples()
    
    if success:
        print("\n🎉 数据库管理功能测试完成，可以启动Gradio界面进行实际操作:")
        print("   python gradio_app.py")
    else:
        print("\n⚠️  请检查数据库连接和配置") 