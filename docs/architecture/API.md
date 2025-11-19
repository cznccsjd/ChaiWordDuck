# 拆词鸭 ChaiWord Duck - API 文档

## 1. API 概述

### 1.1 基本信息

- **基础URL**: `https://api.chaiwordduck.com/v1`
- **协议**: HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **API版本**: v1.0 (支持多语言)

### 1.2 认证方式

```http
# 注册用户认证 (可选)
Authorization: Bearer {jwt_token}

# 游客模式无需认证
```

### 1.3 通用响应格式

#### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "timestamp": "2025-10-26T10:00:00.000Z"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": { ... }
  },
  "timestamp": "2025-10-26T10:00:00.000Z"
}
```

---

## 2. 单词查询 API

### 2.1 查询单词

#### 端点
```http
GET /api/v1/words/query/{word}
```

#### 描述
查询单词的详细学习信息，支持多语言和向后兼容。

#### 请求参数

| 参数 | 类型 | 必需 | 描述 | 示例 |
|------|------|------|------|------|
| word | string | 是 | 要查询的单词 | accountability |
| include_legacy | boolean | 否 | 是否包含向后兼容字段 | false |
| language_code | string | 否 | 首选语言代码 | zh_CN |

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| word | string | 要查询的英文单词 |

#### 查询参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| include_legacy | boolean | false | 是否返回向后兼容的旧格式字段 |
| language_code | string | auto | 首选语言代码 (en, zh_CN, zh_TW, ja, ko, fr, de, es, it, ru) |

#### 响应示例

**英语版本响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "word": "accountability",
    "phonetic": "/əˌkaʊntəˈbɪləti/",
    "translation": null,
    "part_of_speech": "noun",
    "language_code": "en",
    "core_game": {
      "content": "问责制的核心是'能算清账'",
      "difficulty_level": "intermediate",
      "estimated_time": "8分钟",
      "learning_objectives": [
        "理解accountability的含义",
        "学习问责制的概念",
        "掌握相关用法"
      ]
    },
    "game_boards": {
      "board_a_speculative": {
        "type": "棋盘A (思辨场)",
        "name": "思辨场景",
        "example": "在企业管理中，建立问责制是提高效率的关键",
        "context": "business_management",
        "formality_level": "formal"
      },
      "board_b_life": {
        "type": "棋盘B (生活场)",
        "name": "生活场景",
        "example": "A good friend holds you accountable for your promises",
        "context": "friendship",
        "formality_level": "informal"
      }
    },
    "etymology": {
      "breakdown": {
        "prefix": {
          "part": "ac-",
          "meaning": "toward",
          "examples": ["account", "achieve"]
        },
        "root": {
          "part": "count",
          "meaning": "to count",
          "examples": ["count", "counter"]
        },
        "suffix": {
          "part": "-ability",
          "meaning": "quality of being",
          "examples": ["ability", "capability"]
        }
      },
      "story": "源自拉丁语computare，意为计算。后来演变为accountable（可算清账的），加上-ability后缀表示可问责的特性",
      "historical_usage": [
        {
          "period": "古英语",
          "form": "accounten",
          "meaning": "计算"
        },
        {
          "period": "中古英语",
          "form": "accountable",
          "meaning": "可算清账的"
        }
      ]
    },
    "common_mistakes": {
      "warning": "拼写时容易漏掉第二个'c'或'm'",
      "avoidance": "记住：account(账户) + ability(能力)，两个都要算清楚",
      "examples": [
        {
          "wrong": "acountability",
          "correct": "accountability",
          "explanation": "缺少第二个'c'"
        },
        {
          "wrong": "accountablity",
          "correct": "accountability",
          "explanation": "缺少第二个'm'"
        }
      ]
    },
    "memory_trick": "想象一个会计在仔细计算账户(account)，确保每个数字都对得上(ability)",
    "is_golden": true,
    "source": "manual",
    "prompt_version": "v2.0",
    "remaining_queries": 7,
    "total_queries": 10,
    "user_type": "guest"
  },
  "timestamp": "2025-10-26T10:00:00.000Z"
}
```

