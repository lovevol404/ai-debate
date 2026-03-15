# AI Debate Platform

AI 辩论平台 - 基于 LangChain 和 FastAPI 的智能辩论系统

## 功能特性

- **双 LLM 配置**: 支持配置两个不同的 LLM 作为正方和反方辩手
- **OpenAI API 兼容**: 支持任何兼容 OpenAI API 格式的服务 (OpenAI, Azure, vLLM, Ollama 等)
- **实时辩论**: WebSocket 实时推送每轮辩论内容
- **前端界面**: 响应式 Web 界面，支持辩论管理、LLM 配置、实时观看
- **SQLite 存储**: 本地数据存储，无需额外数据库

## 项目结构

```
ai-debate/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models.py            # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic 模式
│   ├── crud.py              # 数据库操作
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API 路由
│   └── debate/
│       ├── __init__.py
│       └── engine.py        # 辩论引擎 (LangChain)
├── frontend/
│   └── index.html           # 单页应用
├── requirements.txt
├── .env.example
└── debates.db               # SQLite 数据库
```

## 快速开始

### 1. 安装依赖

```bash
.venv/Scripts/pip install -r requirements.txt
```

### 2. 启动服务

```bash
.venv/Scripts/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问应用

- **API 文档**: http://127.0.0.1:8000/docs
- **前端界面**: http://127.0.0.1:8000/

## API 接口

### LLM 配置
- `GET /api/llm-configs` - 获取所有 LLM 配置
- `POST /api/llm-configs` - 创建 LLM 配置
- `PUT /api/llm-configs/{id}` - 更新 LLM 配置
- `DELETE /api/llm-configs/{id}` - 删除 LLM 配置

### 辩题管理
- `GET /api/topics` - 获取所有辩题
- `POST /api/topics` - 创建辩题
- `PUT /api/topics/{id}` - 更新辩题
- `DELETE /api/topics/{id}` - 删除辩题

### 辩论记录
- `GET /api/debates` - 获取辩论历史
- `GET /api/debates/{id}` - 获取辩论详情
- `POST /api/debates/start` - 开始辩论
- `DELETE /api/debates/{id}` - 删除辩论记录
- `POST /api/debates/{id}/abort` - 终止辩论
- `WebSocket /api/debates/{id}/stream` - 实时辩论流

## LLM 配置说明

支持任何兼容 OpenAI API 格式的模型:

| 服务商 | Base URL | 示例模型 |
|--------|----------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4, gpt-3.5-turbo |
| Azure OpenAI | https://your-resource.openai.azure.com/openai/deployments/{model} | gpt-4 |
| Ollama | http://localhost:11434/v1 | llama2, mistral |
| LM Studio | http://localhost:1234/v1 | 本地模型 |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| Moonshot | https://api.moonshot.cn/v1 | moonshot-v1-8k |

配置项包括:
- `base_url`: API 基础地址
- `api_key`: API 密钥
- `model_name`: 模型名称
- `temperature`: 温度参数 (0-2)
- `max_tokens`: 最大生成 tokens

## 辩论流程

辩论分为四个阶段（可自定义）:
1. **立论**: 双方开篇立论，阐述己方观点
2. **驳论**: 反驳对方观点，指出对方漏洞
3. **自由辩论**: 自由交锋，深入辩论
4. **总结**: 总结陈词，强调己方优势

### 自定义辩论轮次

在辩题管理中，可以编辑每个辩题的辩论轮次配置：
- 点击辩题卡片上的"编辑"按钮
- 在"辩论轮次配置"区域添加、删除或修改每个阶段的名称和轮数
- 总轮数会实时显示在下方
- 点击"恢复默认"可以快速重置为标准的四阶段配置

轮次配置以 JSON 格式存储，每个阶段包含：
- `name`: 阶段名称（如"立论"、"驳论"等）
- `rounds`: 该阶段的轮数
- `description`: 阶段描述

示例配置:
```json
[
  {"name": "立论", "rounds": 2, "description": "开篇立论"},
  {"name": "驳论", "rounds": 1, "description": "反驳对方"},
  {"name": "自由辩论", "rounds": 4, "description": "自由交锋"},
  {"name": "总结", "rounds": 1, "description": "总结陈词"}
]
```

## 技术栈

- **后端**: FastAPI, SQLAlchemy, LangChain
- **前端**: HTML, TailwindCSS, Alpine.js
- **数据库**: SQLite
- **实时通信**: WebSocket

## 注意事项

- 首次运行会自动创建 SQLite 数据库
- WebSocket 需要浏览器支持
- 建议使用 Python 3.10+
