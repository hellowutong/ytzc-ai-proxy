# 对话历史批量删除功能实施计划

## TL;DR
在对话历史列表页添加批量删除功能，包括前端UI的多选表格、批量删除按钮，以及后端批量删除API。

**实施范围**: 前端页面修改 + 后端API修改 + 文档更新
**预计时间**: 30分钟
**风险**: 低

---

## 任务清单

### 1. 后端API修改 (backend/api/admin/v1/conversations.py)

**需要添加**: 批量删除API端点

```python
@router.delete("/conversations/batch")
async def batch_delete_conversations(
    body: dict,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """批量删除对话"""
    ids = body.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="未提供对话ID列表")
    
    success_count = 0
    failed_ids = []
    
    for conversation_id in ids:
        try:
            success = await conversation_manager.delete_conversation(conversation_id)
            if success:
                success_count += 1
            else:
                failed_ids.append(conversation_id)
        except Exception:
            failed_ids.append(conversation_id)
    
    return {
        "code": 200,
        "message": f"已删除 {success_count} 个对话",
        "data": {
            "success_count": success_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        }
    }
```

### 2. 前端页面修改 (frontend/src/views/admin/Conversations.vue)

**需要修改**:

#### 2.1 工具栏添加批量删除按钮
- 在搜索框和时间选择器右侧添加批量删除按钮
- 按钮仅在选中对话时可用

#### 2.2 表格添加多选列
- 添加 `el-table-column type="selection"`
- 支持全选和单行选择

#### 2.3 添加选择管理逻辑
```typescript
const selectedConversations = ref<Conversation[]>([])

const handleSelectionChange = (selection: Conversation[]) => {
  selectedConversations.value = selection
}

const hasSelection = computed(() => selectedConversations.value.length > 0)

const batchDeleteConversations = async () => {
  const count = selectedConversations.value.length
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${count} 个对话吗？此操作不可恢复。`,
      '确认批量删除',
      { type: 'warning' }
    )
    
    const ids = selectedConversations.value.map(c => c.id)
    const response = await fetch('/admin/ai/v1/conversations/batch', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids })
    })
    const result = await response.json()
    
    if (result.code === 200) {
      await chatStore.fetchConversations()
      ElMessage.success(`成功删除 ${result.data.success_count} 个对话`)
      selectedConversations.value = []
    }
  } catch {
    // Cancelled
  }
}
```

### 3. 文档更新

#### 3.1 frontend_design.md
- 在对话历史筛选区添加"批量删除按钮"
- 在表格列添加"选择"列

#### 3.2 api_design.md
- 添加批量删除API文档:

```markdown
#### 2.5.6 批量删除

**DELETE** `/admin/ai/v1/conversations/batch`

**请求体**:
```json
{
  "ids": ["conv_001", "conv_002", "conv_003"]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "已删除 3 个对话",
  "data": {
    "success_count": 3,
    "failed_count": 0,
    "failed_ids": []
  }
}
```
```

### 4. 测试案例

添加测试案例到:
- `test/frontend/cases/conversations.test.json`: 批量删除UI测试
- `test/backend/cases/conversations.test.json`: 批量删除API测试

---

## 执行顺序

1. 修改后端API (conversations.py)
2. 修改前端页面 (Conversations.vue)
3. 更新设计文档
4. 重新部署测试

---

## 验收标准

- [x] 表格支持多选（复选框）
- [x] 工具栏显示批量删除按钮
- [x] 未选择时按钮禁用
- [x] 点击按钮显示确认对话框
- [x] 确认后批量删除成功
- [x] 列表刷新并显示成功消息
- [x] 后端API正确处理批量删除请求
