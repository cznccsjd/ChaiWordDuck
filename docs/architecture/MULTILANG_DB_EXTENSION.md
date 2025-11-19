# 多语言Prompt系统数据库扩展方案

## 概述

本扩展方案为words表添加了对多语言Prompt管理系统的支持，采用混合存储策略，既支持结构化数据存储，又保持向后兼容性。

## 设计目标

1. **支持多语言**: 支持英语、中文、日语等多种语言的单词数据
2. **向后兼容**: 现有功能和API不受影响
3. **渐进迁移**: 支持旧格式数据逐步迁移到新格式
4. **性能优化**: 通过合理的索引设计保证查询性能
5. **数据完整性**: 确保新旧格式数据的一致性和完整性

## 架构设计

### 混合存储策略

#### 简单字段（VARCHAR/TEXT）
- `word`: 单词本身
- `phonetic`: 国际音标
- `translation`: 翻译文本
- `part_of_speech`: 词性
- `language_code`: 语言代码
- `prompt_version`: Prompt版本
- `is_legacy_format`: 格式标记

#### 结构化字段（JSONB）
- `core_game_new`: 核心游戏数据
- `game_boards`: 游戏棋盘数据
- `etymology_new`: 词源数据
- `common_mistakes_new`: 常见错误数据

#### 兼容性字段（保留）
- 所有原有字段继续保留，确保现有代码正常运行

## 数据结构

### 新格式数据结构（来自Prompt模板）

```json
{
  "word": "accommodation",
  "phonetic": "/əˌkɒməˈdeɪʃən/",
  "translation": "住宿，调适",
  "part_of_speech": "noun",
  "language_code": "zh_CN",
  "core_game": {
    "content": "核心游戏描述"
  },
  "game_boards": {
    "board_a_speculative": {
      "type": "棋盘A (思辨场)",
      "name": "场景名",
      "example": "示例"
    },
    "board_b_life": {
      "type": "棋盘B (生活场)",
      "name": "场景名",
      "example": "示例"
    }
  },
  "etymology": {
    "breakdown": {
      "prefix": {"part": "ac-", "meaning": "to, toward"},
      "root": {"part": "commod", "meaning": "convenient"},
      "suffix": {"part": "ation", "meaning": "action"}
    },
    "story": "组装故事"
  },
  "common_mistakes": {
    "warning": "常见错误",
    "avoidance": "避免方法"
  },
  "memory_trick": "记忆技巧",
  "prompt_version": "v2.0"
}
```

## 实现文件

### 1. 数据库迁移脚本
- `alembic/versions/005_add_multilang_prompt_support.py`
  - 添加新字段和JSONB支持
  - 创建必要的索引和约束
  - 执行初始数据迁移

### 2. 数据模型
- `app/models/word.py`
  - 扩展Word模型以支持新字段
  - 添加向后兼容方法
  - 实现数据访问和转换逻辑

### 3. 数据转换器
- `app/models/word_converter.py`
  - 新旧格式数据转换
  - AI响应数据映射
  - 数据验证和错误处理

### 4. 迁移服务
- `app/services/word_migration_service.py`
  - 批量数据迁移
  - 迁移进度跟踪
  - 数据完整性验证

### 5. 管理工具
- `migrate_words.py`
  - 命令行迁移工具
  - 统计信息查看
  - 迁移验证

### 6. 测试脚本
- `test_word_multilang_migration.py`
  - 完整的测试覆盖
  - 功能验证
  - 兼容性测试

## 使用方法

### 1. 执行数据库迁移

```bash
# 运行Alembic迁移
pdm run alembic upgrade head

# 或者使用迁移工具
pdm run python migrate_words.py migrate --batch-size 50
```

### 2. 批量迁移数据

```bash
# 迁移所有单词
pdm run python migrate_words.py migrate

# 只迁移黄金手册单词
pdm run python migrate_words.py migrate --golden-only

# 迁移指定单词
pdm run python migrate_words.py migrate --word accommodation

# 批量迁移（自定义批次大小）
pdm run python migrate_words.py migrate --batch-size 100 --max-batches 10
```

### 3. 验证迁移结果

```bash
# 验证数据完整性
pdm run python migrate_words.py validate

# 查看统计信息
pdm run python migrate_words.py stats

# 估算迁移时间
pdm run python migrate_words.py estimate
```

### 4. 回滚迁移

```bash
# 回滚指定单词
pdm run python migrate_words.py rollback accommodation
```

