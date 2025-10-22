import { QueryClient } from '@tanstack/react-query';
import { handleApiError } from '@/lib/api/errorHandling';

// 创建QueryClient实例
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 数据 stale 时间：5分钟
      staleTime: 5 * 60 * 1000,
      // 缓存时间：10分钟
      gcTime: 10 * 60 * 1000,
      // 重试配置
      retry: (failureCount, error) => {
        // 4xx 错误不重试
        if (error && typeof error === 'object' && 'status' in error) {
          const status = (error as any).status;
          if (status >= 400 && status < 500) {
            return false;
          }
        }
        // 最多重试2次
        return failureCount < 2;
      },
      // 重试延迟
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // 网络状态变化时自动重新获取
      refetchOnWindowFocus: false,
      // 错误边界处理
      throwOnError: false,
    },
    mutations: {
      // 变更重试配置
      retry: 1,
      // 错误不抛出，由调用方处理
      throwOnError: false,
    },
  },
});

// React Query 错误处理工具函数
export function handleQueryError(error: unknown, showToast?: (message: string, type?: 'error' | 'success' | 'warning' | 'info') => void) {
  const errorMessage = handleApiError(error);
  console.error('Query Error:', error);

  if (showToast) {
    showToast(errorMessage, 'error');
  }

  return errorMessage;
}

// 查询键工厂
export const queryKeys = {
  // 用户相关
  user: ['user'] as const,
  auth: () => [...queryKeys.user, 'auth'] as const,

  // 单词相关
  words: ['words'] as const,
  word: (id: string) => [...queryKeys.words, id] as const,
  searchWords: (query: string) => [...queryKeys.words, 'search', query] as const,

  // 查询限制
  queryLimit: ['queryLimit'] as const,

  // 收藏相关
  favorites: ['favorites'] as const,

  // AI生成相关
  aiGeneration: ['aiGeneration'] as const,
} as const;

// 开发环境下的调试工具
export const queryConfig = {
  // 开发环境下开启日志
  enableLogging: process.env.NODE_ENV === 'development',

  // 日志函数
  logQueryData: (queryKey: unknown[], data: unknown) => {
    if (queryConfig.enableLogging) {
      console.log(`[Query Success] ${queryKey.join('/')}:`, data);
    }
  },

  logQueryError: (queryKey: unknown[], error: unknown) => {
    if (queryConfig.enableLogging) {
      console.error(`[Query Error] ${queryKey.join('/')}:`, error);
    }
  },
};