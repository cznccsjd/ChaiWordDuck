# React Query 集成指南

本文档说明如何在拆词鸭项目中使用React Query（TanStack Query）进行数据获取和状态管理。

## 🚀 快速开始

### 1. 基本配置

React Query已经集成到项目的基础架构中，无需额外配置。

- **配置文件**: `frontend/lib/react-query/index.ts`
- **Provider**: 已在 `frontend/app/layout.tsx` 中集成
- **Devtools**: 开发环境自动启用，页面右下角可访问

### 2. 核心概念

```typescript
// Query Client - 管理查询状态
import { queryClient } from '@/lib/react-query';

// Query Keys - 查询键管理
import { queryKeys } from '@/lib/react-query';

// 通用Hooks - 封装常用操作
import { useApiQuery, useApiMutation } from '@/lib/react-query/hooks';
```

## 📚 使用指南

### 1. 基本查询

```typescript
import { useApiQuery } from '@/lib/react-query/hooks';
import { queryKeys } from '@/lib/react-query';
import { getSomeData } from '@/lib/api/someApi';

function MyComponent() {
  const {
    data,
    isLoading,
    error,
    refetch
  } = useApiQuery(
    queryKeys.someData('param'), // 查询键
    () => getSomeData('param'), // 查询函数
    {
      enabled: true, // 是否启用查询
      staleTime: 5 * 60 * 1000, // 数据保持新鲜时间（5分钟）
      onSuccess: (data) => {
        // 成功回调
        console.log('数据获取成功:', data);
      }
    }
  );

  if (isLoading) return <div>加载中...</div>;
  if (error) return <div>错误: {error.message}</div>;

  return <div>{JSON.stringify(data)}</div>;
}
```

### 2. 变更操作

```typescript
import { useApiMutation } from '@/lib/react-query/hooks';
import { queryKeys } from '@/lib/react-query';
import { updateData } from '@/lib/api/someApi';

function MyComponent() {
  const mutation = useApiMutation(
    (variables: { id: number; data: any }) => updateData(variables),
    {
      invalidateQueries: [queryKeys.someData()], // 操作成功后自动刷新相关查询
      showToast: {
        success: '更新成功！',
        error: '更新失败，请重试'
      },
      onSuccess: (data, variables) => {
        // 成功回调
        console.log('更新成功:', data);
      }
    }
  );

  const handleUpdate = () => {
    mutation.mutate({
      id: 1,
      data: { name: '新名称' }
    });
  };

  return (
    <button
      onClick={handleUpdate}
      disabled={mutation.isLoading}
    >
      {mutation.isLoading ? '更新中...' : '更新数据'}
    </button>
  );
}
```

### 3. 乐观更新

```typescript
import { useOptimisticMutation } from '@/lib/react-query/hooks';
import { queryKeys } from '@/lib/react-query';
import { updateItem } from '@/lib/api/itemsApi';

function ItemList() {
  const mutation = useOptimisticMutation(
    (variables: { id: number; data: any }) => updateItem(variables),
    {
      queryKey: queryKeys.items(),
      updateFn: (oldData, variables) => {
        // 乐观更新函数
        if (!oldData) return oldData;
        return oldData.map((item: any) =>
          item.id === variables.id
            ? { ...item, ...variables.data }
            : item
        );
      },
      showToast: {
        success: '更新成功！',
        error: '更新失败'
      }
    }
  );
}
```

## 🔧 实际示例

### 1. 单词查询Hook

```typescript
// frontend/lib/hooks/useWordQuery.ts
import { useApiQuery } from '@/lib/react-query/hooks';
import { queryKeys } from '@/lib/react-query';
import { queryWord } from '@/lib/api/words';

export function useWordQuery(word: string, enabled?: boolean) {
  return useApiQuery(
    queryKeys.searchWords(word),
    () => queryWord(word),
    {
      enabled: enabled && Boolean(word.trim()),
      staleTime: 10 * 60 * 1000, // 10分钟缓存
    }
  );
}

// 使用示例
function WordSearch() {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: wordData, isLoading, error } = useWordQuery(
    searchTerm,
    searchTerm.length > 2 // 只有输入超过2个字符才查询
  );

  // ... 组件逻辑
}
```

### 2. 查询限制Hook

```typescript
// frontend/lib/hooks/useQueryLimitReactQuery.ts
import { useApiQuery } from '@/lib/react-query/hooks';
import { queryKeys } from '@/lib/react-query';

export function useQueryLimitReactQuery() {
  const { user } = useAuthStore();

  const { data: apiQueryLimit, refetch } = useApiQuery(
    queryKeys.queryLimit,
    () => getQueryLimit(),
    {
      enabled: !!user, // 只有登录用户才启用API查询
      staleTime: 2 * 60 * 1000,
    }
  );

  // 游客使用本地存储逻辑...

  return {
    remaining: user ? apiQueryLimit?.remaining : guestRemaining,
    refetch,
    // ... 其他属性
  };
}
```

## 🎯 最佳实践

### 1. 查询键管理

