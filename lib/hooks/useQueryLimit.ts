import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/store/auth';
import { getQueryLimit } from '@/lib/api/words';
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

export function useQueryLimit() {
  const { user } = useAuthStore();
  const [queryLimit, setQueryLimit] = useState<QueryLimit>({
    remaining: 1,
    total: 1,
    is_guest: true,
  });
  const [isLoading, setIsLoading] = useState(true);

  // 加载查询限制
  const loadQueryLimit = async () => {
    setIsLoading(true);
    try {
      if (user) {
        // 已登录用户：从API获取
        const limit = await getQueryLimit();
        setQueryLimit(limit);
      } else {
        // 游客：从localStorage获取
        getGuestId(); // 确保游客ID存在
        const record = getGuestQueryRecord();
        setQueryLimit({
          remaining: Math.max(0, 1 - record.count),
          total: 1,
          is_guest: true,
        });
      }
    } catch (error) {
      console.error('Failed to load query limit:', error);
      // 出错时使用默认值
      if (!user) {
        const record = getGuestQueryRecord();
        setQueryLimit({
          remaining: Math.max(0, 1 - record.count),
          total: 1,
          is_guest: true,
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  // 检查单词是否已查询过
  const hasQueriedWord = (word: string): boolean => {
    if (user) {
      // 已登录用户：从API判断（暂时返回false，实际需要后端支持）
      return false;
    } else {
      // 游客：从localStorage判断
      const record = getGuestQueryRecord();
      return record.queriedWords.includes(word.toLowerCase());
    }
  };

  // 记录查询
  const recordQuery = (word: string) => {
    if (user) {
      // 已登录用户：查询已在后端记录，只需刷新限制
      loadQueryLimit();
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

      // 更新状态
      setQueryLimit({
        remaining: Math.max(0, 1 - record.count),
        total: 1,
        is_guest: true,
      });
    }
  };

  // 初始化和监听用户登录状态变化
  useEffect(() => {
    loadQueryLimit();
  }, [user]);

  return {
    ...queryLimit,
    isLoading,
    hasQueriedWord,
    recordQuery,
    refresh: loadQueryLimit,
  };
}
