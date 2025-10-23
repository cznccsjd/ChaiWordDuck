import { useApiQuery, useApiMutation } from '@/lib/react-query/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/react-query';
import { queryWord, getWordById } from '@/lib/api/words';
import type { WordManual } from '@/types';

// 查询单词的hook
export function useWordQuery(word: string, enabled?: boolean) {
  return useApiQuery(
    queryKeys.searchWords(word),
    () => queryWord(word),
    {
      enabled: enabled && Boolean(word.trim()),
      staleTime: 10 * 60 * 1000, // 10分钟
      gcTime: 30 * 60 * 1000, // 30分钟缓存
    }
  );
}

// 通过ID获取单词详情的hook
export function useWordById(wordId: number, enabled?: boolean) {
  return useApiQuery(
    queryKeys.word(wordId.toString()),
    () => getWordById(wordId),
    {
      enabled: enabled && Boolean(wordId),
      staleTime: 15 * 60 * 1000, // 15分钟
      gcTime: 60 * 60 * 1000, // 1小时缓存
    }
  );
}

// 预加载单词的hook
export function usePrefetchWord() {
  const queryClient = useQueryClient();

  return function prefetch(word: string) {
    return queryClient.prefetchQuery({
      queryKey: queryKeys.searchWords(word),
      queryFn: () => queryWord(word),
      staleTime: 10 * 60 * 1000, // 10分钟
    });
  };
}

// 变更单词相关操作的hook（用于收藏、取消收藏等）
export function useWordMutation<TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<unknown>,
  options?: {
    showToast?: {
      success?: string;
      error?: string;
    };
  }
) {
  return useApiMutation(mutationFn, {
    showToast: options?.showToast,
    invalidateQueries: [
      [queryKeys.favorites[0]],
    ],
  });
}