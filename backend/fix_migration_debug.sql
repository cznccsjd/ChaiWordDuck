-- ============================================
-- 数据库迁移问题诊断和修复脚本
-- ============================================

-- 1. 检查当前alembic版本
SELECT version_num, created_at
FROM alembic_version
ORDER BY created_at DESC;

-- 2. 检查words表上的所有索引
SELECT
    indexname as index_name,
    tablename as table_name,
    indexdef as index_definition
FROM pg_indexes
WHERE tablename = 'words'
    AND indexname LIKE '%language%'
ORDER BY indexname;

-- 3. 检查是否存在重复索引
SELECT
    indexname as index_name,
    tablename as table_name,
    indexdef as index_definition,
    schemaname as schema_name
FROM pg_indexes
WHERE tablename = 'words'
    AND indexname = 'idx_words_language_code'
ORDER BY indexname;

-- 4. 检查words表结构
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'words'
    AND table_schema = 'public'
ORDER BY ordinal_position;

-- 5. 检查约束
SELECT
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint
WHERE conrelid = 'words'::regclass
ORDER BY conname;

-- 6. 如果idx_words_language_code重复存在，可以使用以下命令删除重复索引
-- 注意：谨慎执行，确保不会破坏现有依赖关系
-- DROP INDEX IF EXISTS idx_words_language_code;

-- 7. 修复完成后，重新创建索引（如果需要）
-- CREATE INDEX idx_words_language_code ON words (language_code);

-- 8. 检查迁移历史依赖关系
SELECT
    av.version_num,
    av.created_at,
    CASE
        WHEN av.version_num = '005_add_multilang_prompt_support' THEN 'Creates idx_words_language_code'
        WHEN av.version_num = '006_add_word_language_unique_constraint' THEN 'Attempts to create idx_words_language_code again'
        ELSE 'Other migration'
    END as description
FROM alembic_version av
ORDER BY av.created_at;

-- ============================================
-- 使用说明
-- ============================================
/*
1. 首先运行查询1-5来了解当前数据库状态
2. 如果发现重复索引，运行查询6删除重复的索引
3. 重新运行alembic迁移命令
4. 如果仍有问题，可能需要手动设置alembic版本
5. 备份数据库后再执行任何修改操作

命令示例：
- 检查当前版本：alembic current
- 查看迁移历史：alembic history
- 标记迁移为完成：alembic stamp <revision_id>
- 重新运行迁移：alembic upgrade head
*/