```typescript
// 使用查询键工厂确保一致性
export const queryKeys = {
  user: ['user'] as const,
  userById: (id: number) => [...queryKeys.user, id] as const,
  userSettings: () => [...queryKeys.user, 'settings'] as const,

  // 相关查询
  invalidateUserQueries: (queryClient) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.user });
  }
} as const;
```

### 2. 错误处理

React Query已与现有Toast系统集成：

```typescript
// 自动通过Toast显示错误
const { data, error } = useApiQuery(queryKey, queryFn);
// 错误会自动显示在Toast中

// 自定义错误处理
const mutation = useApiMutation(mutationFn, {
  showToast: {
    success: '操作成功！',
    error: '自定义错误消息'
  }
});
```

### 3. 性能优化

```typescript
// 预加载查询
function usePrefetchQueries() {
  const queryClient = useQueryClient();

  // 在用户可能需要之前预加载数据
  useEffect(() => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.userData(),
      queryFn: getUserData,
      staleTime: 5 * 60 * 1000
    });
  }, []);
}

// 条件查询
function UserProfile({ userId }) {
  const { data } = useApiQuery(
    queryKeys.userById(userId),
    () => getUserProfile(userId),
    {
      enabled: !!userId // 只有userId存在时才查询
    }
  );
}
```

### 4. 缓存策略

```typescript
// 根据数据特性设置不同的缓存策略
const { data } = useApiQuery(queryKey, fetchFn, {
  // 用户数据：经常变化，短缓存
  staleTime: 2 * 60 * 1000, // 2分钟
  gcTime: 5 * 60 * 1000, // 5分钟

  // 字典数据：很少变化，长缓存
  staleTime: 60 * 60 * 1000, // 1小时
  gcTime: 24 * 60 * 60 * 1000, // 1天
});
```

## 🐛 调试技巧

### 1. React Query Devtools

- 开发环境自动启用
- 页面右下角点击图标打开
- 可以查看：
  - 查询状态
  - 缓存数据
  - API请求详情
  - 查询依赖关系

### 2. 查询日志

开发环境下自动启用查询日志：

```typescript
// console输出示例
[Query Success] words/search/extravagant: { id: 123, word: "extravagant", ... }
[Query Error] words/query-limit: "API请求失败"
```

### 3. 查询状态检查

```typescript
function DebugQuery() {
  const queryClient = useQueryClient();

  const logQueryState = (queryKey: any[]) => {
    const query = queryClient.getQueryCache().find({ queryKey });
    console.log('查询状态:', {
      status: query?.state.status,
      fetchStatus: query?.state.fetchStatus,
      data: query?.state.data,
      error: query?.state.error,
      staleTime: query?.state.staleTime,
    });
  };

  return <button onClick={() => logQueryState(queryKeys.userData())}>
    检查查询状态
  </button>;
}
```

## 🔄 迁移指南

### 从传统async/await迁移到React Query

**之前：**
```typescript
function useUser() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        const data = await getUserApi();
        setUser(data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  return { user, loading, error };
}
```

**之后：**
```typescript
function useUser() {
  return useApiQuery(
    queryKeys.user(),
    () => getUserApi()
  );
}
```

React Query自动处理：
- ✅ 加载状态
- ✅ 错误状态
- ✅ 缓存管理
- ✅ 重复请求去重
- ✅ 后台重新获取
- ✅ 错误重试

## 📋 清单

集成React Query后的检查清单：

- [ ] 使用 `useApiQuery` 替代手动 fetch/axios
- [ ] 使用 `useApiMutation` 处理数据变更
- [ ] 正确设置查询键（使用 `queryKeys` 工厂）
- [ ] 根据数据特性设置适当的 `staleTime`
- [ ] 使用 `invalidateQueries` 自动刷新相关数据
- [ ] 利用乐观更新提升用户体验
- [ ] 通过 Devtools 调试查询状态
- [ ] 确保错误通过 Toast 正确显示给用户

## 🆘 常见问题

### Q: 如何取消正在进行的查询？
```typescript
const { data } = useApiQuery(queryKey, queryFn, {
  enabled: false // 禁用自动查询
});

// 手动触发查询
const { refetch } = useApiQuery(queryKey, queryFn);
refetch(); // 手动执行查询

// 使用 queryClient 取消查询
queryClient.cancelQueries({ queryKey });
```

### Q: 如何处理依赖查询？
```typescript
// 只有当第一个查询成功后才执行第二个查询
const { data: user } = useApiQuery(queryKeys.user(), getUser);
const { data: profile } = useApiQuery(
  queryKeys.userProfile(user?.id),
  () => getUserProfile(user.id),
  {
    enabled: !!user // 只有user存在时才查询profile
  }
);
```

### Q: 如何实现无限滚动？
```typescript
import { useInfiniteQuery } from '@tanstack/react-query';

function useInfiniteItems() {
  return useInfiniteQuery({
    queryKey: queryKeys.items(),
    queryFn: ({ pageParam = 0 }) => fetchItems({ page: pageParam }),
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.hasMore) {
        return allPages.length;
      }
      return undefined;
    }
  });
}
```