**中文翻译版本响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "word": "accountability",
    "phonetic": "/əˌkaʊntəˈbɪləti/",
    "translation": "问责制，问责性，负责程度",
    "part_of_speech": "名词",
    "language_code": "zh_CN",
    "core_game": {
      "content": "问责制的核心是'能算清账'：就像会计要把账目算清楚一样，做错事的人也要承担责任，把责任算清楚",
      "difficulty_level": "intermediate",
      "estimated_time": "8分钟",
      "learning_objectives": [
        "理解问责制的中文含义",
        "掌握相关中文表达",
        "学会在中文语境中使用"
      ]
    },
    "game_boards": {
      "board_a_speculative": {
        "type": "棋盘A (思辨场)",
        "name": "思辨场景",
        "example": "在企业治理中，建立问责制是确保管理层对股东负责的关键机制",
        "context": "corporate_governance",
        "formality_level": "formal"
      },
      "board_b_life": {
        "type": "棋盘B (生活场)",
        "name": "生活场景",
        "example": "好朋友之间也要相互负责，说到做到",
        "context": "friendship",
        "formality_level": "informal"
      }
    },
    "etymology": {
      "breakdown": {
        "prefix": {
          "part": "ac-",
          "meaning": "向，朝向",
          "examples": ["approach", "accompany"]
        },
        "root": {
          "part": "count",
          "meaning": "计算，数数",
          "examples": ["count", "counter", "account"]
        },
        "suffix": {
          "part": "-ability",
          "meaning": "能够，能力",
          "examples": ["ability", "capability", "responsibility"]
        }
      },
      "story": "这个单词来自拉丁语computare（计算）→古法语aconter→英语account（账户）。加上后缀-ability变成'可以被计算的性质'，引申为'可以被追究责任的性质'。在中文里，我们理解为'把责任算清楚'的能力，也就是问责制。",
      "historical_usage": [
        {
          "period": "16世纪",
          "form": "accountable",
          "meaning": "可算清账的，应负责的"
        },
        {
          "period": "18世纪",
          "form": "accountability",
          "meaning": "问责制，应负责任的状态"
        }
      ]
    },
    "common_mistakes": {
      "warning": "中文拼写虽然不会错，但要注意：这个词不是简单的'账目'，而是'追究责任'的概念",
      "avoidance": "记住：account(算账) + ability(能力) = 能够追究责任的能力",
      "examples": [
        {
          "wrong": "这是账目问题",
          "correct": "这是问责制问题",
          "explanation": "accountability不是指账目，而是指追究责任的制度"
        }
      ]
    },
    "memory_trick": "想象一个会计拿着算盘正在算账，一边算一边说'你要负责任！' - 这就是accountability",
    "is_golden": true,
    "source": "manual",
    "prompt_version": "v2.0",
    "remaining_queries": 6,
    "total_queries": 10,
    "user_type": "guest"
  },
  "timestamp": "2025-10-26T10:00:00.000Z"
}
```

#### 向后兼容字段 (`include_legacy=true`)

```json
{
  "data": {
    // ... 现代格式字段 ...
    "scenario_formal": "在企业管理中，建立问责制是提高效率的关键",
    "scenario_casual": "A good friend holds you accountable for your promises",
    "etymology_breakdown": "ac-count-ability",
    "etymology_story": "源自拉丁语computare，意为计算...",
    "common_mistakes": "拼写时容易漏掉第二个'c'或'm'",
    "memory_trick": "记住：account(账户) + ability(能力)"
  }
}
```

#### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "WORD_NOT_FOUND",
    "message": "单词不存在",
    "details": {
      "word": "nonexistentword123",
      "suggestion": "请检查拼写或尝试相关词汇"
    }
  },
  "timestamp": "2025-10-26T10:00:00.000Z"
}
```

### 2.2 获取单词详情（ID）

#### 端点
```http
GET /api/v1/words/{word_id}
```

#### 描述
根据单词ID获取详细信息，不计入查询次数限制。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| word_id | integer | 单词的唯一标识符 |

