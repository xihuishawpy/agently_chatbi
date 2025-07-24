# ChatBI - 智能数据查询系统

基于 Agently 框架的数据仓库自然语言查询系统，支持将自然语言转换为 SQL 查询并提供智能数据分析。

## 🚀 特性

- **自然语言查询**: 使用自然语言描述查询需求，自动生成 SQL
- **智能数据分析**: 基于 AI 的查询结果分析和洞察
- **智能可视化**: 自动识别查询类型，为聚合和时间序列数据生成合适的图表
- **数据库元数据管理**: 支持表和字段备注的实时编辑与自动刷新
- **双重前端**: 支持传统 Web 界面和现代 Gradio 界面
- **数据仓库支持**: 支持 PostgreSQL、MySQL 等主流数据库
- **REST API**: 完整的 RESTful API 接口
- **缓存优化**: 支持 Redis 缓存，提升查询性能
- **安全防护**: SQL 注入检测和安全验证

## 下一步计划
- [ ] 登录界面
- [ ] 查询缓存

## 🆕 最新改进

### 数据库元数据管理增强

- **实时自动刷新**: 更新表或字段备注后，界面自动显示最新数据，无需手动刷新
- **元数据质量评估**: 提供数据库元数据完整性评分和改进建议
- **一键缓存清除**: 支持手动清除缓存以解决异常情况

### 安全认证系统

- **工号权限控制**: 只有允许列表中的工号才能注册
- **强密码策略**: 密码至少6位，包含大小写字母和符号
- **安全数据库配置**: 数据库密码安全存储在.env文件中，配置文件不含敏感信息
- **多租户隔离**: 每个用户只能访问指定的数据库，数据完全隔离

### 用户体验优化

- **简化操作流程**: 从原来的3步操作（更新→清缓存→刷新）简化为1步操作（更新）
- **更直观的界面**: 重新设计了数据库管理界面，提供更清晰的信息展示
- **操作反馈增强**: 提供更详细的操作状态提示

## 📋 系统要求

- Python 3.8+
- PostgreSQL 或 MySQL 数据库
- Redis (可选，用于缓存)
- 通义千问 API 密钥

## 🛠️ 安装指南

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd agently_chatbi
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：
```bash
# AI 模型配置
DASHSCOPE_API_KEY=your_dashscope_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Agently 配置
AGENTLY_MODEL_CODE=qwen-coder-plus
AGENTLY_MODEL_QA=qwen-max
AGENTLY_EMBEDDING_MODEL=text-embedding-v3
AGENTLY_RERANK_MODEL=gte-rerank-v2

# 数据库配置
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=data_warehouse
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_URL=postgresql://your_db_user:your_db_password@localhost:5432/data_warehouse

# Flask 配置
FLASK_SECRET_KEY=your_secret_key_here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Redis 配置 (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 🚀 快速开始

### 启动传统 Web 服务
```bash
python main.py
```

访问 http://localhost:5000 开始使用传统 Web 界面。

### 启动 Gradio 前端 (推荐)
```bash
python start_gradio.py
# 或者直接运行
python gradio_app.py
```

访问 http://localhost:7860 开始使用现代化的 Gradio 界面，支持：
- 友好的用户界面
- 实时查询结果展示
- 智能数据可视化
- 数据库元数据管理
- 示例查询建议

### 数据库元数据管理
1. 进入 🗃️ 数据库管理 Tab
2. 选择要编辑的表
3. 修改表备注或字段备注
4. 点击更新按钮，系统会自动刷新显示最新数据

### 传统 Web 服务
```bash
python main.py
```

#### 查看数据库信息
```bash
python main.py --info
```

#### 执行查询
```bash
python main.py --query "显示销售额最高的10个产品"
```

#### 自定义端口启动
```bash
python main.py --port 8080
```

## 📚 API 接口

### 自然语言查询
```http
POST /api/query
Content-Type: application/json

{
    "query": "显示销售额最高的10个产品"
}
```

### 获取数据库结构
```http
GET /api/schema
```

### 元数据管理
```http
POST /api/metadata/table/comment
Content-Type: application/json

{
    "table_name": "products",
    "comment": "产品信息表"
}

POST /api/metadata/column/comment
Content-Type: application/json

{
    "table_name": "products",
    "column_name": "price",
    "comment": "产品价格"
}
```

## 🔐 安全配置

### 数据库安全配置

系统采用安全的数据库配置方式，数据库密码不在配置文件中明文存储：

**配置文件结构（database_mapping.json）**：
```json
{
  "工号": {
    "database_type": "mysql",
    "database_name": "数据库名称",
    "description": "数据库描述"
  }
}
```

**环境变量（.env）**：
```bash
# 数据库连接参数（安全存储）
DB_HOST=localhost
DB_PORT=3306
DB_USER=username
DB_PASSWORD=password
```

系统会根据 `database_type` 和 `database_name` 动态构建数据库连接URL，确保敏感信息安全。

## 💡 使用示例

### 数据库元数据管理
1. 打开浏览器访问 http://localhost:7860
2. 切换到 🗃️ 数据库管理 Tab
3. 从下拉列表中选择表
4. 编辑表备注或字段备注
5. 点击更新按钮
6. 观察界面自动刷新显示最新数据

### 元数据质量评估
1. 在数据库管理界面展开 📊 元数据质量报告
2. 查看:
   - 总体评分
   - 表备注覆盖率
   - 字段备注覆盖率
   - AI 优化建议

## 🏗️ 项目结构

```
agently_chatbi/
├── main.py                 # 主入口文件
├── config.py              # 配置文件
├── requirements.txt       # 依赖列表
├── README.md             # 项目说明
├── .env.example          # 环境变量模板
├── gradio_app.py         # Gradio 前端应用
├── start_gradio.py       # Gradio 启动脚本
├── database/             # 数据库模块
│   └── db_manager.py     # 数据库管理器
├── agents/               # AI Agent 模块
│   └── chatbi_agent.py   # ChatBI Agent (含可视化功能)
├── web/                  # 传统 Web 应用
│   └── app.py           # Flask 应用
├── templates/            # 前端模板
│   └── index.html       # 主页面
└── logs/                # 日志目录
```



## ⚙️ 配置说明

### 元数据缓存配置
- **自动刷新**: 默认启用，更新后立即刷新
- **缓存超时**: 默认1小时
- **强制刷新**: 可通过 `force_refresh=True` 参数强制刷新

## 🔒 安全考虑

1. **元数据编辑权限**: 仅限授权用户
2. **操作审计**: 记录所有元数据变更
3. **数据验证**: 确保备注内容安全

## 🐛 故障排除

### 元数据不更新
1. 检查数据库连接是否正常
2. 尝试手动清除缓存
3. 查看日志文件 `logs/chatbi.log`

### 元数据质量报告
```bash
# 生成元数据报告
python -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); print(db.get_metadata_completeness_report())"
```



## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

MIT License

## 📞 支持

如有问题，请：
1. 查看 FAQ 和故障排除部分
2. 查看日志文件
3. 提交 Issue 