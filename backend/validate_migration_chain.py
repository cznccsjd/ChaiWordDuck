#!/usr/bin/env python3
"""
迁移链验证脚本

验证修复方案不会破坏现有的迁移历史和依赖关系
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import re

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[0]
sys.path.append(str(project_root))


class MigrationFile:
    """迁移文件类"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.filename = file_path.name
        self.content = file_path.read_text(encoding='utf-8')

        # 提取迁移信息
        self.revision_id = self._extract_revision_id()
        self.down_revision = self._extract_down_revision()
        self.description = self._extract_description()

    def _extract_revision_id(self) -> str:
        """提取revision ID"""
        match = re.search(r"revision:\s*str\s*=\s*['\"]([^'\"]+)['\"]", self.content)
        return match.group(1) if match else ""

    def _extract_down_revision(self) -> Optional[str]:
        """提取down_revision"""
        match = re.search(r"down_revision:\s*Union\[str,\s*None\]\s*=\s*['\"]([^'\"]*)['\"]", self.content)
        return match.group(1) if match and match.group(1) else None

    def _extract_description(self) -> str:
        """提取描述"""
        # 从文件名提取（去掉.py扩展名）
        desc = self.filename.replace('.py', '')

        # 从文件内容提取更详细的描述
        doc_match = re.search(r'\"\"\"([^\"\"\"].*?)\"\"\"', self.content, re.DOTALL)
        if doc_match:
            first_line = doc_match.group(1).split('\n')[0].strip()
            if first_line:
                desc = first_line

        return desc


