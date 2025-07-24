"""
ChatBI 应用主入口文件
基于 Agently 框架的数据仓库自然语言查询系统
"""
import sys
import os
import argparse
from loguru import logger

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from web.app import create_app, socketio

def setup_logging():
    """配置日志系统"""
    # 移除默认日志处理器
    logger.remove()
    
    # 添加控制台日志输出
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 添加文件日志输出
    logger.add(
        "logs/chatbi.log",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    logger.info("日志系统初始化完成")

def create_log_directory():
    """创建日志目录"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        logger.info(f"创建日志目录: {log_dir}")

def check_dependencies():
    """检查关键依赖是否安装"""
    try:
        import agently
        import flask
        import sqlalchemy
        import pandas
        import redis
        logger.info("关键依赖检查通过")
        return True
    except ImportError as e:
        logger.error(f"缺少关键依赖: {e}")
        logger.error("请运行: pip install -r requirements.txt")
        return False

def print_banner():
    """打印应用启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                          ChatBI                              ║
    ║                基于 Agently 框架的智能数据查询系统              ║
    ║                                                              ║
    ║  特性:                                                        ║
    ║  • 自然语言转 SQL 查询                                        ║
    ║  • 智能数据分析                                               ║
    ║  • 数据仓库集成                                               ║
    ║  • 实时查询结果                                               ║
    ║  • Web 界面和 API                                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def validate_environment():
    """验证环境配置"""
    logger.info("验证环境配置...")
    
    # 检查配置文件
    if not Config.validate_config():
        logger.error("配置验证失败，请检查环境变量设置")
        logger.info("请创建 .env 文件并配置以下变量:")
        logger.info("- DASHSCOPE_API_KEY: 通义千问 API 密钥")
        logger.info("- DB_URL: 数据库连接字符串")
        return False
    
    # 检查数据库连接
    try:
        from database.db_manager import DatabaseManager
        db_manager = DatabaseManager()
        if not db_manager.engine:
            logger.error("数据库连接失败，请检查数据库配置")
            return False
        db_manager.close()
        logger.info("数据库连接测试通过")
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False
    
    logger.info("环境配置验证通过")
    return True

def run_web_server():
    """启动 Web 服务器"""
    logger.info("启动 ChatBI Web 服务器...")
    
    app = create_app()
    if not app:
        logger.error("应用创建失败")
        return False
    
    logger.info(f"ChatBI 服务启动成功!")
    logger.info(f"Web 界面: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"API 文档: http://{Config.HOST}:{Config.PORT}/api/health")
    logger.info("按 Ctrl+C 停止服务")
    
    try:
        socketio.run(
            app,
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            use_reloader=False  # 避免在生产环境中使用重载器
        )
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭应用...")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        return False
    
    return True

def run_cli_query(query: str):
    """运行命令行查询"""
    logger.info(f"执行命令行查询: {query}")
    
    try:
        from database.db_manager import DatabaseManager
        from agents.chatbi_agent import ChatBIAgent
        
        # 初始化组件
        db_manager = DatabaseManager()
        if not db_manager.engine:
            logger.error("数据库连接失败")
            return False
        
        chatbi_agent = ChatBIAgent(db_manager)
        
        # 执行查询
        result = chatbi_agent.execute_query_with_analysis(query)
        
        # 输出结果
        if result['success']:
            print("\n" + "="*60)
            print("查询结果:")
            print("="*60)
            print(f"用户查询: {result['user_query']}")
            print(f"生成的SQL: {result['sql_info']['sql']}")
            print(f"查询说明: {result['sql_info']['explanation']}")
            print(f"结果数量: {result['query_results']['row_count']} 条记录")
            
            # 显示前几行数据
            data = result['query_results']['data']
            if data:
                print("\n前 5 行数据:")
                print("-" * 40)
                for i, row in enumerate(data[:5], 1):
                    print(f"{i}. {row}")
            
            # 显示分析结果
            if result.get('analysis'):
                print(f"\n数据分析:")
                print("-" * 40)
                print(result['analysis']['summary'])
                if result['analysis']['detailed_analysis']:
                    print(f"\n详细分析:\n{result['analysis']['detailed_analysis']}")
            
        else:
            print(f"\n查询失败: {result.get('error', '未知错误')}")
            
        # 清理资源
        db_manager.close()
        return result['success']
        
    except Exception as e:
        logger.error(f"命令行查询失败: {e}")
        return False

def show_database_info():
    """显示数据库信息"""
    try:
        from database.db_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        if not db_manager.engine:
            logger.error("数据库连接失败")
            return False
        
        # 获取数据库结构
        schema = db_manager.get_database_schema()
        
        print("\n" + "="*60)
        print("数据库结构信息:")
        print("="*60)
        print(f"数据库名称: {schema['database_name']}")
        print(f"表数量: {len(schema['tables'])}")
        
        print(f"\n表列表:")
        print("-" * 40)
        for i, (table_name, table_info) in enumerate(schema['tables'].items(), 1):
            column_count = len(table_info['columns'])
            print(f"{i}. {table_name} ({column_count} 个字段)")
            
            # 显示示例数据
            sample_data = db_manager.get_sample_data(table_name, limit=1)
            if sample_data.get('sample_data'):
                print(f"   示例记录: {len(sample_data['sample_data'])} 条")
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        return False

def main():
    """主函数"""
    # 设置命令行参数
    parser = argparse.ArgumentParser(
        description="ChatBI - 基于 Agently 框架的智能数据查询系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                              # 启动 Web 服务器
  python main.py --query "显示销售前10的产品"    # 命令行查询
  python main.py --info                       # 显示数据库信息
  python main.py --check                      # 检查环境配置
        """
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='执行自然语言查询 (命令行模式)'
    )
    
    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='显示数据库结构信息'
    )
    
    parser.add_argument(
        '--check', '-c',
        action='store_true',
        help='检查环境配置和依赖'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=Config.HOST,
        help=f'Web 服务器主机地址 (默认: {Config.HOST})'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=Config.PORT,
        help=f'Web 服务器端口 (默认: {Config.PORT})'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    args = parser.parse_args()
    
    # 创建日志目录
    create_log_directory()
    
    # 设置日志
    setup_logging()
    
    # 打印启动横幅
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 更新配置 (如果从命令行指定)
    if args.host != Config.HOST:
        Config.HOST = args.host
    if args.port != Config.PORT:
        Config.PORT = args.port
    if args.debug:
        Config.DEBUG = True
    
    # 处理不同的运行模式
    try:
        if args.check:
            # 检查环境配置
            logger.info("执行环境检查...")
            if validate_environment():
                print("✅ 环境配置检查通过")
                sys.exit(0)
            else:
                print("❌ 环境配置检查失败")
                sys.exit(1)
        
        elif args.info:
            # 显示数据库信息
            if not validate_environment():
                sys.exit(1)
            if show_database_info():
                sys.exit(0)
            else:
                sys.exit(1)
        
        elif args.query:
            # 命令行查询模式
            if not validate_environment():
                sys.exit(1)
            if run_cli_query(args.query):
                sys.exit(0)
            else:
                sys.exit(1)
        
        else:
            # 默认启动 Web 服务器
            if not validate_environment():
                sys.exit(1)
            if run_web_server():
                sys.exit(0)
            else:
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()