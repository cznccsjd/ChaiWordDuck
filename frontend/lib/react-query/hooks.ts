import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { handleQueryError, queryKeys } from './index';
import { useToast } from '@/components/ui/Toast';

// 通用查询hook
export function useApiQuery<TData, TError = unknown>(
  queryKey: readonly unknown[],
  queryFn: () => Promise<TData>,
  options?: {
    enabled?: boolean;
    onSuccess?: (data: TData) => void;
    onError?: (error: TError) => void;
    [key: string]: any;
  }
) {
  const { showToast } = useToast();

  return useQuery({
    queryKey,
    queryFn,
    onError: (error: TError) => {
      const errorMessage = handleQueryError(error, showToast);
      options?.onError?.(error);
    },
    onSuccess: options?.onSuccess,
    enabled: options?.enabled ?? true,
    ...options,
  });
}

// 通用变更hook
export function useApiMutation<TData, TVariables, TError = unknown>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: TError, variables: TVariables) => void;
    invalidateQueries?: readonly unknown[][];
    showToast?: {
      success?: string;
      error?: string;
    };
    [key: string]: any;
  }
) {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: (data, variables) => {
      // 显示成功提示
      if (options?.showToast?.success) {
        showToast(options.showToast.success, 'success');
      }

      // 使相关查询失效
      if (options?.invalidateQueries) {
        options.invalidateQueries.forEach(queryKey => {
          queryClient.invalidateQueries({ queryKey });
        });
      }

      options?.onSuccess?.(data, variables);
    },
    onError: (error: TError, variables) => {
      // 处理错误提示
      if (options?.showToast?.error) {
        showToast(options.showToast.error, 'error');
      } else {
        // 使用默认错误处理
        handleQueryError(error, showToast);
      }

      options?.onError?.(error, variables);
    },
    ...options,
  });
}

// 乐观更新工具函数
export function useOptimisticMutation<TData, TVariables, TError = unknown>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options: {
    queryKey: readonly unknown[];
    updateFn: (oldData: unknown, variables: TVariables) => unknown;
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: TError, variables: TVariables) => void;
    showToast?: {
      success?: string;
      error?: string;
    };
  }
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onMutate: async (variables: TVariables) => {
      // 取消正在进行的查询
      await queryClient.cancelQueries({ queryKey: options.queryKey });

      // 保存之前的数据
      const previousData = queryClient.getQueryData(options.queryKey);

      // 乐观更新
      queryClient.setQueryData(options.queryKey, (old: unknown) =>
        options.updateFn(old, variables)
      );

      return { previousData };
    },
    onError: (error: TError, variables: TVariables, context: any) => {
      // 回滚乐观更新
      if (context?.previousData) {
        queryClient.setQueryData(options.queryKey, context.previousData);
      }

      // 调用原始错误处理
      options.onError?.(error, variables);
    },
    onSettled: () => {
      // 无论成功失败都重新获取数据
      queryClient.invalidateQueries({ queryKey: options.queryKey });
    },
    onSuccess: options.onSuccess,
  });
}

// 预加载hook
export function usePrefetchQuery() {
  const queryClient = useQueryClient();

  return function prefetch<TData>(
    queryKey: readonly unknown[],
    queryFn: () => Promise<TData>,
    options?: {
      staleTime?: number;
    }
  ) {
    queryClient.prefetchQuery({
      queryKey,
      queryFn,
      staleTime: options?.staleTime || 5 * 60 * 1000, // 默认5分钟
    });
  };
}

// 清除查询缓存hook
export function useClearQueries() {
  const queryClient = useQueryClient();

  return {
    clearAll: () => queryClient.clear(),
    invalidateAll: () => queryClient.invalidateQueries(),
    invalidateQueries: (queryKey: readonly unknown[]) =>
      queryClient.invalidateQueries({ queryKey }),
    removeQueries: (queryKey: readonly unknown[]) =>
      queryClient.removeQueries({ queryKey }),
    resetQueries: (queryKey: readonly unknown[]) =>
      queryClient.resetQueries({ queryKey }),
  };
}