#### 查询参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| include_legacy | boolean | false | 是否包含向后兼容字段 |
| language_code | string | auto | 首选语言代码 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "id": 1,
    "word": "accountability",
    "phonetic": "/əˌkaʊntəˈbɪləti/",
    "translation": "问责制，问责性，负责程度",
    "part_of_speech": "noun",
    "language_code": "zh_CN",
    // ... 其他字段与单词查询API相同 ...
  }
}
```

### 2.3 搜索单词

#### 端点
```http
GET /api/v1/words/search/{query}
```

#### 描述
根据部分匹配搜索单词列表。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| query | string | 搜索关键词（至少3个字符） |

#### 查询参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| language_code | string | auto | 按语言过滤 |
| is_golden | boolean | null | 是否只搜索黄金手册 |
| limit | integer | 20 | 返回结果数量限制 (1-100) |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "words": [
      {
        "id": 1,
        "word": "accountability",
        "phonetic": "/əˌkaʊntəˈbɪləti/",
        "translation": "问责制，问责性",
        "language_code": "zh_CN",
        "is_golden": true
      },
      {
        "id": 25,
        "word": "accountable",
        "phonetic": "/əˈkaʊntəbl/",
        "translation": "应负责任的，可问责的",
        "language_code": "zh_CN",
        "is_golden": false
      }
    ],
    "total_count": 2,
    "has_more": false
  }
}
```

---

## 3. 查询限制 API

### 3.1 获取查询限制信息

#### 端点
```http
GET /api/v1/words/query-limit
```

#### 描述
获取当前用户的查询限制和使用情况，支持游客和注册用户。

#### 查询参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| language_code | string | auto | 返回信息的语言 |

#### 响应示例

**游客模式**:
```json
{
  "success": true,
  "data": {
    "user_type": "guest",
    "remaining_queries": 7,
    "used_queries": 3,
    "total_queries": 10,
    "reset_at": "2025-10-27T00:00:00Z",
    "upgrade_message": "注册可获得每日50次查询 + 收藏功能",
    "queried_words": [
      {
        "id": 1,
        "word": "accountability",
        "queried_at": "2025-10-26T09:15:30Z"
      },
      {
        "id": 12,
        "word": "entrepreneurship",
        "queried_at": "2025-10-26T09:20:45Z"
      },
      {
        "id": 8,
        "word": "procrastination",
        "queried_at": "2025-10-26T09:25:12Z"
      }
    ]
  },
  "timestamp": "2025-10-26T10:00:00.000Z"
}
```

**注册用户**:
```json
{
  "success": true,
  "data": {
    "user_type": "free",
    "remaining_queries": 42,
    "used_queries": 8,
    "total_queries": 50,
    "reset_at": "2025-10-27T00:00:00Z",
    "upgrade_message": "升级Premium可获得无限查询",
    "queried_words": [
      // ... 查询历史 ...
    ]
  }
}
```

**Premium用户**:
```json
{
  "success": true,
  "data": {
    "user_type": "premium",
    "remaining_queries": -1,
    "used_queries": 15,
    "total_queries": -1,
    "unlimited": true,
    "queried_words": [
      // ... 查询历史 ...
    ]
  }
}
```

---

## 4. 多语言支持 API

### 4.1 获取支持的语言列表

#### 端点
```http
GET /api/v1/languages/supported
```

