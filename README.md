# Smart BOM System

Smart BOM System 是一个基于 CrewAI 和 RAG (Retrieval-Augmented Generation) 技术的智能 BOM (Bill of Materials) 生成与匹配系统。它旨在通过利用历史 BOM 数据和现有库存数据，自动化并优化 BOM 的创建过程。

## 功能特点

- **双重 RAG 检索**：
  - **库存检索 (Inventory RAG)**：优先匹配现有库存中的物料，确保库存利用率。
  - **历史检索 (History RAG)**：从历史 BOM 中学习和检索相似物料，提供参考。
- **智能匹配代理 (Agents)**：利用 CrewAI 编排智能代理，根据物料描述、规格等信息自动寻找最佳匹配。
- **结构化输出**：生成标准化的 Excel BOM 文件，包含匹配结果、来源（库存/历史）及置信度。
- **向量数据库**：使用 ChromaDB 存储和检索物料数据的向量表示，支持语义搜索。

## 项目结构

```
SmartBom/
├── src/
│   ├── agents.py       # CrewAI 代理定义 (BOMMatchingAgent)
│   ├── config.py       # 配置加载 (API Keys, 路径等)
│   ├── main.py         # 主程序入口
│   ├── tools.py        # 自定义工具 (InventorySearchTool, HistorySearchTool)
│   └── vector_store.py # 向量数据库管理 (BOMVectorStore)
├── data/               # 数据目录 (输入/输出 Excel 文件)
├── History_BOM/        # 历史 BOM 文件目录
├── chroma_db/          # 向量数据库持久化目录
├── requirements.txt    # 项目依赖
└── .env                # 环境变量配置
```

## 安装指南

1.  **克隆仓库**：

    ```bash
    git clone <repository-url>
    cd SmartBom
    ```

2.  **创建虚拟环境 (可选但推荐)**：

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    # .venv\Scripts\activate   # Windows
    ```

3.  **安装依赖**：

    ```bash
    pip install -r requirements.txt
    ```

4.  **配置环境变量**：
    复制 `.env.example` (如果有) 或直接创建 `.env` 文件，并填入必要的 API Key：
    ```ini
    OPENAI_API_KEY=sk-...
    OPENAI_API_BASE=https://api.openai.com/v1
    OPENAI_MODEL_NAME=gpt-4o
    # 其他相关配置
    ```

## 使用说明

1.  **准备数据**：

    - 将待处理的 BOM 文件放入 `data/` 目录（例如 `Raw_BOM.xlsx`）。
    - 确保 `History_BOM/` 目录下有历史 BOM 文件用于构建知识库。
    - 确保有库存数据文件（如 `Inventory.xlsx`）用于构建库存索引。

2.  **运行程序**：

    ```bash
    python src/main.py
    ```

    程序将自动初始化向量数据库（如果不存在），加载数据，并开始处理 BOM 匹配任务。

3.  **查看结果**：
    处理完成后，生成的最终 BOM 文件将保存在 `data/` 目录下（例如 `Final_BOM.xlsx`）。

## 开发与调试

- `debug_api.py`: 用于测试 API 连接和基本功能的脚本。
- 日志文件 (`*.log`) 会记录运行过程中的详细信息，便于排查问题。

## 贡献

欢迎提交 Issue 和 Pull Request！
