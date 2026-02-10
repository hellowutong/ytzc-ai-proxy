# 使用说明

## 前后端统一 Mock 数据

**文件位置**: `test/shared/mock-data/api_mock_data.json`

**版本**: 2.0 (完整测试覆盖版)

**用途**:
1. 前端开发时使用 Mock 数据，不依赖后端
2. 后端测试时使用相同的 Mock 数据
3. **保证前后端数据格式完全一致**
4. 作为 API 契约的参考
5. **提供完整的测试数据覆盖**（正常、边界、异常）

**使用方式**:

### 前端使用

```typescript
// 在测试或 Mock 服务中导入
import mockData from '../../../test/shared/mock-data/api_mock_data.json'

// MSW (Mock Service Worker) 示例
rest.get('/admin/ai/v1/models', (req, res, ctx) => {
  return res(ctx.json(mockData.virtual_models.list))
})

// 或者在组件测试中使用
const mockModels = mockData.virtual_models.list.models
```

### 后端使用

```python
# 在测试中使用
import json

with open('test/shared/mock-data/api_mock_data.json', 'r', encoding='utf-8') as f:
    mock_data = json.load(f)

# 在测试中使用
async def test_get_models():
    expected = mock_data['virtual_models']['list']
    # 执行测试...
```

## 数据内容

### 1. 正常业务数据 (`api_mock_data.json`)

包含以下模块的 Mock 数据:

- `dashboard` - 看板统计、健康检查、活动日志
- `config` - 配置数据（当前配置、模板配置）
- `virtual_models` - 虚拟模型列表、创建请求/响应、测试连接响应
- `skills` - Skill 列表、详情、执行日志、统计
- `conversations` - 对话列表、详情
- `knowledge` - 知识库文档列表、配置、搜索结果
- `media` - 媒体文件列表（视频、音频）
- `rss` - RSS 订阅列表、文章列表
- `logs` - 系统日志、操作日志、Skill 日志
- `raw_data` - 原始数据（会话、媒体）
- `chat` - 对话请求/响应、模型列表

### 2. 边界测试数据 (`_test_scenarios.boundary_tests`)

**空值测试:**
- 空字符串、空数组、空对象、null值、空白字符

**极值长度测试:**
- 超短字符串（1-2字符）
- 超长字符串（100、1000、10000、100000字符）
- 数组边界（空、单元素、100元素、1000元素）

**特殊字符测试:**
- Unicode字符（中文、日文、韩文、阿拉伯文、俄文、emoji）
- 危险字符（XSS攻击、SQL注入、HTML标签、JavaScript）
- 控制字符（空字节、响铃、转义符）

**数值边界:**
- 整数边界（最小/最大整型、零、正负值）
- 浮点数边界（最大/最小浮点、科学计数法、极小值）

**日期时间边界:**
- 时间戳起点（epoch）
- 最小/最大日期
- 闰年、时区边界

**配置边界:**
- 深层嵌套（5层嵌套）
- 大量键值对（100个key）

### 3. 异常/错误数据 (`_test_scenarios.error_responses`)

**HTTP错误:**
- 400 Bad Request - 请求参数错误
- 401 Unauthorized - 认证失败
- 403 Forbidden - 权限不足
- 404 Not Found - 资源不存在
- 422 Validation Error - 验证失败（含多个字段错误）
- 429 Rate Limit - 频率限制
- 500 Internal Error - 服务器内部错误
- 502 Bad Gateway - 上游服务错误
- 503 Service Unavailable - 服务不可用
- 504 Gateway Timeout - 上游超时

**业务错误:**
- Skill验证/执行失败
- 配置验证失败（含详细路径）
- 模型不存在/重复名称
- Proxy Key无效
- 数据库连接错误
- 向量搜索错误
- 文件上传错误（大小超限）
- 转录失败

**网络错误:**
- 连接被拒绝
- 请求超时
- DNS解析失败

### 4. 边界情况 (`_test_scenarios.edge_cases`)

**并发操作:**
- 同时修改同一资源
- 竞态条件
- 部分失败场景

**资源耗尽:**
- 磁盘满、内存耗尽、连接数超限

**数据损坏:**
- 无效JSON、校验和不匹配、孤儿记录

### 5. 压力测试数据 (`_test_scenarios.load_test_data`)

**高容量数据:**
- 10万会话、1万文档、5000媒体文件
- 突发流量：1000 RPS、500并发用户

## 维护规范

1. **修改时必须同步更新前后端** - 保持数据一致性
2. **添加新字段时在文档中标注** - 说明字段用途
3. **保留历史版本** - 重大变更时创建备份文件
4. **与 api_design.md 保持一致** - 数据格式必须符合 API 设计文档

## 文件结构

```
test/shared/mock-data/
├── api_mock_data.json      # 主要 Mock 数据文件
├── README.md               # 本说明文件
└── backups/                # 历史版本备份
    ├── api_mock_data_v1.json
    └── api_mock_data_v2.json
```
