'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui';
import { useToast } from '@/components/ui';
import { queryWord } from '@/lib/api/words';

interface SearchBoxProps {
  remainingQueries?: number;
  totalQueries?: number;
  isGuest?: boolean;
  onSearch?: () => void;
}

export function SearchBox({
  remainingQueries = 1,
  totalQueries = 1,
  isGuest = true,
  onSearch,
}: SearchBoxProps) {
  const router = useRouter();
  const { showToast } = useToast();
  const [word, setWord] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    // 验证输入
    const trimmedWord = word.trim().toLowerCase();
    if (!trimmedWord) {
      showToast('请输入单词', 'error');
      return;
    }

    // 只允许英文字母
    if (!/^[a-zA-Z]+$/.test(trimmedWord)) {
      showToast('请输入英文单词（仅支持字母）', 'error');
      return;
    }

    // 检查是否有剩余次数
    if (remainingQueries <= 0) {
      if (isGuest) {
        showToast('今日体验次数已用完，注册可获得3次/天', 'error');
        setTimeout(() => {
          router.push('/register');
        }, 1500);
      } else {
        showToast('今日查询次数已用完，明天再来或升级高级版', 'error');
      }
      return;
    }

    setIsSearching(true);
    try {
      // 调用API查询单词
      const wordData = await queryWord(trimmedWord);

      // 验证返回的数据包含有效的ID
      if (!wordData || !wordData.id) {
        throw new Error('API返回数据格式错误，缺少单词ID');
      }

      console.log('SearchBox: 查询成功，单词数据:', wordData);

      // 触发回调（用于刷新查询次数）
      onSearch?.();

      // 跳转到单词详情页
      console.log('SearchBox: 准备跳转到路由:', `/word/${wordData.id}`);
      router.push(`/word/${wordData.id}`);
    } catch (error) {
      console.error('SearchBox: 查询单词失败:', error);
      const errorMessage = error instanceof Error ? error.message : '查询失败，请稍后重试';
      showToast(errorMessage, 'error');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          value={word}
          onChange={(e) => setWord(e.target.value)}
          placeholder="输入要学习的单词..."
          disabled={isSearching}
          className="flex-1 px-4 py-3 sm:py-4 border-2 border-gray-200 rounded-lg focus:border-yellow-400 focus:outline-none transition-colors text-base sm:text-lg disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
        <Button
          type="submit"
          disabled={isSearching}
          size="lg"
          className="w-full sm:w-auto sm:px-8 min-h-[44px]"
        >
          {isSearching ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-2 h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              正在拆解...
            </span>
          ) : (
            '搜索'
          )}
        </Button>
      </form>

      {/* 查询次数提示 */}
      <div className="mt-4 text-center">
        {remainingQueries > 0 ? (
          <p className="text-sm text-gray-600">
            {isGuest ? (
              <>
                游客模式：今日剩余{' '}
                <span className="font-semibold text-yellow-600">
                  {remainingQueries}/{totalQueries}
                </span>{' '}
                次查询
              </>
            ) : (
              <>
                今日剩余{' '}
                <span className="font-semibold text-yellow-600">
                  {remainingQueries}/{totalQueries}
                </span>{' '}
                次查询
              </>
            )}
          </p>
        ) : (
          <p className="text-sm text-red-600 font-medium">
            {isGuest ? '今日体验次数已用完' : '今日查询次数已用完'}
          </p>
        )}
      </div>
    </div>
  );
}
