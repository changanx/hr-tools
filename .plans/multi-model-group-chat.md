# 多模型群聊功能设计方案

## 需求总结

### 对话模式
| 特性 | 选择 |
|------|------|
| 模型交互方式 | 接力讨论（模型之间可以看到彼此的回复并讨论） |
| 回复机制 | 两者结合（默认全部回复，支持@指定） |
| UI 布局 | 单列时间线（同一滚动区域按时间展示） |
| 消息引用 | 两者结合（@语法 + UI 选择器） |
| 参与机制 | 角色预设（每个模型有预设角色描述，理解自己的定位） |
| 历史记录 | 全部可见（所有模型都能看到用户消息 + 其他模型回复） |
| 并发控制 | 首批并发，讨论串行 |
| 结束判断 | 模型判断 + 最大轮次限制 |

### 功能描述

用户可以创建一个"群聊会话"，邀请多个 AI 模型参与。在群聊中：
- 每个参与模型有**预设角色描述**，理解自己在群聊中的定位
- 用户发消息时可以 **@特定模型** 让其回复
- 被 @ 的模型**并发回复**，之后**串行讨论**
- 所有模型能看到**完整对话历史**
- 界面采用**单列时间线**展示
- 讨论结束由**模型判断**或**最大轮次限制**控制

---

## 架构设计

### 1. 数据模型扩展

#### 新增表：`group_chat_session`（群聊会话）

```sql
CREATE TABLE group_chat_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT '新群聊',
    max_discussion_rounds INTEGER DEFAULT 3,  -- 最大讨论轮次
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 新增表：`group_chat_participant`（群聊参与者）

```sql
CREATE TABLE group_chat_participant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    model_config_id INTEGER NOT NULL,
    nickname TEXT,                      -- 群聊中的昵称（如 @gpt4）
    role_description TEXT,              -- 角色描述（让模型理解自己的定位）
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES group_chat_session(id) ON DELETE CASCADE,
    FOREIGN KEY (model_config_id) REFERENCES ai_model_config(id)
);
```

#### 新增表：`group_chat_message`（群聊消息）

```sql
CREATE TABLE group_chat_message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,                 -- 'user', 'assistant', 'host'
    model_config_id INTEGER,            -- 哪个模型的回复（assistant 时）
    content TEXT NOT NULL,
    mentioned_models TEXT,              -- JSON 数组，被 @ 的模型 ID 列表
    parent_message_id INTEGER,          -- 回复的上一条消息（用于讨论链）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES group_chat_session(id) ON DELETE CASCADE,
    FOREIGN KEY (model_config_id) REFERENCES ai_model_config(id)
);
```

#### Python 数据类

```python
# data/models/group_chat.py

@dataclass
class GroupChatSession:
    id: Optional[int] = None
    title: str = "新群聊"
    max_discussion_rounds: int = 3  # 最大讨论轮次
    created_at: str = ""
    updated_at: str = ""

@dataclass
class GroupChatParticipant:
    id: Optional[int] = None
    session_id: int = 0
    model_config_id: int = 0
    nickname: str = ""  # 默认使用模型名
    role_description: str = ""  # 角色描述
    joined_at: str = ""

@dataclass
class GroupChatMessage:
    id: Optional[int] = None
    session_id: int = 0
    role: str = "user"  # user, assistant
    model_config_id: Optional[int] = None
    content: str = ""
    mentioned_models: List[int] = field(default_factory=list)
    discussion_round: int = 0  # 第几轮讨论
    created_at: str = ""
```

### 2. 业务逻辑层

#### `core/group_chat_manager.py`

```python
class GroupChatManager:
    """群聊管理器"""

    def __init__(self):
        self._session_models: Dict[int, Dict[int, Any]] = {}  # session_id -> {model_id -> model}
        self._discussion_round: Dict[int, int] = {}  # session_id -> current_round

    def create_session(self, title: str, max_rounds: int = 3) -> GroupChatSession:
        """创建群聊会话"""
        pass

    def add_participant(self, session_id: int, model_config_id: int, 
                        nickname: str = None, role_description: str = ""):
        """添加参与模型"""
        pass

    def remove_participant(self, session_id: int, model_config_id: int):
        """移除参与模型"""
        pass

    def chat(self, session_id: int, user_message: str, 
             mentioned_model_ids: List[int] = None) -> Generator:
        """
        发送消息并获取多模型回复

        流程：
        1. 保存用户消息
        2. 解析 @ 提及的模型
        3. 构建带角色描述的 system prompt
        4. 并发调用被 @ 的模型（或所有参与者）
        5. 收集回复并 yield
        6. 判断是否继续讨论（轮次 + 模型判断）
        """
        pass

    def _build_system_prompt(self, participant: GroupChatParticipant, 
                              all_participants: List[GroupChatParticipant]) -> str:
        """构建带角色描述的 system prompt"""
        others = [p.nickname for p in all_participants if p.id != participant.id]
        
        prompt = f"""你正在参与一个多模型群聊讨论。

你的昵称是: {participant.nickname}
其他参与者: {', '.join(others)}

{participant.role_description}

当回复时：
1. 你可以引用其他模型的发言，例如："我同意 @{others[0]} 的观点..."
2. 如果用户 @ 了你，你应该优先回复
3. 如果你认为讨论已经结束，请在回复末尾说 [讨论结束]
"""
        return prompt

    def _should_continue_discussion(self, responses: List[str], 
                                     current_round: int, max_rounds: int) -> bool:
        """判断是否继续讨论"""
        if current_round >= max_rounds:
            return False
        
        # 检查是否有模型说 [讨论结束]
        for resp in responses:
            if "[讨论结束]" in resp:
                return False
        
        return True

    def _call_models_concurrent(self, model_ids: List[int], messages: List[Dict]) -> Generator:
        """并发调用多个模型"""
        pass

    def _call_models_serial(self, model_ids: List[int], messages: List[Dict]) -> Generator:
        """串行调用多个模型（用于讨论阶段）"""
        pass

    def _build_context(self, session_id: int) -> List[Dict]:
        """构建对话上下文（包含所有模型回复）"""
        pass

    def parse_mentions(self, content: str, participants: List[GroupChatParticipant]) -> List[int]:
        """解析消息中的 @ 提及"""
        pass
