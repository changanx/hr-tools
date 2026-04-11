# 日志系统改进计划

## 目标

1. **核心层/数据层补充日志** - 在关键业务流程添加日志埋点
2. **结构化日志** - 支持 JSON 格式输出
3. **分级日志控制** - 通过 UI 界面配置日志级别
4. **日志轮转** - 自动清理 7 天前的日志

---

## 架构设计

### 日志模块结构

```
app/common/
├── logger.py          # 日志核心模块（重构）
├── log_config.py      # 日志配置管理（新增）
└── json_formatter.py  # JSON 格式化器（新增）
```

### 日志级别

| 级别 | 用途 |
|------|------|
| DEBUG | 详细调试信息（开发环境） |
| INFO | 关键流程节点（默认） |
| WARNING | 异常但可恢复的情况 |
| ERROR | 需要关注的错误 |
| CRITICAL | 严重错误，影响核心功能 |

### 日志埋点位置

#### 核心层 (core/)

| 模块 | 方法 | 级别 | 事件 |
|------|------|------|------|
| excel_processor.py | import_excel | INFO | 导入开始/结束、部门/员工数量 |
| excel_processor.py | import_excel | ERROR | 导入失败 |
| ppt_generator.py | generate | INFO | 生成开始/结束、节点数量 |
| ppt_generator.py | generate | ERROR | 生成失败 |
| model_manager.py | create_chat_model | INFO | 模型创建 |
| model_manager.py | set_current_model | INFO | 切换模型 |
| model_manager.py | chat/chat_with_tools | DEBUG | 对话流程 |
| model_manager.py | _execute_tool | INFO | 工具调用 |
| tools/base.py | validate_path | WARNING | 路径安全验证失败 |

#### 数据层 (data/)

| 模块 | 方法 | 级别 | 事件 |
|------|------|------|------|
| database.py | _init_schema | DEBUG | 数据库初始化 |
| database.py | clear | INFO | 数据清空 |
| database.py | transaction | ERROR | 事务失败 |

---

## 实现步骤

### Step 1: 重构日志核心模块

**目标**: 支持多格式输出、日志轮转、配置热更新

**修改文件**: `app/common/logger.py`

**关键改动**:
1. 添加 `JsonFormatter` 类支持 JSON 格式
2. 使用 `TimedRotatingFileHandler` 实现日志轮转
3. 添加 `set_level()` 方法支持动态调整级别
4. 添加结构化日志方法 `log_with_context()`

### Step 2: 创建日志配置管理模块

**目标**: 持久化日志配置，支持 UI 调整

**新增文件**: `app/common/log_config.py`

**功能**:
1. 日志配置模型（级别、格式、保留天数）
2. 配置持久化（JSON 文件存储在 `~/.hr-tools/config/`）
3. 配置变更通知信号

### Step 3: 在核心层添加日志

**修改文件**:
- `core/excel_processor.py`
- `core/ppt_generator.py`
- `core/model_manager.py`
- `core/tools/base.py`
- `core/tools/file_tools.py`
- `core/tools/directory_tools.py`

**日志埋点示例**:
```python
# ExcelProcessor.import_excel
logger.info("Excel 导入开始", extra={"file": excel_path})
# ... 处理 ...
logger.info("Excel 导入成功", extra={"departments": dept_count, "employees": emp_count})
```

### Step 4: 在数据层添加日志

**修改文件**:
- `data/database.py`
- `data/repositories/*.py` (按需)

### Step 5: 添加日志配置 UI

**修改文件**: `app/view/ai_settings_interface.py`

**新增内容**:
1. 日志级别下拉框（DEBUG/INFO/WARNING/ERROR）
2. 日志保留天数设置
3. 打开日志目录按钮
4. 实时日志预览（可选）

### Step 6: 更新测试

**修改文件**: `tests/test_core/test_logger.py` (新增)

**测试内容**:
1. JSON 格式输出测试
2. 日志轮转测试
3. 级别动态调整测试
4. 结构化日志字段测试

---

## 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `app/common/logger.py` | 核心日志模块重构 |
| 新增 | `app/common/log_config.py` | 日志配置管理 |
| 修改 | `core/excel_processor.py` | 添加导入日志 |
| 修改 | `core/ppt_generator.py` | 添加生成日志 |
| 修改 | `core/model_manager.py` | 添加模型/工具日志 |
| 修改 | `core/tools/base.py` | 添加安全验证日志 |
| 修改 | `data/database.py` | 添加数据库操作日志 |
| 修改 | `app/view/ai_settings_interface.py` | 添加日志配置 UI |
| 新增 | `tests/test_core/test_logger.py` | 日志模块测试 |

---

## 验收标准

1. [ ] 核心层/数据层关键流程都有日志埋点
2. [ ] 日志文件按 JSON 格式输出，包含 timestamp、level、name、message、extra 字段
3. [ ] 日志文件自动清理，只保留 7 天
4. [ ] AI 设置页面可调整日志级别，立即生效
5. [ ] 测试覆盖率 >= 80%

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 日志文件过大 | 磁盘空间 | 日志轮转 + 保留天数限制 |
| 敏感信息泄露 | 安全 | 文档说明不要记录敏感数据 |
| 性能影响 | 响应速度 | 使用异步日志（可选优化） |

---

## 预估工作量

- Step 1-2: 1-2 小时（日志模块重构）
- Step 3-4: 1-2 小时（添加日志埋点）
- Step 5: 1 小时（UI 配置）
- Step 6: 1 小时（测试）

**总计**: 4-6 小时