### 5. 运行测试

```bash
# 运行完整测试套件
pdm run python test_word_multilang_migration.py

# 或使用pytest
pdm run pytest tests/test_word_multilang_migration.py
```

## 性能优化

### 索引设计

#### 常规索引
- `idx_words_language_code`: 语言代码查询
- `idx_words_prompt_version`: 版本查询
- `idx_words_is_legacy_format`: 格式筛选

#### GIN索引（JSONB）
- `idx_words_core_game_new_gin`: 核心游戏内容搜索
- `idx_words_game_boards_gin`: 游戏棋盘搜索
- `idx_words_etymology_new_gin`: 词源内容搜索
- `idx_words_common_mistakes_new_gin`: 错误内容搜索

### 查询优化

```sql
-- 查询指定语言的单词（使用语言索引）
SELECT * FROM words WHERE language_code = 'zh_CN';

-- JSONB内容查询（使用GIN索引）
SELECT * FROM words WHERE core_game_new @@ '"content" : "游戏"';

-- 混合查询（旧格式兼容）
SELECT * FROM words
WHERE (is_legacy_format = false AND language_code = 'zh_CN')
   OR (is_legacy_format = true);
```

## 向后兼容性

### API层兼容
- 现有API端点继续正常工作
- 自动检测数据格式并返回兼容响应
- 支持新旧格式数据的混合查询

### 数据访问兼容
- Word模型提供兼容性方法：
  - `get_core_game_content()`: 获取核心游戏内容
  - `get_game_boards_data()`: 获取游戏棋盘数据
  - `get_etymology_data()`: 获取词源数据
  - `get_common_mistakes_data()`: 获取常见错误数据

### 字段映射
```python
# 新格式
word.core_game_new['content']

# 旧格式（兼容）
word.get_core_game_content()  # 自动选择正确格式
```

## 支持的语言

目前支持以下语言：
- `en`: English
- `zh_CN`: 简体中文
- `zh_TW`: 繁體中文
- `ja`: 日本語
- `ko`: 한국어
- `fr`: Français
- `de`: Deutsch
- `es`: Español
- `it`: Italiano
- `ru`: Русский

## 数据迁移策略

### 阶段1: Schema扩展
- 添加新字段
- 创建索引
- 保持现有字段不变

### 阶段2: 数据转换
- 自动转换旧格式数据
- 保留原始字段作为备份
- 设置格式标记

### 阶段3: 渐进迁移
- 分批处理数据
- 实时监控进度
- 支持回滚机制

### 阶段4: 完全迁移（可选）
- 清理旧字段（谨慎操作）
- 优化存储空间
- 更新应用逻辑

## 监控和维护

### 迁移监控
```python
# 获取迁移统计
stats = migration_service.get_migration_stats()
print(f"迁移进度: {stats['migration_progress']}")

# 验证数据完整性
validation = migration_service.validate_migration_integrity()
print(f"发现问题: {len(validation['issues_found'])}")
```

### 性能监控
- 监控JSONB字段大小
- 跟踪查询性能变化
- 定期维护索引

## 注意事项

1. **数据库版本**: 需要PostgreSQL 9.4+（支持JSONB）
2. **备份**: 执行迁移前请备份数据库
3. **测试**: 先在测试环境验证迁移效果
4. **回滚**: 准备好回滚计划
5. **监控**: 迁移过程中密切监控系统性能

## 故障排除

### 常见问题

1. **迁移失败**
   - 检查数据库连接
   - 确认Alembic状态
   - 查看错误日志

2. **性能问题**
   - 检查索引是否创建
   - 分析查询计划
   - 考虑批次大小调整

3. **数据不一致**
   - 运行验证脚本
   - 检查转换逻辑
   - 必要时重新迁移

### 日志位置
- 应用日志: `logs/app.log`
- 迁移日志: `logs/migration.log`
- 数据库日志: PostgreSQL日志文件

## 未来扩展

### 可能的改进
1. **全文搜索**: 集成PostgreSQL全文搜索功能
2. **缓存层**: 添加Redis缓存提高查询性能
3. **分表策略**: 大数据量时考虑按语言分表
4. **版本管理**: 更精细的数据版本控制

### 新功能
1. **多语言关联**: 同一单词的多语言版本关联
2. **用户偏好**: 基于用户语言的个性化推荐
3. **统计分析**: 多语言数据使用情况分析
4. **质量评估**: 自动评估翻译和数据质量