# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 PySide6 的桌面应用：
- AI 智能助手（多模型对话 + 工具调用）
- 群聊模式（多 AI 模型讨论）
- Excel 员工数据导入生成组织架构 PPT

## 常用命令

```bash
# 安装依赖
uv sync

# 安装开发依赖（测试工具）
uv sync --all-extras

# 运行应用
uv run python -m app.main

# 运行测试
uv run pytest

# 运行指定测试文件
uv run pytest tests/test_core/test_security_context.py

# 运行指定测试方法
uv run pytest tests/test_core/test_security_context.py::TestSecurityContext::test_is_safe_path_inside

# 带覆盖率报告
uv run pytest --cov=app --cov=core --cov=data --cov-report=html

# 只运行失败的测试
uv run pytest --lf
```

## 架构

```
app/                    # 应用层
├── ui/                 # 嵌入的 PySide6-Fluent-Widgets 源码（从 qfluentwidgets 导入改为 app.ui）
├── components/         # 业务组件（ChatMessageWidget、FileSelectorWidget 等）
├── view/               # 页面视图（MainWindow、AIChatInterface 等）
├── common/             # 公共模块（logger、storage_config）
└── main.py             # 应用入口、单实例控制

core/                   # 业务层
├── model_manager.py    # AI 模型管理（LangChain 封装）
├── group_chat_manager.py  # 群聊管理
├── excel_processor.py  # Excel 数据处理
├── ppt_generator.py    # PPT 生成
└── tools/              # AI 工具（文件操作、目录操作）

data/                   # 数据层
├── database.py         # 双数据库架构：内存库（临时数据）+ 文件库（持久配置）
├── models/             # 数据模型（Department、Employee、AIModelConfig、ChatSession）
└── repositories/       # 数据仓库

tests/                  # 测试
├── conftest.py         # 全局 fixtures
├── helpers.py          # 测试辅助工具（DataHelper）
└── mocks/              # Mock 对象（MockChatModel）
```

## 关键设计

### 双数据库架构

- **内存数据库** (`:memory:`)：员工组织数据，每次启动清空
- **文件数据库**：用户配置、模型配置、聊天记录，持久化存储

### 嵌入式 UI 框架

`app/ui/` 目录包含精简后的 PySide6-Fluent-Widgets 源码，导入路径已从 `qfluentwidgets` 改为 `app.ui`。

依赖变更：
- 已移除 `PySide6-Fluent-Widgets`
- 保留 `PySideSix-Frameless-Window` 和 `darkdetect`

### AI 模型配置

支持多提供商：OpenAI、Anthropic、DeepSeek、Ollama、智谱 AI 等。

环境变量自动配置：
```
ANTHROPIC_AUTH_TOKEN=your_api_key
ANTHROPIC_BASE_URL=https://api.lkeap.cloud.tencent.com/coding/anthropic
ANTHROPIC_MODEL=glm-5
```

或通过「AI 设置」页面手动添加。

### 数据存储

默认位置：`C:/ProgramData/xo1997-pyside-gallery/db`

可在「AI 设置」中更改，支持数据迁移。

---

## 测试规范

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 测试文件 | `test_<模块名>.py` | `test_security_context.py` |
| 测试类 | `Test<类名>` | `TestSecurityContext` |
| 测试方法 | `test_<功能描述>` | `test_is_safe_path_inside` |

### Fixture 使用

```python
# 临时工作目录
def test_file_operation(self, temp_work_dir):
    file_path = temp_work_dir / "test.txt"

# 示例 Excel 文件
def test_excel_import(self, sample_excel_file):
    processor = ExcelProcessor()

# Mock LangChain 模型
def test_chat(self, mock_chat_model):
    manager = ModelManager()
    manager._current_model = mock_chat_model
```

### 测试辅助工具

```python
from tests.helpers import DataHelper

dept = DataHelper.create_department(name="技术部", level=0)
emp = DataHelper.create_employee(name="张三", department="技术部")
config = DataHelper.create_model_config(name="测试模型")
```

### 覆盖率要求

| 层级 | 目标覆盖率 |
|------|------------|
| 数据层 | ≥ 90% |
| 核心层 | ≥ 80% |
| 组件层 | ≥ 85% |
| 视图层 | ≥ 70% |
