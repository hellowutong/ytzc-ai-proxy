# Chat Pipeline 测试案例

## 1. 单元测试

### 1.1 UserMessagePersistence Handler

**测试1**: 首次对话创建并保存用户消息
```
输入: 新对话（无conversation_id）
预期: 
  - 创建新对话返回ID
  - 用户消息保存到MongoDB
  - context.user_message_saved = True
```

**测试2**: 已有对话添加消息
```
输入: 已有conversation_id
预期:
  - 不创建新对话
  - 消息添加到现有对话
```

**测试3**: 数据库异常处理
```
输入: 数据库连接断开
预期:
  - 抛出异常
  - 不影响职责链继续执行（由ErrorRecoveryHandler处理）
```

### 1.2 KnowledgeRetrievalHandler

**测试1**: 知识库未启用
```
配置: knowledge.enabled = false
预期: 直接返回，不处理
```

**测试2**: 知识库启用但无Skill
```
配置: knowledge.enabled = true, skill.enabled = false
预期: 
  - 读取配置
  - metadata.knowledge_checked = True
  - 不调用Skill
```

### 1.3 WebSearchHandler

**测试1**: 4get空实现
```
配置: target包含4get
预期: 记录日志，不实际调用
```

**测试2**: LibreX预留
```
配置: target包含LibreX
预期: 记录日志"预留接口"
```

### 1.4 ModelRoutingHandler（关键词替换）

**测试1**: 关键词匹配并替换（@大哥）
```
输入: user_message = "@大哥 你是什么模型"
配置:
  routing.keywords.enabled = true
  routing.keywords.rules = [{pattern: "@大哥", target: "big"}]
预期:
  - context.model_type = "big"
  - context.metadata.route_reason = "关键词匹配: @大哥"
  - context.user_message = "你是什么模型"  # 关键词被移除
  - context.metadata.original_user_message = "@大哥 你是什么模型"
  - context.metadata.processed_user_message = "你是什么模型"
```

**测试2**: 关键词匹配并替换（@小弟）
```
输入: user_message = "@小弟 你好"
配置:
  routing.keywords.enabled = true
  routing.keywords.rules = [{pattern: "@小弟", target: "small"}]
预期:
  - context.model_type = "small"
  - context.metadata.route_reason = "关键词匹配: @小弟"
  - context.user_message = "你好"
```

**测试3**: 无关键词匹配，使用默认路由
```
输入: user_message = "你好"
配置:
  routing.keywords.enabled = true
  routing.keywords.rules = [{pattern: "@大哥", target: "big"}]
预期:
  - 继续调用ModelRouter.route()
  - context.model_type 根据路由决策确定
  - context.user_message 保持不变
```

**测试4**: 关键词功能未启用
```
输入: user_message = "@大哥 你好"
配置: routing.keywords.enabled = false
预期:
  - 跳过关键词匹配
  - 继续调用ModelRouter.route()
  - context.user_message 保持不变
```

**测试5**: 多个关键词匹配（首个匹配优先）
```
输入: user_message = "@大哥 @小弟 你好"
配置:
  routing.keywords.enabled = true
  routing.keywords.rules = [
    {pattern: "@大哥", target: "big"},
    {pattern: "@小弟", target: "small"}
  ]
预期:
  - 匹配"@大哥"（首个规则）
  - context.model_type = "big"
  - context.user_message = " @小弟 你好"  # 保留剩余内容
```

### 1.5 RawDataArchiveHandler

**测试1**: 正常归档
```
输入: 完整请求和响应
预期: 
  - 数据保存到raw_conversation_logs
  - 包含request, response, metadata
```

## 2. 集成测试

### 2.1 完整对话流程

**测试**: 正常对话流程
```
步骤:
  1. 用户发送"你好"
  2. 职责链处理
  3. 调用LLM
  4. 返回响应

验证:
  - 用户消息已保存
  - 助手回复已保存
  - Raw数据已归档
  - 响应包含conversation_id
```

### 2.2 错误恢复

**测试**: LLM调用失败
```
场景: LLM服务不可用

验证:
  - 用户消息仍然保存
  - 返回友好的错误提示
  - Raw数据记录错误信息
```

## 3. 边界测试

**测试1**: 超长输入
```
输入: 10000字符以上
预期: InputValidatorHandler拦截，返回错误
```

**测试2**: 空消息
```
输入: 空字符串或纯空格
预期: InputValidatorHandler拦截
```

**测试3**: 特殊字符
```
输入: 包含SQL注入/XSS尝试
预期: 安全过滤，正常处理或返回错误
```

## 4. 性能测试

**测试1**: 高并发处理
```
场景: 100个并发请求
预期:
  - 所有请求正常处理
  - 数据库连接池不耗尽
  - 响应时间 < 5秒
```

**测试2**: 大上下文
```
输入: messages包含50条历史
预期:
  - 正常处理
  - 响应时间可接受
```

## 5. 数据清理测试

**测试1**: 自动清理
```
配置: retention.days = 30
数据: 创建31天前的记录
预期: 清理任务删除过期记录
```

**测试2**: 保留最近数据
```
数据: 创建29天前的记录
预期: 不被清理
```

### 1.6 对话历史保存API

**测试1**: PUT更新对话消息
```
接口: PUT /admin/ai/v1/conversations/{id}
请求体: {messages: [...], updated_at: "..."}
预期:
  - 返回200
  - code = 200
  - message = "对话更新成功"
```

**测试2**: 对话不存在
```
接口: PUT /admin/ai/v1/conversations/{不存在id}
预期:
  - 返回404
  - detail = "对话不存在"
```

**测试3**: 405错误处理
```
场景: 前端调用不存在的端点
预期: 静默处理，不显示错误给用户
```
