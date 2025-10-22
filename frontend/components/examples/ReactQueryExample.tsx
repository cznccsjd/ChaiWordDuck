'use client';

import { useState } from 'react';
import { useWordQuery, useWordById } from '@/lib/hooks/useWordQuery';
import { useQueryLimitReactQuery } from '@/lib/hooks/useQueryLimitReactQuery';
import { Button } from '@/components/ui';
import { Input } from '@/components/ui';

/**
 * React Query使用示例组件
 * 展示如何使用新的React Query hooks进行API调用
 */
export function ReactQueryExample() {
  const [searchWord, setSearchWord] = useState('');
  const [wordId, setWordId] = useState('');

  // 使用React Query查询单词
  const {
    data: wordData,
    isLoading: isWordLoading,
    error: wordError,
  } = useWordQuery(searchWord, searchWord.length > 0);

  // 使用React Query通过ID获取单词
  const {
    data: wordByIdData,
    isLoading: isWordByIdLoading,
    error: wordByIdError,
  } = useWordById(Number(wordId), Boolean(wordId) && !isNaN(Number(wordId)));

  // 使用React Query版本的查询限制hook
  const {
    remaining,
    total,
    is_guest: isGuest,
    isLoading: isLimitLoading,
    hasQueriedWord,
    recordQuery,
    refresh,
  } = useQueryLimitReactQuery();

  const handleSearch = () => {
    if (searchWord.trim()) {
      recordQuery(searchWord.trim());
    }
  };

  const handleSearchById = () => {
    // ID查询不需要记录查询次数，因为是通过ID获取
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          React Query 使用示例
        </h1>
        <p className="text-gray-600">
          展示如何使用React Query进行数据获取和状态管理
        </p>
      </div>

      {/* 查询限制信息 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-blue-800 mb-2">
          查询限制信息（使用React Query版本）
        </h2>
        <div className="space-y-1">
          <p className="text-blue-700">
            {isLimitLoading ? (
              '加载中...'
            ) : (
              <>
                剩余查询次数：<span className="font-bold">{remaining}</span> / {total}
                {isGuest && '（游客用户）'}
              </>
            )}
          </p>
          <Button
            onClick={refresh}
            variant="outline"
            size="sm"
            disabled={isLimitLoading}
          >
            刷新限制
          </Button>
        </div>
      </div>

      {/* 通过单词名称查询 */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          通过单词名称查询
        </h2>
        <div className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={searchWord}
              onChange={(e) => setSearchWord(e.target.value)}
              placeholder="输入要查询的单词..."
              className="flex-1"
            />
            <Button
              onClick={handleSearch}
              disabled={!searchWord.trim() || isWordLoading || remaining <= 0}
            >
              {isWordLoading ? '查询中...' : '查询'}
            </Button>
          </div>

          {searchWord && hasQueriedWord(searchWord) && (
            <p className="text-sm text-gray-500">
              这个单词你已经查询过了，不会消耗次数
            </p>
          )}

          {wordError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded">
              查询失败：{wordError.message}
            </div>
          )}

          {wordData && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">查询结果：</h3>
              <div className="space-y-2 text-sm">
                <p><strong>单词：</strong>{wordData.word}</p>
                <p><strong>音标：</strong>{wordData.phonetic || '无'}</p>
                <p><strong>词性：</strong>{wordData.part_of_speech || '无'}</p>
                <p><strong>核心游戏：</strong>{wordData.core_game}</p>
                <p><strong>正式场景：</strong>{wordData.scene_formal}</p>
                <p><strong>日常场景：</strong>{wordData.scene_daily}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 通过ID查询 */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          通过单词ID查询
        </h2>
        <div className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={wordId}
              onChange={(e) => setWordId(e.target.value)}
              placeholder="输入单词ID..."
              className="flex-1"
              type="number"
            />
            <Button
              onClick={handleSearchById}
              disabled={!wordId || isWordByIdLoading}
            >
              {isWordByIdLoading ? '查询中...' : '查询'}
            </Button>
          </div>

          {wordByIdError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded">
              查询失败：{wordByIdError.message}
            </div>
          )}

          {wordByIdData && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">查询结果：</h3>
              <div className="space-y-2 text-sm">
                <p><strong>ID：</strong>{wordByIdData.id}</p>
                <p><strong>单词：</strong>{wordByIdData.word}</p>
                <p><strong>音标：</strong>{wordByIdData.phonetic || '无'}</p>
                <p><strong>词性：</strong>{wordByIdData.part_of_speech || '无'}</p>
                <p><strong>记忆技巧：</strong>{wordByIdData.memory_trick}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* React Query Devtools 提示 */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="font-semibold text-yellow-800 mb-2">
          💡 开发工具提示
        </h3>
        <p className="text-yellow-700 text-sm">
          在开发环境下，你可以通过页面右下角的React Query Devtools查看查询状态、
          缓存数据和API请求详情。
        </p>
      </div>
    </div>
  );
}