class MigrationChainValidator:
    """迁移链验证器"""

    def __init__(self, versions_dir: Path):
        self.versions_dir = versions_dir
        self.migrations: Dict[str, MigrationFile] = {}
        self.load_migrations()

    def load_migrations(self):
        """加载所有迁移文件"""
        for py_file in self.versions_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            migration = MigrationFile(py_file)
            if migration.revision_id:
                self.migrations[migration.revision_id] = migration

    def validate_chain(self) -> List[Dict]:
        """验证迁移链的完整性"""
        issues = []

        # 1. 检查所有down_revision是否存在
        for rev_id, migration in self.migrations.items():
            if migration.down_revision and migration.down_revision not in self.migrations:
                issues.append({
                    'type': 'missing_down_revision',
                    'revision': rev_id,
                    'down_revision': migration.down_revision,
                    'message': f"迁移 {rev_id} 依赖的 {migration.down_revision} 不存在"
                })

        # 2. 检查重复的revision ID
        rev_ids = list(self.migrations.keys())
        duplicates = [x for x in rev_ids if rev_ids.count(x) > 1]
        if duplicates:
            issues.append({
                'type': 'duplicate_revision',
                'revisions': list(set(duplicates)),
                'message': f"发现重复的revision ID: {duplicates}"
            })

        # 3. 检查循环依赖
        if self._has_circular_dependency():
            issues.append({
                'type': 'circular_dependency',
                'message': "检测到循环依赖"
            })

        # 4. 检查分支点
        branch_points = self._find_branch_points()
        if branch_points:
            issues.append({
                'type': 'branch_points',
                'points': branch_points,
                'message': f"发现分支点: {branch_points}"
            })

        return issues

    def _has_circular_dependency(self) -> bool:
        """检查是否存在循环依赖"""
        visited = set()
        rec_stack = set()

        def has_cycle(rev_id: str) -> bool:
            if rev_id in rec_stack:
                return True
            if rev_id in visited:
                return False

            visited.add(rev_id)
            rec_stack.add(rev_id)

            migration = self.migrations.get(rev_id)
            if migration and migration.down_revision:
                if has_cycle(migration.down_revision):
                    return True

            rec_stack.remove(rev_id)
            return False

        for rev_id in self.migrations:
            if has_cycle(rev_id):
                return True

        return False

    def _find_branch_points(self) -> List[str]:
        """查找分支点（被多个迁移依赖的点）"""
        down_revision_counts = {}
        for migration in self.migrations.values():
            if migration.down_revision:
                down_revision_counts[migration.down_revision] = down_revision_counts.get(migration.down_revision, 0) + 1

        return [rev for rev, count in down_revision_counts.items() if count > 1]

    def get_main_chain(self) -> List[MigrationFile]:
        """获取主链（最长的依赖链）"""
        # 找到所有叶子节点（没有被任何迁移依赖的节点）
        leaf_nodes = []
        for rev_id, migration in self.migrations.items():
            is_leaf = True
            for other in self.migrations.values():
                if other.down_revision == rev_id:
                    is_leaf = False
                    break
            if is_leaf:
                leaf_nodes.append(rev_id)

        # 对每个叶子节点，追踪其完整链路
        chains = []
        for leaf in leaf_nodes:
            chain = []
            current = leaf
            while current:
                migration = self.migrations.get(current)
                if migration:
                    chain.append(migration)
                    current = migration.down_revision
                else:
                    break
            chains.append(chain)

        # 返回最长的链
        return max(chains, key=len) if chains else []

    def print_chain_info(self):
        """打印迁移链信息"""
        print("迁移链分析报告")
        print("=" * 60)

        # 基本信息
        print(f"迁移文件目录: {self.versions_dir}")
        print(f"迁移文件总数: {len(self.migrations)}")

        # 主链信息
        main_chain = self.get_main_chain()
        print(f"主链长度: {len(main_chain)}")

        # 验证结果
        issues = self.validate_chain()
        if not issues:
            print("迁移链完整性验证通过")
        else:
            print("发现迁移链问题:")
            for issue in issues:
                print(f"   - {issue['message']}")

        # 主链详情
        print(f"\n主链详情:")
        print("-" * 60)
        for i, migration in enumerate(reversed(main_chain)):
            status = "[MIG]"
            if migration.revision_id == "fix_alembic_version_length":
                status = "[FIX]"  # 修复迁移
            elif migration.revision_id == "006_add_word_language_unique_constraint":
                status = "[TGT]"  # 目标迁移

            print(f"{status} {migration.revision_id}")
            print(f"    描述: {migration.description}")
            if migration.down_revision:
                print(f"    依赖: {migration.down_revision}")
            print()

    def validate_fix_migration(self) -> bool:
        """验证修复迁移的正确性"""
        print("验证修复迁移...")

        # 检查修复迁移是否存在
        fix_migration = self.migrations.get("fix_alembic_version_length")
        if not fix_migration:
            print("修复迁移不存在")
            return False

        print(f"修复迁移存在: {fix_migration.revision_id}")

        # 检查修复迁移的依赖
        if fix_migration.down_revision != "005_add_multilang_prompt_support":
            print(f"修复迁移依赖不正确: {fix_migration.down_revision}")
            return False

        print(f"修复迁移依赖正确: {fix_migration.down_revision}")

        # 检查006迁移是否正确依赖修复迁移
        target_migration = self.migrations.get("006_add_word_language_unique_constraint")
        if not target_migration:
            print("006迁移不存在")
            return False

        if target_migration.down_revision != "fix_alembic_version_length":
            print(f"006迁移依赖不正确: {target_migration.down_revision}")
            return False

        print(f"006迁移依赖正确: {target_migration.down_revision}")

        # 检查主链是否包含修复迁移
        main_chain = self.get_main_chain()
        chain_revisions = [m.revision_id for m in main_chain]

        # 检查关键迁移是否在某个链中
        critical_migrations = [
            "005_add_multilang_prompt_support",
            "fix_alembic_version_length",
            "006_add_word_language_unique_constraint"
        ]

        for critical_rev in critical_migrations:
            if critical_rev not in chain_revisions:
                print(f"关键迁移缺失: {critical_rev}")
                return False

        print("主链完整性验证通过")
        return True


def main():
    """主函数"""
    print("迁移链验证工具")
    print("=" * 50)

    versions_dir = project_root / "alembic" / "versions"

    if not versions_dir.exists():
        print(f"❌ 迁移目录不存在: {versions_dir}")
        return

    validator = MigrationChainValidator(versions_dir)

    # 打印基本信息
    validator.print_chain_info()

    # 验证修复迁移
    is_valid = validator.validate_fix_migration()

    if is_valid:
        print("\n修复方案验证通过!")
        print("迁移链完整性良好")
        print("修复迁移依赖关系正确")
        print("不会破坏现有迁移历史")

        print(f"\n下一步操作:")
        print(f"   1. 运行: pdm run python fix_alembic_migration.py")
        print(f"   2. 或者手动执行: pdm run alembic upgrade fix_alembic_version_length")
        print(f"   3. 然后执行: pdm run alembic upgrade 006_add_word_language_unique_constraint")

    else:
        print("\n修复方案验证失败!")
        print("请检查迁移文件和依赖关系")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())