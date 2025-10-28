# Alembic迁移修复指南

## 问题描述

在执行Alembic迁移时遇到以下错误：

```
sqlalchemy.exc.DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.StringDataRightTruncationError'>: value too long for type character varying(32)
[SQL: UPDATE alembic_version SET version_num='006_add_word_language_unique_constraint' WHERE alembic_version.version_num = '005_add_multilang_prompt_support']
```

**根本原因**：
- 版本号 `006_add_word_language_unique_constraint` 长度为38个字符
- 数据库中 `alembic_version.version_num` 字段限制为32个字符
- 需要扩展字段长度以支持更长的描述性版本号

## 修复方案

### 方案概述

采用**数据库结构修改**方案，将 `alembic_version.version_num` 字段从 `VARCHAR(32)` 扩展到 `VARCHAR(64)`。

**优势**：
- ✅ 保持现有版本号不变，避免重写迁移历史
- ✅ 一次性解决问题，防止未来类似问题
- ✅ 对业务数据无影响
- ✅ 完全兼容Alembic机制

### 修复文件

1. **修复迁移文件**: `backend/alembic/versions/fix_alembic_version_length.py`
   - 扩展版本号字段长度
   - 包含安全检查和回滚机制

2. **更新依赖关系**: 修改了 `006_add_word_language_unique_constraint.py`
   - 现在依赖于 `fix_alembic_version_length`
   - 确保修复迁移先执行

3. **自动化脚本**: `backend/fix_alembic_migration.py`
   - 检查数据库状态
   - 自动执行修复流程
   - 提供详细的执行反馈

## 使用方法

### 方法一：自动化修复（推荐）

```bash
cd backend
pdm run python fix_alembic_migration.py
```

脚本会自动：
1. 检查数据库连接
2. 检查当前版本和字段长度
3. 根据状态判断是否需要修复
4. 执行相应的修复步骤

### 方法二：手动执行

如果需要手动控制修复过程：

```bash
# 1. 检查当前状态
pdm run alembic current

# 2. 应用修复迁移
pdm run alembic upgrade fix_alembic_version_length

# 3. 应用006迁移
pdm run alembic upgrade 006_add_word_language_unique_constraint

# 4. 验证最终状态
pdm run alembic current
```

## 执行步骤详解

### 步骤1：检查当前状态

```bash
pdm run alembic current
```

预期输出：
```
005_add_multilang_prompt_support
```

### 步骤2：应用修复迁移

```bash
pdm run alembic upgrade fix_alembic_version_length
```

此步骤会：
- 检查当前版本是否为 `005_add_multilang_prompt_support`
- 将 `alembic_version.version_num` 字段从 `VARCHAR(32)` 扩展到 `VARCHAR(64)`
- 添加表注释说明

### 步骤3：应用目标迁移

```bash
pdm run alembic upgrade 006_add_word_language_unique_constraint
```

此步骤会：
- 执行原有的006迁移逻辑
- 添加单词和语言代码的唯一约束
- 创建相关索引

### 步骤4：验证结果

```bash
pdm run alembic current
```

预期输出：
```
006_add_word_language_unique_constraint
```

## 安全机制

### 1. 版本检查
修复迁移会在执行前检查当前版本，确保只在正确的状态下执行：

```python
if version_check == '005_add_multilang_prompt_support':
    # 执行修复
else:
    raise Exception(f"Cannot apply fix: current database version is {version_check}")
```

### 2. 回滚支持
每个迁移都包含完整的 downgrade 方法：

```python
def downgrade() -> None:
    """Revert alembic_version.version_num field back to VARCHAR(32)"""
    # 回滚逻辑
```

### 3. 字段长度检查
修复前会检查当前字段长度，避免重复修复：

```python
if current_length and current_length < 64:
    # 执行修复
else:
    print("ℹ️  alembic_version.version_num is already extended")
```

## 验证方法

### 1. 检查迁移历史

```bash
pdm run alembic history
```

应该看到完整的迁移链，包括新的修复迁移。

### 2. 检查数据库结构

```sql
SELECT
    column_name,
    character_maximum_length,
    data_type
FROM information_schema.columns
WHERE table_name = 'alembic_version'
AND column_name = 'version_num';
```

输出应该显示：
```
version_num | 64 | character varying
```

### 3. 检查当前版本

```sql
SELECT version_num FROM alembic_version;
```

输出应该显示：
```
006_add_word_language_unique_constraint
```

## 预防措施

为防止未来出现类似问题，建议：

### 1. 版本号命名规范

- 保持版本号在64字符以内
- 使用简洁但描述性的命名
- 格式：`序号_简短描述`

### 2. 数据库初始化脚本

在新数据库初始化时，可以考虑直接创建扩展长度的 `alembic_version` 表：

```sql
CREATE TABLE alembic_version (
    version_num VARCHAR(64) NOT NULL PRIMARY KEY
);
```

### 3. 开发流程检查

在创建新迁移时，检查版本号长度：

```bash
# 创建迁移后检查版本号长度
ls -la alembic/versions/*.py | head -n 1
```

## 故障排除

### 问题1：数据库连接失败

**错误**: `ConnectionRefusedError`

**解决方案**：
1. 检查数据库服务是否运行
2. 验证环境变量中的数据库URL
3. 确认网络连接和防火墙设置

### 问题2：版本不匹配

**错误**: `Cannot apply fix: current database version is xxx`

**解决方案**：
1. 检查当前数据库版本：`pdm run alembic current`
2. 根据实际情况选择合适的修复路径
3. 如需要，可以回滚到之前的稳定版本

### 问题3：迁移执行失败

**错误**: `sqlalchemy.exc.IntegrityError` 或其他数据库错误

**解决方案**：
1. 检查数据库状态和约束
2. 查看详细错误日志
3. 如需要，可以执行回滚：`pdm run alembic downgrade <previous_version>`

## 联系支持

如果在修复过程中遇到问题，请提供以下信息：

1. 完整的错误日志
2. 当前数据库版本：`pdm run alembic current`
3. 数据库连接配置（隐藏敏感信息）
4. 执行的具体命令和输出

---

**修复完成标志**：
- ✅ `pdm run alembic current` 显示 `006_add_word_language_unique_constraint`
- ✅ 数据库中 `alembic_version.version_num` 字段长度为64
- ✅ 所有相关约束和索引已创建
- ✅ 应用程序可以正常运行，无数据库相关错误