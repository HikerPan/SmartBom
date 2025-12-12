目标：构建基于 CrewAI + 双 RAG (历史经验+ERP库存) 的智能 BOM 生成系统。
适用场景：全云端 API (OpenAI / DeepSeek)，不依赖本地算力。
输入文件：

HVIL1.01.04.csv (原始 EDA 导出的 BOM)

存货2025-11-10.xlsx - _1.csv (ERP 存货数据库)

bom_template.xlsx (目标输出模版，如无则需创建)

阶段 1: 基础设施搭建 (Infrastructure)

Prompt 指令:

引用文件: @智能BOM生成系统设计方案.md (如果有)

你是高级 Python 架构师。请初始化名为 Smart_BOM_Cloud 的项目结构。

1. 目录结构创建：
请执行 shell 命令创建以下结构：

data/：存放数据文件。

data/history_boms/：存放历史项目 BOM（创建一个 .keep 文件以保留目录）。

src/：存放源代码 (__init__.py, config.py, utils.py, vector_store.py, tools.py, agents.py, main.py)。

chroma_db/：存放向量库数据。

2. 文件迁移操作：

将根目录下的 HVIL1.01.04.csv 移动并重命名为 data/raw_bom.csv。

将根目录下的 存货2025-11-10.xlsx 移动并重命名为 data/inventory.csv。

如果存在 bom_template.xlsx，移入 data/；如果不存在，请忽略。

3. 依赖管理：
创建 requirements.txt，内容必须包含：
pandas
openpyxl
python-dotenv
crewai
langchain
langchain-community
langchain-openai
langchain-chroma
chromadb
tiktoken
4. 环境变量模版：
创建 .env 文件，写入以下内容（请提醒用户后续填入真实 Key）：
OPENAI_API_KEY=sk-proj-xxxx
OPENAI_API_BASE=[https://api.openai.com/v1](https://api.openai.com/v1)  # DeepSeek 用户请填 [https://api.deepseek.com](https://api.deepseek.com)
OPENAI_MODEL_NAME=gpt-4o  # DeepSeek 用户请填 deepseek-chat
阶段 2: 配置加载与数据清洗 (Config & ETL)

Prompt 指令:

任务：实现配置与工具函数

1. 实现 src/config.py：

使用 dotenv 加载 .env 文件。

导出变量：API_KEY, API_BASE, MODEL_NAME。

增加防御性编程：如果 API_KEY 为空，抛出 ValueError 提示用户。

2. 实现 src/utils.py：

load_data(file_path): 使用 Pandas 读取 CSV/Excel。对于 CSV，尝试 utf-8 和 gbk 两种编码，防止乱码。

clean_footprint(str): 清洗封装。逻辑：如果字符串以 "R" 或 "C" 开头且后接数字（如 "R0603"），去除首字母返回 "0603"；否则原样返回。

clean_value(str): 清洗数值。逻辑：去除 "_1%" 或 "_10%" 等后缀，例如将 "1.02K_1%" 清洗为 "1.02K"。

阶段 3: 双知识库向量层 (Dual Vector Store)

Prompt 指令:

任务：实现基于 OpenAI Embeddings 的双知识库构建

请编写 src/vector_store.py：

1. 初始化 Embedding：

引入 from langchain_openai import OpenAIEmbeddings。

使用模型 text-embedding-3-small。

传入 config 中的 api_key 和 base_url。

2. 实现 init_knowledge_bases() 函数：

构建 Inventory 库：

读取 data/inventory.csv。

构造 Embedding 文本: "名称: {存货名称}, 规格: {规格型号}, 供应商: {主要供货单位名称}"。

元数据 (Metadata): {"code": 存货编码, "spec": 规格型号}。

存入 Chroma 的 inventory 集合。

构建 History 库：

扫描 data/history_boms/ 目录下的所有 CSV。

如果目录为空，打印“未发现历史数据，跳过历史库构建”。

如果有文件，读取并构造文本: "原始输入: {Comment} {Footprint} => 最终编码: {Matched_Code}"。

存入 Chroma 的 history 集合。

3. 实现 Getter 方法：

get_inventory_retriever(k=3)

get_history_retriever(k=1)

阶段 4: 智能体与工具 (Cloud Agents)

Prompt 指令:

任务：实现 CrewAI 智能体与搜索工具

1. 实现 src/tools.py：

InventorySearchTool: 在 inventory 集合搜索 Top 3，返回格式化的候选物料信息。

HistorySearchTool: 在 history 集合搜索 Top 1。

关键逻辑: 获取相似度 score。只有当 score > 0.95 (高度匹配) 时，才返回 FOUND: {code}；否则返回 NOT_FOUND。

2. 实现 src/agents.py：

引入 from langchain_openai import ChatOpenAI。

初始化 LLM: 使用 src/config.py 中的配置 (支持 GPT-4o 或 DeepSeek)。

定义 BOMMatcherAgent：

Role: BOM Normalization Expert

Goal: 为原始 BOM 行找到最准确的 ERP 存货编码。

System Prompt (Backstory):
"你拥有双重检索能力，请严格遵守以下决策流程：

优先查历史：首先调用 HistorySearchTool。如果返回 FOUND，直接输出该编码，停止思考。

次要查库存：如果历史未命中，调用 InventorySearchTool。对比原始描述与候选物料的阻值、容值、精度、封装（注意忽略 R/C 前缀）。

兜底策略：如果都不确定，或者没有合适的候选，输出 MANUAL_CHECK。"

阶段 5: 业务流串联 (Pipeline Integration)

Prompt 指令:

任务：编写主程序 src/main.py

请将所有模块串联，实现完整的 ETL 流程：

初始化：调用 vector_store.init_knowledge_bases() (启动时自动构建/更新向量库)。

读取：读取 data/raw_bom.csv。

处理循环：

遍历每一行数据。

调用 utils 中的清洗函数处理 Comment 和 Footprint。

构造查询 Query: "{Comment} {Footprint} {Description}"。

开发限制：为了快速测试且节省 Token，代码中请加入 if index > 5: break 限制只处理前 5 行。

创建并执行 CrewAI Task，获取 Agent 的返回结果（存货编码）。

结果写入：

如果 data/bom_template.xlsx 存在，加载它；否则创建一个新的 DataFrame。

将 [原始位号, 原始数量, 匹配到的存货编码] 写入对应列。

保存结果为 data/Final_BOM.xlsx。

注意：请在控制台打印每一行的处理进度和匹配结果（如 "Row 1: 10K R0603 -> 10023456"）。

调试建议 (Troubleshooting)

API 连接失败：

检查 .env 文件是否存在。

如果使用 DeepSeek，确认 OPENAI_API_BASE 结尾不要带 /chat/completions，通常是 https://api.deepseek.com 或 https://api.deepseek.com/v1。

ChromaDB 报错：

如果遇到 sqlite3 版本过低错误，提示用户安装 pysqlite3-binary 并替换 sys.modules['sqlite3']。

编码错误：

如果读取 CSV 报错 `UnicodeDecodeError