#### 描述
获取系统支持的所有语言及其配置信息。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "supported_languages": [
      {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "default_prompt_version": "v2.0",
        "is_default": true,
        "translation_available": false
      },
      {
        "code": "zh_CN",
        "name": "Simplified Chinese",
        "native_name": "简体中文",
        "default_prompt_version": "v2.0",
        "is_default": false,
        "translation_available": true,
        "supported_prompt_versions": ["v1.0", "v2.0"]
      },
      {
        "code": "zh_TW",
        "name": "Traditional Chinese",
        "native_name": "繁體中文",
        "default_prompt_version": "v2.0",
        "is_default": false,
        "translation_available": true
      },
      {
        "code": "ja",
        "name": "Japanese",
        "native_name": "日本語",
        "default_prompt_version": "v2.0",
        "is_default": false,
        "translation_available": true
      }
    ]
  }
}
```

### 4.2 设置用户语言偏好

#### 端点
```http
POST /api/v1/users/language-preference
```

#### 描述
设置用户的语言偏好（需要认证）。

#### 请求体

```json
{
  "language_code": "zh_CN",
  "prompt_version": "v2.0"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "language_code": "zh_CN",
    "prompt_version": "v2.0",
    "updated_at": "2025-10-26T10:00:00Z"
  },
  "message": "语言偏好设置成功"
}
```

### 4.3 生成多语言单词内容

#### 端点
```http
POST /api/v1/words/generate-multilang
```

#### 描述
为指定单词生成多语言学习内容（管理员功能，需要认证）。

#### 请求体

```json
{
  "word": "accountability",
  "target_languages": ["zh_CN", "ja", "ko"],
  "prompt_version": "v2.0",
  "force_regenerate": false
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "word": "accountability",
    "generated_content": {
      "zh_CN": {
        "translation": "问责制，问责性，负责程度",
        "core_game_new": {
          "content": "问责制的核心是'能算清账'...",
          "difficulty_level": "intermediate"
        },
        "game_boards": { ... },
        "etymology_new": { ... },
        "common_mistakes_new": { ... }
      },
      "ja": {
        "translation": "アカウンタビリティ、説明責任",
        "core_game_new": { ... },
        // ... 其他字段 ...
      },
      "ko": {
        "translation": "책임성, 설명 책임",
        "core_game_new": { ... },
        // ... 其他字段 ...
      }
    },
    "generation_time_ms": 3500,
    "prompt_version": "v2.0"
  }
}
```

---

## 5. 用户认证 API

### 5.1 用户注册（支持游客迁移）

#### 端点
```http
POST /api/v1/auth/register
```

#### 描述
注册新用户账户，支持游客数据迁移。

#### 请求体

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "language_preference": "zh_CN",
  "guest_session_id": "abc123def456...",  // 可选，游客数据迁移
  "accept_terms": true
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "language_preference": "zh_CN",
      "membership_tier": "free",
      "created_at": "2025-10-26T10:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 10080,  // 7天（分钟）
    "migrated_data": {
      "query_logs_migrated": 3,
      "guest_session_converted": true,
      "migrated_at": "2025-10-26T10:00:00Z"
    }
  },
  "message": "注册成功，游客数据已迁移"
}
```

---

## 6. 收藏管理 API

### 6.1 添加收藏

#### 端点
```http
POST /api/v1/favorites
```

#### 描述
将单词添加到用户收藏列表。

#### 请求体

```json
{
  "word_id": 1,
  "language_code": "zh_CN",  // 可选，用于个性化推荐
  "note": "这个单词很有用"  // 可选，用户笔记
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "id": 456,
    "user_id": 123,
    "word_id": 1,
    "word": "accountability",
    "translation": "问责制，问责性",
    "language_code": "zh_CN",
    "note": "这个单词很有用",
    "created_at": "2025-10-26T10:00:00Z"
  },
  "message": "收藏成功"
}
```

### 6.2 获取收藏列表

#### 端点
```http
GET /api/v1/favorites
```

#### 描述
获取用户的收藏列表，支持多语言。