```

#### 消息格式设计

为了让模型理解群聊上下文，消息格式如下：

```python
# 用户消息
{
    "role": "user",
    "content": "请分析这段代码",
    "metadata": {
        "mentioned_models": [1, 2]  # @gpt-4 @deepseek
    }
}

# 模型回复（带标识）
{
    "role": "assistant",
    "content": "我认为这段代码...",
    "metadata": {
        "model_id": 1,
        "model_name": "gpt-4",
        "nickname": "@gpt-4"
    }
}

# 发送给模型时的 system prompt
system_prompt = """
你正在参与一个多模型群聊。你的昵称是 @gpt-4。
其他参与者：@claude, @deepseek

你是代码审查专家，专注于：
- 代码质量和可维护性
- 设计模式应用
- 潜在 bug 发现

当回复时：
1. 你可以引用其他模型的发言，例如："我同意 @deepseek 的观点..."
2. 如果用户 @ 了你，你应该优先回复
3. 如果你认为讨论已经结束，请在回复末尾说 [讨论结束]
"""
```

### 3. UI 层设计

#### 界面切换

在主窗口添加模式切换：

```
┌─────────────────────────────────────────────────────────────┐
│ [单聊] [群聊]  |  工作目录: [选择]                          │
└─────────────────────────────────────────────────────────────┘

单聊模式: 现有的 AIChatInterface
群聊模式: 新的 GroupChatInterface
```

#### 群聊界面 `GroupChatInterface`

```
┌─────────────────────────────────────────────────────────────┐
│ 群聊标题: [代码审查小组]     最大轮次: [3]      [设置] [新建]│
├─────────────────────────────────────────────────────────────┤
│ 参与模型: [+ 添加]                                          │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ 🤖 GPT-4    │ │ 🤖 Claude   │ │ 🤖 DeepSeek │            │
│ │ @gpt-4      │ │ @claude     │ │ @deepseek   │            │
│ │ 代码审查专家 │ │ 架构分析师  │ │ 性能优化师  │            │
│ │ [编辑] [移除]│ │ [编辑] [移除]│ │ [编辑] [移除]│            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│ 消息区域（单列时间线）                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 👤 用户: 请分析这段代码                                  │ │
│ │    @gpt-4 @deepseek 请你们重点看性能问题                 │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 🤖 GPT-4:                                               │ │
│ │    我分析了代码，发现几个性能问题...                      │ │
│ │    [思考过程] [工具调用]                                 │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 🤖 DeepSeek:                                            │ │
│ │    我同意 @gpt-4 的分析，补充一点...                     │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 🤖 Claude:                                              │ │
│ │    从架构角度，我建议...                                 │ │
│ │    [讨论结束]                                           │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ @ 提及: [✓ GPT-4] [✓ Claude] [✓ DeepSeek] [全选] [清除]   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 输入消息... (@ 提及模型)                                 │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                           [发送] [停止]     │
└─────────────────────────────────────────────────────────────┘
```

#### 参与者编辑对话框 `ParticipantEditDialog`

```
┌─────────────────────────────────┐
│ 添加/编辑参与者                  │
├─────────────────────────────────┤
│ 选择模型: [GPT-4         ▼]     │
│                                 │
│ 昵称:    [@gpt-4           ]   │
│                                 │
│ 角色描述:                       │
│ ┌─────────────────────────────┐ │
│ │ 你是代码审查专家，专注于：   │ │
│ │ - 代码质量和可维护性         │ │
│ │ - 设计模式应用               │ │
│ │ - 潜在 bug 发现              │ │
│ └─────────────────────────────┘ │
│                                 │
│            [取消]  [确定]       │
└─────────────────────────────────┘
```

#### 消息组件 `GroupChatMessageWidget`

```python
class GroupChatMessageWidget(QWidget):
    """群聊消息组件"""

    def __init__(self, role: str, content: str, model_info: Dict = None):
        # role: "user", "assistant", "host"
        # model_info: {"id": 1, "name": "GPT-4", "nickname": "@gpt-4"}
        pass

    def set_model_avatar(self, model_name: str):
        """设置模型头像/图标"""
        pass

    def append_thinking(self, text: str):
        """追加思考过程"""
        pass

    def append_content(self, text: str):
        """追加内容"""
        pass
