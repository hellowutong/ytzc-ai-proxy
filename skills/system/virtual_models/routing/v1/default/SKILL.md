---
name: default
description: 默认路由规则
type: rule-based
priority: 50
version: "v1"
input_schema:
  type: object
  properties:
    message:
      type: string
output_schema:
  type: object
  properties:
    result:
      type: string
---

# Default Routing Skill

这是默认的模型路由规则。

## 功能说明

根据用户输入的关键词或意图，自动选择合适的模型进行响应。

## 规则定义

当前为默认配置，暂无特定规则。