#### 查询参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| language_code | string | auto | 按语言过滤收藏 |
| limit | integer | 50 | 返回数量限制 |
| offset | integer | 0 | 分页偏移量 |
| sort_by | string | created_at | 排序字段 (created_at, word) |
| sort_order | string | desc | 排序方向 (asc, desc) |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "favorites": [
      {
        "id": 456,
        "word_id": 1,
        "word": "accountability",
        "translation": "问责制，问责性，负责程度",
        "phonetic": "/əˌkaʊntəˈbɪləti/",
        "language_code": "zh_CN",
        "note": "这个单词很有用",
        "is_golden": true,
        "created_at": "2025-10-26T09:15:30Z"
      }
    ],
    "total_count": 1,
    "has_more": false
  }
}
```

---

## 7. 错误代码参考

### 7.1 通用错误码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| METHOD_NOT_ALLOWED | 405 | HTTP方法不允许 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| INTERNAL_SERVER_ERROR | 500 | 服务器内部错误 |

### 7.2 业务特定错误码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| WORD_NOT_FOUND | 404 | 单词不存在 |
| QUERY_LIMIT_EXCEEDED | 429 | 查询次数用尽 |
| DUPLICATE_FAVORITE | 400 | 重复收藏 |
| FAVORITE_NOT_FOUND | 404 | 收藏不存在 |
| INVALID_LANGUAGE_CODE | 400 | 无效的语言代码 |
| UNSUPPORTED_PROMPT_VERSION | 400 | 不支持的Prompt版本 |
| AI_GENERATION_FAILED | 503 | AI生成失败 |
| GUEST_SESSION_EXPIRED | 401 | 游客会话过期 |
| EMAIL_ALREADY_EXISTS | 400 | 邮箱已存在 |
| INVALID_CREDENTIALS | 401 | 登录凭据无效 |

---

## 8. 请求限制

### 8.1 用户级别限制

| 用户类型 | 每日查询限制 | 说明 |
|---------|-------------|------|
| 游客 | 10次 | 基于IP+设备指纹识别 |
| 免费用户 | 50次 | 需要邮箱注册 |
| Premium用户 | 无限 | 付费用户 |

### 8.2 IP级别限制

| 限制类型 | 频率 | 说明 |
|---------|------|------|
| API请求 | 30次/分钟 | 防爬虫和DDoS |
| AI生成 | 5次/小时/IP | 控制成本 |
| 注册请求 | 3次/小时/IP | 防止垃圾注册 |

### 8.3 限制响应格式

```json
{
  "success": false,
  "error": {
    "code": "QUERY_LIMIT_EXCEEDED",
    "message": "今日查询次数已用完（10次/天）",
    "details": {
      "user_type": "guest",
      "used_queries": 10,
      "total_queries": 10,
      "reset_at": "2025-10-27T00:00:00Z",
      "upgrade_message": "注册可获得每日50次查询 + 收藏功能"
    }
  },
  "timestamp": "2025-10-26T10:00:00.000Z"
}
```

---

## 9. 多语言支持详情

### 9.1 支持的语言

| 语言代码 | 语言名称 | Prompt版本 | 翻译支持 | 状态 |
|---------|---------|-----------|---------|------|
| en | English | v1.0, v2.0 | ❌ | 完全支持 |
| zh_CN | 简体中文 | v1.0, v2.0 | ✅ | 完全支持 |
| zh_TW | 繁体中文 | v2.0 | ✅ | 测试阶段 |
| ja | 日本語 | v2.0 | ✅ | 测试阶段 |
| ko | 한국어 | v2.0 | ✅ | 开发中 |
| fr | Français | v2.0 | ✅ | 开发中 |
| de | Deutsch | v2.0 | ✅ | 开发中 |
| es | Español | v2.0 | ✅ | 开发中 |
| it | Italiano | v2.0 | ✅ | 开发中 |
| ru | Русский | v2.0 | ✅ | 开发中 |

### 9.2 语言偏好处理

```http
# 1. 自动检测用户语言
GET /api/v1/words/query/hello
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8

# 2. 显式指定语言
GET /api/v1/words/query/hello?language_code=zh_CN

# 3. 用户设置偏好
POST /api/v1/users/language-preference
{
  "language_code": "zh_CN",
  "prompt_version": "v2.0"
}
```

### 9.3 翻译字段说明

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| translation | string | 单词的主要翻译 | 问责制，问责性，负责程度 |
| language_code | string | 内容的主要语言 | zh_CN |
| prompt_version | string | 使用的Prompt版本 | v2.0 |
| is_legacy_format | boolean | 是否为旧格式数据 | false |

---

## 10. SDK和客户端库

### 10.1 JavaScript/TypeScript SDK

```typescript
// npm install chaiword-duck-api
import { ChaiWordDuckAPI } from 'chaiword-duck-api';