```

### 4. 并发调用实现

```python
# core/group_chat_manager.py

import concurrent.futures
from typing import Generator, Dict, Any, List

class GroupChatManager:
    
    def _call_models_concurrent(self, model_ids: List[int], messages: List[Dict]) -> Generator:
        """并发调用多个模型"""
        
        results = {}  # model_id -> response chunks
        
        def call_model(model_id: int):
            model = self._get_model(model_id)
            chunks = []
            for chunk in model.stream(messages):
                chunks.append(chunk)
            return model_id, chunks
        
        # 使用 ThreadPoolExecutor 并发调用
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_ids)) as executor:
            futures = {executor.submit(call_model, mid): mid for mid in model_ids}
            
            for future in concurrent.futures.as_completed(futures):
                model_id, chunks = future.result()
                yield {
                    "type": "model_response_start",
                    "model_id": model_id
                }
                for chunk in chunks:
                    yield chunk
                yield {
                    "type": "model_response_end",
                    "model_id": model_id
                }
```

### 5. @ 提及解析

```python
import re

def parse_mentions(content: str, participants: List[GroupChatParticipant]) -> List[int]:
    """解析消息中的 @ 提及"""
    mentioned_ids = []
    
    # 匹配 @nickname 或 @模型名
    pattern = r'@(\w+)'
    matches = re.findall(pattern, content)
    
    for match in matches:
        for p in participants:
            if p.nickname == f"@{match}" or p.nickname == match:
                mentioned_ids.append(p.model_config_id)
                break
    
    return list(set(mentioned_ids))  # 去重
```

---

## 实现计划

### 阶段一：数据层 (1-2 天)
1. 创建数据模型 `data/models/group_chat.py`
   - `GroupChatSession`
   - `GroupChatParticipant`（含 role_description）
   - `GroupChatMessage`
2. 创建数据仓库 `data/repositories/group_chat_repository.py`
3. 扩展数据库表结构 `data/database.py`
4. 编写数据层单元测试

### 阶段二：业务逻辑层 (2-3 天)
1. 创建群聊管理器 `core/group_chat_manager.py`
   - 会话管理（创建/删除/查询）
   - 参与者管理（添加/移除/编辑角色）
   - @ 提及解析
   - 对话上下文构建
   - System Prompt 生成（带角色描述）
2. 实现并发模型调用（ThreadPoolExecutor）
3. 实现讨论结束判断逻辑
4. 编写业务层单元测试

### 阶段三：UI 层 (2-3 天)
1. 创建参与者编辑对话框 `app/components/participant_edit_dialog.py`
2. 创建群聊消息组件 `app/components/group_chat_message_widget.py`
   - 显示模型昵称和头像
   - 思考过程折叠展示
   - 工具调用展示
3. 创建群聊界面 `app/view/group_chat_interface.py`
   - 参与者管理区域
   - @ 提及选择器
   - 消息时间线
   - 输入区域
4. 修改主窗口，添加模式切换（单聊/群聊）
5. 编写 UI 层测试

### 阶段四：集成测试与优化 (1-2 天)
1. 编写端到端集成测试
2. 性能优化（并发调用、UI 响应）
3. 边界情况处理（API 限流、超时、错误）
4. 用户体验优化（加载状态、错误提示）

---

## 关键决策点

### Q1: 模型回复时是否知道自己是谁？

**决定**: 是的，通过 System Prompt 告知每个模型自己的昵称、角色和其他参与者

### Q2: 讨论串行调用时，如何判断讨论结束？

**决定**: 双重机制
1. 模型在回复末尾说 `[讨论结束]`
2. 配置最大讨论轮次（默认 3 轮）

### Q3: 角色描述如何设置？

**决定**: 用户在添加参与者时可以编辑角色描述，提供预设模板：
- 代码审查专家
- 架构分析师
- 性能优化师
- 测试工程师
- 安全审计员
- 自定义...

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 并发调用 API 限流 | 实现请求队列，控制并发数 |
| 上下文过长超 token | 实现上下文压缩/摘要 |
| 模型回复顺序混乱 | 使用时间戳和消息 ID 排序 |
| UI 卡顿 | 使用多线程，异步更新 UI |

---

## 下一步

确认以上设计方案后，我将创建详细的实现计划。
