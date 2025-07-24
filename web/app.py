"""
Flask Web 应用
提供 ChatBI 的 REST API 接口和前端页面
"""
import os
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any
import traceback

from config import Config
from database.db_manager import DatabaseManager
from agents.chatbi_agent import ChatBIAgent
from loguru import logger

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

# 创建 Flask 应用，指定正确的模板和静态文件路径
app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['JSON_AS_ASCII'] = False  # 支持中文 JSON 返回

# 启用 CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 启用 WebSocket
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化 Redis 缓存
try:
    redis_client = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("Redis 连接成功")
except Exception as e:
    logger.warning(f"Redis 连接失败: {e}, 将使用内存缓存")
    redis_client = None

# 内存缓存作为备选
memory_cache = {}

# 全局对象
db_manager = None
chatbi_agent = None

def init_app():
    """初始化应用组件"""
    global db_manager, chatbi_agent
    
    try:
        # 初始化数据库管理器
        db_manager = DatabaseManager()
        if not db_manager.engine:
            logger.error("数据库连接失败，应用无法启动")
            return False
        
        # 初始化 ChatBI Agent
        chatbi_agent = ChatBIAgent(db_manager)
        
        logger.info("ChatBI 应用初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"应用初始化失败: {e}")
        return False

def get_cache(key: str) -> Any:
    """获取缓存数据"""
    try:
        if redis_client:
            data = redis_client.get(key)
            return json.loads(data) if data else None
        else:
            return memory_cache.get(key)
    except Exception as e:
        logger.error(f"缓存读取失败: {e}")
        return None

def set_cache(key: str, value: Any, expire: int = Config.CACHE_EXPIRY):
    """设置缓存数据"""
    try:
        if redis_client:
            redis_client.setex(key, expire, json.dumps(value, ensure_ascii=False))
        else:
            memory_cache[key] = value
        return True
    except Exception as e:
        logger.error(f"缓存设置失败: {e}")
        return False

def generate_cache_key(query: str, params: Dict = None) -> str:
    """生成缓存键"""
    content = f"{query}_{params or {}}"
    return f"chatbi_query_{hashlib.md5(content.encode()).hexdigest()}"

@app.route('/')
def index():
    """主页"""
    try:
        logger.info(f"模板目录: {app.template_folder}")
        logger.info(f"静态目录: {app.static_folder}")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"模板渲染失败: {e}")
        # 返回简单的 HTML 作为备选
        return """
        <html>
        <head><title>ChatBI - 启动错误</title></head>
        <body>
            <h1>ChatBI 系统</h1>
            <p>模板文件加载失败，但 API 接口仍然可用。</p>
            <p>请访问 <a href="/api/health">/api/health</a> 检查 API 状态。</p>
            <p>错误信息: {}</p>
        </body>
        </html>
        """.format(str(e))

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database_connected': db_manager is not None and db_manager.engine is not None,
        'agent_ready': chatbi_agent is not None
    })

