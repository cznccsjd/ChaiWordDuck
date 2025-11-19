# 单词数据更新策略设计

## 🎯 问题分析

当前系统只有INSERT操作，缺少UPDATE操作，导致：
- 同一单词可能存在多个语言版本的重复记录
- 存储空间浪费
- 数据管理复杂化

## 🔧 解决方案

### 1. 核心设计原则

**智能更新策略 (Smart Upsert Logic)**
```
当查询单词时：
├── 词库中存在该单词？
│   ├── 是 → 检查是否需要更新/补充
│   │   ├── 需要新语言版本？ → 更新现有记录
│   │   ├── 数据格式过时？ → 迁移到新格式
│   │   └── 数据完整？ → 直接返回
│   └── 否 → AI生成新记录
└── 返回结果
```

### 2. 具体实现策略

#### A. 主键策略调整
```sql
-- 当前：单词作为唯一键
ALTER TABLE words ADD CONSTRAINT uk_words_word UNIQUE (word);

-- 建议：复合唯一键 (单词 + 语言)
ALTER TABLE words DROP CONSTRAINT uk_words_word;
ALTER TABLE words ADD CONSTRAINT uk_words_word_lang UNIQUE (word, language_code);
```

#### B. Upsert操作逻辑
```python
async def upsert_word_with_language(
    db: AsyncSession,
    word_data: dict,
    language_code: str = "zh_CN"
) -> Word:
    """
    智能插入或更新单词数据

    策略：
    1. 尝试查找 (word, language_code) 组合
    2. 存在 → 比较并更新缺失/过时字段
    3. 不存在 → 创建新记录
    """

    # 1. 查找现有记录
    existing = await db.execute(
        select(Word)
        .where(Word.word == word_data["word"])
        .where(Word.language_code == language_code)
    )
    existing_word = existing.scalar_one_or_none()

    if existing_word:
        # 2. 更新策略：合并新旧数据
        updated = False

        # 检查新格式字段
        if not existing_word.core_game_new and word_data.get("core_game_new"):
            existing_word.core_game_new = word_data["core_game_new"]
            updated = True

        if not existing_word.game_boards and word_data.get("game_boards"):
            existing_word.game_boards = word_data["game_boards"]
            updated = True

        # 更新时间戳
        if updated:
            existing_word.updated_at = datetime.utcnow()
            existing_word.prompt_version = word_data.get("prompt_version", "v1.0")

        await db.commit()
        await db.refresh(existing_word)
        return existing_word
    else:
        # 3. 创建新记录
        word_record = Word(**word_data, language_code=language_code)
        db.add(word_record)
        await db.commit()
        await db.refresh(word_record)
        return word_record
```

#### C. 查询逻辑优化
```python
async def query_word_with_fallback(
    db: AsyncSession,
    word_text: str,
    preferred_language: str = "zh_CN"
) -> Optional[Word]:
    """
    智能单词查询，支持语言降级

    优先级：
    1. 指定语言的单词
    2. 英文原版单词
    3. 任何可用的版本
    """

    # 1. 首选：指定语言
    result = await db.execute(
        select(Word)
        .where(Word.word == word_text)
        .where(Word.language_code == preferred_language)
        .order_by(Word.is_golden.desc())
    )
    word = result.scalar_one_or_none()

    if word:
        return word

    # 2. 备选：英文原版
    result = await db.execute(
        select(Word)
        .where(Word.word == word_text)
        .where(Word.language_code == "en")
        .order_by(Word.is_golden.desc())
    )
    word = result.scalar_one_or_none()

    if word:
        return word

    # 3. 兜底：任何可用版本
    result = await db.execute(
        select(Word)
        .where(Word.word == word_text)
        .order_by(Word.is_golden.desc(), Word.language_code.asc())
    )
    word = result.scalar_one_or_none()

    return word
```

### 3. 数据库迁移脚本

```sql
-- Migration: 006_add_word_language_unique_constraint.py

-- 1. 清理重复数据（保留最新的记录）
WITH ranked_words AS (
    SELECT
        id,
        word,
        language_code,
        ROW_NUMBER() OVER (
            PARTITION BY word, language_code
            ORDER BY updated_at DESC, id DESC
        ) as rn
    FROM words
),
duplicates_to_delete AS (
    SELECT id FROM ranked_words WHERE rn > 1
)
DELETE FROM words WHERE id IN (SELECT id FROM duplicates_to_delete);

-- 2. 删除旧的单词唯一约束
ALTER TABLE words DROP CONSTRAINT IF EXISTS uk_words_word;

-- 3. 添加新的复合唯一约束
ALTER TABLE words
ADD CONSTRAINT uk_words_word_lang
UNIQUE (word, language_code);

-- 4. 添加索引优化查询性能
CREATE INDEX CONCURRENTLY idx_words_word_lang
ON words (word, language_code);

-- 5. 为查询优化添加部分索引
CREATE INDEX CONCURRENTLY idx_words_golden_by_word_lang
ON words (word, language_code)
WHERE is_golden = true;
```

### 4. API层改进

#### A. 修改查询单词逻辑
```python
# 在 words.py 中
async def query_word_internal(
    word_text: str,
    current_user: Optional[User],
    db: AsyncSession,
    request: Optional[Request] = None,
    language: Optional[str] = None,
) -> WordQueryResponse:

    # ... 现有验证逻辑 ...

    # 使用新的查询函数
    word = await query_word_with_fallback(
        db, normalized_word, effective_language
    )

    if word:
        # 检查是否需要数据更新
        if should_update_word_data(word, effective_language):
            word = await update_word_data_if_needed(
                db, word, effective_language
            )

        # ... 返回响应 ...

    # ... AI生成逻辑 ...
```

#### B. 添加数据版本检查
```python
def should_update_word_data(word: Word, preferred_language: str) -> bool:
    """
    检查是否需要更新单词数据
    """
    # 1. 语言不匹配
    if word.language_code != preferred_language:
        return True

    # 2. 数据格式过时
    if word.is_legacy_format:
        return True

    # 3. 新格式字段缺失
    if not word.core_game_new or not word.game_boards:
        return True

    return False
```

### 5. 优势分析

#### ✅ **存储优化**
- 避免重复数据存储
- 一单词多语言版本集中管理
- 减少存储空间浪费

#### ✅ **查询性能**
- 明确的查询索引策略
- 语言降级机制提高命中率
- 减少无效查询

#### ✅ **数据一致性**
- 单一数据源
- 版本控制明确
- 更新逻辑可追溯

#### ✅ **向后兼容**
- 现有数据平滑迁移
- API接口保持不变
- 渐进式升级

### 6. 实施计划

#### Phase 1: 数据库迁移
1. 执行数据清理
2. 添加复合唯一约束
3. 创建优化索引

#### Phase 2: 代码更新
1. 实现upsert服务函数
2. 更新查询逻辑
3. 添加数据更新检查

#### Phase 3: 测试验证
1. 单元测试覆盖
2. 集成测试验证
3. 性能基准测试

### 7. 风险评估

#### 🔴 **高风险**
- 数据库迁移可能导致数据丢失
- 需要充分的数据备份

#### 🟡 **中风险**
- 查询逻辑变更可能影响现有API
- 需要完整的回归测试

#### 🟢 **低风险**
- 新增upsert逻辑对现有功能影响最小

## 🚀 下一步行动

1. **立即**: 创建数据库迁移脚本
2. **短期**: 实现upsert服务函数
3. **中期**: 更新API查询逻辑
4. **长期**: 优化查询性能和缓存策略

这个设计解决了当前系统只有INSERT没有UPDATE的问题，同时保持了向后兼容性和性能优化。