#!/usr/bin/env python3
"""
专门修复hello单词Unicode问题的脚本
"""

import asyncio
import re
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

from app.core.config import settings
from app.core.logging import get_logger
from app.models.word import Word

logger = get_logger(__name__)

async def fix_hello_word():
    """修复hello单词的Unicode问题"""

    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 查找hello单词
        result = await session.execute(select(Word).where(Word.word == 'hello'))
        word = result.scalar_one_or_none()

        if not word:
            print("Hello word not found in database")
            return

        print(f"Found hello word: ID {word.id}")

        # 清理函数
        def clean_unicode(text):
            if not text:
                return text
            # 移除所有无效的代理对字符
            return re.sub(r'[\udc80-\udfff]', '', text)

        # 准备更新数据
        update_data = {}
        fields_to_clean = [
            'phonetic', 'part_of_speech', 'core_game', 'scenario_formal',
            'scenario_casual', 'etymology_breakdown', 'etymology_story',
            'common_mistakes', 'memory_trick'
        ]

        for field in fields_to_clean:
            original_value = getattr(word, field, None)
            if original_value:
                cleaned_value = clean_unicode(original_value)
                if cleaned_value != original_value:
                    update_data[field] = cleaned_value
                    print(f"Field {field} will be updated")
                    print(f"  Original: {repr(original_value[:50])}")
                    print(f"  Cleaned:  {repr(cleaned_value[:50])}")

        if update_data:
            # 执行更新
            await session.execute(
                update(Word)
                .where(Word.id == word.id)
                .values(**update_data)
            )
            await session.commit()
            print(f"Successfully updated hello word with {len(update_data)} fields")
        else:
            print("No fields need to be updated")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_hello_word())