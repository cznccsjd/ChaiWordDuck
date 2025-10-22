import { useCallback } from 'react';
import { useApiQuery, useApiMutation } from '@/lib/react-query/hooks';
import { queryKeys } from '@/lib/react-query';
import { getQueryLimit } from '@/lib/api/words';
import { useAuthStore } from '@/lib/store/auth';
import type { QueryLimit } from '@/types';

const GUEST_STORAGE_KEY = 'chaiword_guest_queries';
const GUEST_COOKIE_NAME = 'guest_id';

// 生成游客ID
function generateGuestId(): string {
  return `guest_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

// 获取或创建游客ID
function getGuestId(): string {
  if (typeof window === 'undefined') return '';

  // 尝试从cookie获取
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === GUEST_COOKIE_NAME) {
      return value;
    }
  }

  // 创建新的游客ID
  const guestId = generateGuestId();

  // 存储到cookie（7天过期）
  const expiryDate = new Date();
  expiryDate.setDate(expiryDate.getDate() + 7);
  document.cookie = `${GUEST_COOKIE_NAME}=${guestId}; expires=${expiryDate.toUTCString()}; path=/`;

  return guestId;
}

// 获取今天的日期字符串（用于判断是否需要重置）
function getTodayKey(): string {
  return new Date().toISOString().split('T')[0];
}

// 游客查询记录结构
interface GuestQueryRecord {
  date: string;
  count: number;
  queriedWords: string[];
}

// 获取游客查询记录
function getGuestQueryRecord(): GuestQueryRecord {
  if (typeof window === 'undefined') {
    return { date: getTodayKey(), count: 0, queriedWords: [] };
  }

  const stored = localStorage.getItem(GUEST_STORAGE_KEY);
  if (!stored) {
    return { date: getTodayKey(), count: 0, queriedWords: [] };
  }

  try {
    const record: GuestQueryRecord = JSON.parse(stored);
    const today = getTodayKey();

    // 如果是新的一天，重置记录
    if (record.date !== today) {
      return { date: today, count: 0, queriedWords: [] };
    }

    return record;
  } catch {
    return { date: getTodayKey(), count: 0, queriedWords: [] };
  }
}

// 保存游客查询记录
function saveGuestQueryRecord(record: GuestQueryRecord) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(record));
}

// 获取游客查询限制（本地函数）
function getGuestQueryLimit(): QueryLimit {
  getGuestId(); // 确保游客ID存在
  const record = getGuestQueryRecord();
  return {
    remaining: Math.max(0, 1 - record.count),
    total: 1,
    is_guest: true,
  };
}

export function useQueryLimitReactQuery() {
  const { user } = useAuthStore();

  // 对于已登录用户，使用React Query查询API
  const {
    data: apiQueryLimit,
    isLoading: isApiLoading,
    refetch: refetchApi,
  } = useApiQuery(
    queryKeys.queryLimit,
    () => getQueryLimit(),
    {
      enabled: !!user, // 只有登录用户才启用
      staleTime: 2 * 60 * 1000, // 2分钟
      gcTime: 5 * 60 * 1000, // 5分钟缓存
    }
  );

  // 对于游客，使用本地存储
  const guestQueryLimit = getGuestQueryLimit();

  // 根据用户状态返回相应的查询限制
  const queryLimit = user ? (apiQueryLimit || { remaining: 0, total: 3, is_guest: false }) : guestQueryLimit;
  const isLoading = user ? isApiLoading : false;

  // 检查单词是否已查询过
  const hasQueriedWord = useCallback((word: string): boolean => {
    if (user) {
      // 已登录用户：从API判断（暂时返回false，实际需要后端支持）
      return false;
    } else {
      // 游客：从localStorage判断
      const record = getGuestQueryRecord();
      return record.queriedWords.includes(word.toLowerCase());
    }
  }, [user]);

  // 记录查询
  const recordQuery = useCallback((word: string) => {
    if (user) {
      // 已登录用户：查询已在后端记录，只需刷新限制
      refetchApi();
    } else {
      // 游客：更新localStorage
      const record = getGuestQueryRecord();
      const wordLower = word.toLowerCase();

      // 如果单词已查询过，不消耗次数
      if (record.queriedWords.includes(wordLower)) {
        return;
      }

      record.count += 1;
      record.queriedWords.push(wordLower);
      saveGuestQueryRecord(record);

      // 这里不直接更新状态，让组件重新渲染时从localStorage读取最新值
    }
  }, [user, refetchApi]);

  // 刷新查询限制
  const refresh = useCallback(() => {
    if (user) {
      refetchApi();
    }
    // 对于游客，组件会在下次渲染时自动从localStorage读取最新数据
  }, [user, refetchApi]);

  return {
    ...queryLimit,
    isLoading,
    hasQueriedWord,
    recordQuery,
    refresh,
  };
}