const api = new ChaiWordDuckAPI({
  baseURL: 'https://api.chaiwordduck.com/v1',
  token: 'your-jwt-token', // 可选，游客模式可不提供
  languageCode: 'zh_CN',  // 默认语言
  promptVersion: 'v2.0'   // 默认Prompt版本
});

// 查询单词
const result = await api.words.query('accountability', {
  includeLegacy: false
});

console.log(result.data.translation); // "问责制，问责性，负责程度"
```

### 10.2 Python SDK

```python
# pip install chaiword-duck-api
from chaiword_duck_api import ChaiWordDuckAPI

api = ChaiWordDuckAPI(
    base_url='https://api.chaiwordduck.com/v1',
    token='your-jwt-token',  # 可选
    language_code='zh_CN'
)

# 查询单词
result = api.words.query('accountability')
print(result.data['translation'])  # "问责制，问责性，负责程度"
```

### 10.3 cURL 示例

```bash
# 基础查询（游客模式）
curl -X GET "https://api.chaiwordduck.com/v1/words/query/accountability" \
  -H "Accept: application/json"

# 指定语言查询
curl -X GET "https://api.chaiwordduck.com/v1/words/query/accountability?language_code=zh_CN" \
  -H "Accept: application/json"

# 包含向后兼容字段
curl -X GET "https://api.chaiwordduck.com/v1/words/query/accountability?include_legacy=true" \
  -H "Accept: application/json"

# 认证用户查询
curl -X GET "https://api.chaiwordduck.com/v1/words/query/accountability" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Accept: application/json"

# 设置语言偏好
curl -X POST "https://api.chaiwordduck.com/v1/users/language-preference" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "language_code": "zh_CN",
    "prompt_version": "v2.0"
  }'
```

---

## 11. 版本变更历史

### v1.0 (2025-10-26) - 多语言支持版本

#### 新增功能
- ✅ **多语言Prompt系统**：支持10种语言的AI生成
- ✅ **混合存储策略**：简单字段VARCHAR，复杂结构JSONB
- ✅ **自动格式转换**：向后兼容处理
- ✅ **语言偏好设置**：用户可设置首选语言
- ✅ **多语言缓存**：按语言优化的缓存策略

#### API变更
- **新增字段**：
  - `translation`：单词翻译
  - `language_code`：语言代码
  - `prompt_version`：Prompt版本标识
  - `is_legacy_format`：格式标识

- **新增端点**：
  - `GET /languages/supported`：获取支持的语言列表
  - `POST /users/language-preference`：设置语言偏好
  - `POST /words/generate-multilang`：生成多语言内容

- **查询参数**：
  - `include_legacy`：是否包含向后兼容字段
  - `language_code`：指定首选语言

#### 向后兼容性
- ✅ **100%向后兼容**：现有API继续正常工作
- ✅ **渐进式迁移**：支持旧格式数据和新格式并存
- ✅ **可选升级**：客户端可选择何时使用新功能

#### 性能优化
- ✅ **JSONB索引**：优化复杂查询性能
- ✅ **多层缓存**：减少AI生成调用
- ✅ **预生成机制**：热门单词提前生成

#### 安全增强
- ✅ **多语言输入验证**：防止多语言环境下的注入攻击
- ✅ **语言权限控制**：某些语言需要特殊授权
- ✅ **内容审核**：多语言内容自动审核

---

## 12. 支持和联系方式

### 12.1 技术支持

- **文档网站**: https://docs.chaiwordduck.com
- **API状态页**: https://status.chaiwordduck.com
- **GitHub Issues**: https://github.com/cznccsjd/ChaiWordDuck/issues

### 12.2 商务合作

- **邮箱**: business@chaiwordduck.com
- **官网**: https://chaiwordduck.com

### 12.3 社区

- **开发者交流群**: [微信群二维码]
- **技术博客**: https://blog.chaiwordduck.com
- **GitHub**: https://github.com/cznccsjd/ChaiWordDuck

---

**文档版本**: v1.0
**最后更新**: 2025-10-26
**适用API版本**: v1.0+