@app.route('/api/schema')
def get_database_schema():
    """获取数据库结构"""
    try:
        cache_key = "chatbi_schema"
        cached_schema = get_cache(cache_key)
        
        if cached_schema:
            return jsonify({
                'success': True,
                'data': cached_schema,
                'cached': True
            })
        
        schema = db_manager.get_database_schema()
        set_cache(cache_key, schema, expire=3600)  # 缓存1小时
        
        return jsonify({
            'success': True,
            'data': schema,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"获取数据库结构失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tables')
def get_tables():
    """获取数据库表列表"""
    try:
        tables = db_manager.get_table_names()
        return jsonify({
            'success': True,
            'data': tables
        })
    except Exception as e:
        logger.error(f"获取表列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/table/<table_name>/info')
def get_table_info(table_name: str):
    """获取特定表的详细信息"""
    try:
        cache_key = f"chatbi_table_info_{table_name}"
        cached_info = get_cache(cache_key)
        
        if cached_info:
            return jsonify({
                'success': True,
                'data': cached_info,
                'cached': True
            })
        
        # 获取表结构
        schema = db_manager.get_table_schema(table_name)
        
        # 获取示例数据
        sample_data = db_manager.get_sample_data(table_name, limit=5)
        
        # 获取统计信息
        statistics = db_manager.get_table_statistics(table_name)
        
        table_info = {
            'schema': schema,
            'sample_data': sample_data,
            'statistics': statistics
        }
        
        set_cache(cache_key, table_info, expire=1800)  # 缓存30分钟
        
        return jsonify({
            'success': True,
            'data': table_info,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"获取表信息失败 {table_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/query', methods=['POST'])
def execute_natural_language_query():
    """执行自然语言查询"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': '缺少查询参数'
            }), 400
        
        user_query = data['query'].strip()
        if not user_query:
            return jsonify({
                'success': False,
                'error': '查询不能为空'
            }), 400
        
        if len(user_query) > Config.MAX_QUERY_LENGTH:
            return jsonify({
                'success': False,
                'error': f'查询长度超过限制 ({Config.MAX_QUERY_LENGTH} 字符)'
            }), 400
        
        # 检查缓存
        cache_key = generate_cache_key(user_query)
        cached_result = get_cache(cache_key)
        
        if cached_result:
            cached_result['cached'] = True
            return jsonify(cached_result)
        
        # 执行查询
        result = chatbi_agent.execute_query_with_analysis(user_query)
        
        # 添加时间戳
        result['timestamp'] = datetime.now().isoformat()
        result['cached'] = False
        
        # 缓存结果
        if result['success']:
            set_cache(cache_key, result, expire=Config.CACHE_EXPIRY)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"查询执行失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/sql', methods=['POST'])
def execute_sql_query():
    """直接执行 SQL 查询"""
    try:
        data = request.get_json()
        if not data or 'sql' not in data:
            return jsonify({
                'success': False,
                'error': '缺少 SQL 参数'
            }), 400
        
        sql = data['sql'].strip()
        if not sql:
            return jsonify({
                'success': False,
                'error': 'SQL 不能为空'
            }), 400
        
        # 验证 SQL
        is_valid, validation_msg = db_manager.validate_sql(sql)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': validation_msg
            }), 400
        
        # 执行 SQL
        success, result = db_manager.execute_query(sql)
        
        return jsonify({
            'success': success,
            'data': result if success else None,
            'error': result if not success else None,
            'sql': sql,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"SQL 执行失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/suggestions')
def get_query_suggestions():
    """获取查询建议"""
    try:
        table_name = request.args.get('table')
        suggestions = chatbi_agent.get_suggested_queries(table_name)
        
        return jsonify({
            'success': True,
            'data': suggestions
        })
        
    except Exception as e:
        logger.error(f"获取查询建议失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/history')
def get_query_history():
    """获取查询历史（示例接口）"""
    try:
        # 这里可以实现查询历史的存储和检索
        # 目前返回空列表
        return jsonify({
            'success': True,
            'data': []
        })
    except Exception as e:
        logger.error(f"获取查询历史失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@socketio.on('connect')
def handle_connect():
    """WebSocket 连接处理"""
    logger.info("WebSocket 客户端连接")
    emit('connected', {'message': 'ChatBI 连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 断开处理"""
    logger.info("WebSocket 客户端断开")

@socketio.on('realtime_query')
def handle_realtime_query(data):
    """实时查询处理"""
    try:
        user_query = data.get('query', '').strip()
        if not user_query:
            emit('query_error', {'error': '查询不能为空'})
            return
        
        # 发送处理状态
        emit('query_status', {'status': 'processing', 'message': '正在分析查询...'})
        
        # 执行查询
        result = chatbi_agent.execute_query_with_analysis(user_query)
        
        # 发送结果
        if result['success']:
            emit('query_result', result)
        else:
            emit('query_error', {'error': result.get('error', '未知错误')})
            
    except Exception as e:
        logger.error(f"实时查询失败: {e}")
        emit('query_error', {'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    logger.error(f"服务器内部错误: {error}")
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

def create_app():
    """创建并配置 Flask 应用"""
    if not Config.validate_config():
        logger.error("配置验证失败")
        return None
    
    if not init_app():
        logger.error("应用初始化失败")
        return None
    
    return app

if __name__ == '__main__':
    app = create_app()
    if app:
        logger.info(f"ChatBI 应用启动中... http://{Config.HOST}:{Config.PORT}")
        socketio.run(
            app,
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    else:
        logger.error("应用启动失败") 