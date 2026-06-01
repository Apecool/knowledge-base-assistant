# 知识库助手 (Knowledge Base Assistant)

基于 FastAPI + Vue 3 的 RAG 知识管理应用，支持多格式文档上传、语义搜索、多轮对话和流式 SSE 输出。

## 项目结构

```
knowledge-base-assistant/
├── backend/                       # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── knowledge.py       # 知识库 CRUD + 文件上传解析
│   │   │   ├── search.py          # 全文搜索 + 语义搜索 (RAG)
│   │   │   ├── chat.py            # 多轮对话 + SSE 流式输出
│   │   │   └── auth.py            # JWT 注册/登录
│   │   ├── models/                # SQLAlchemy 数据模型
│   │   ├── schemas/               # Pydantic 请求/响应模式
│   │   ├── services/
│   │   │   ├── langchain_rag.py   # RAG 编排 (检索 + 重排序 + 缓存)
│   │   │   ├── embedding_service.py # TF-IDF 嵌入 (零下载, 离线)
│   │   │   ├── vector_store.py    # ChromaDB 向量存储
│   │   │   ├── document_parser.py # 文档解析 (标题/表格感知分块)
│   │   │   ├── file_parser.py     # 文件解析 (.txt/.md/.pdf/.docx)
│   │   │   ├── chat_memory.py     # 多轮对话会话管理
│   │   │   ├── semantic_cache.py  # 语义缓存
│   │   │   └── reranker.py        # Cross-encoder 重排序
│   │   └── utils/logger.py        # 结构化日志 + 请求链路追踪
│   ├── tests/                     # pytest 测试 (34+ 用例)
│   └── requirements.txt
├── frontend/                      # Vue 3 + Vite + TailwindCSS
│   └── src/
│       ├── api/                   # Axios API 封装 (含 SSE 解析)
│       ├── components/            # SFC 组件
│       ├── pages/                 # 5 个页面 (含 Chat 页)
│       ├── stores/                # Pinia 状态管理
│       └── types/                 # TypeScript 类型定义
└── docker-compose.yml
```

## 快速开始

### 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

## RAG 语义搜索架构

```
用户提问 → 语义缓存查询 (阈值 >0.95 直接返回)
                ↓ miss
      TF-IDF 本地嵌入 (128维, 零下载)
                ↓
      ChromaDB 余弦相似度检索 (Top-20)
                ↓
      Cross-encoder 重排序 (Top-5)
                ↓
      ChatSession 多轮历史拼接
                ↓
      LLM 生成 (DeepSeek/OpenAI) 或 SSE 流式输出
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/knowledge/` | 分页查询知识列表 |
| POST | `/api/v1/knowledge/` | 创建知识条目 |
| POST | `/api/v1/knowledge/parse-file` | **上传解析文件 (不保存)** |
| POST | `/api/v1/knowledge/upload` | 上传文件并直接保存 |
| GET | `/api/v1/knowledge/{id}` | 获取知识详情 |
| PUT | `/api/v1/knowledge/{id}` | 更新知识条目 |
| DELETE | `/api/v1/knowledge/{id}` | 删除知识条目 |
| GET | `/api/v1/search/?q=xxx` | 全文搜索 (SQL LIKE) |
| GET | `/api/v1/search/semantic?q=xxx` | **语义搜索 (RAG)** |
| POST | `/api/v1/search/reindex` | 批量重新索引 |
| POST | `/api/v1/chat/` | 非流式多轮对话 |
| POST | `/api/v1/chat/stream` | **SSE 流式对话** |
| GET | `/api/v1/chat/sessions` | 会话列表 |
| GET | `/api/v1/chat/cache/stats` | 语义缓存统计 |

## 配置 LLM (DeepSeek / OpenAI)

编辑 `backend/.env`：

```ini
# 使用 DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-你的key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 或使用 OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-你的key
```

不配置 API Key 时，对话功能会以结构化方式展示知识库检索结果，但不会生成智能回答。

## 测试

```bash
cd backend
source venv/bin/activate
pytest -v
```

## 技术栈

- **后端**: FastAPI, SQLAlchemy, Pydantic, LangChain
- **向量**: ChromaDB + TF-IDF (scikit-learn, 离线)
- **前端**: Vue 3, Vite, Pinia, Axios, TailwindCSS v4
- **LLM**: DeepSeek / OpenAI (可选, 带 SSE 流式)
- **测试**: pytest, httpx (30+ 用例)