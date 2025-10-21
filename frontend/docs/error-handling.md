# 前端错误处理指南

## 概述

本项目已经更新了前端错误处理机制，以更好地支持后端的新错误格式，特别是429状态码的API限额限制错误。

## 新的错误处理功能

### 1. 支持的错误格式

#### 新格式（推荐）
```typescript
{
  success: false,
  error: {
    code: "AI_GENERATION_LIMIT_EXCEEDED",
    message: "原始错误消息"
  }
}
```

#### 传统格式（向后兼容）
```typescript
{
  detail: "错误详情"
}
// 或
{
  message: "错误消息"
}
```

### 2. 429错误专门处理

系统现在能够识别和处理`AI_GENERATION_LIMIT_EXCEEDED`错误码，并为不同用户类型提供友好的提示消息：

#### 游客用户
```
🦆 游客体验次数已用完！
注册账号可享受每天3次免费查询，还能收藏喜欢的单词哦！
```

#### 注册用户
```
📚 今日查询次数已用完！
明天会自动重置，或升级高级版享受无限查询权限～
```

## 使用方法

### 1. 基本错误处理

```typescript
import { handleApiError } from '@/lib/api/client';

try {
  // API调用
  await someApiCall();
} catch (error) {
  const errorMessage = handleApiError(error);
  // 处理错误消息
}
```

### 2. 在组件中使用ErrorDisplay

```typescript
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';

const MyComponent = () => {
  const [error, setError] = useState<string | null>(null);

  return (
    <div>
      {error && (
        <ErrorDisplay
          message={error}
          onRetry={() => {/* 重试逻辑 */}}
          onDismiss={() => setError(null)}
          type="warning"
        />
      )}
    </div>
  );
};
```

### 3. 错误码常量

```typescript
import { ERROR_CODES } from '@/lib/api/client';

// 检查特定错误码
if (error.code === ERROR_CODES.AI_GENERATION_LIMIT_EXCEEDED) {
  // 处理限额超出错误
}
```

## 组件更新

### SearchBox组件
- 集成了新的错误显示组件
- 429错误会显示友好的提示和操作按钮
- 支持游客引导注册和用户升级提示

### ErrorDisplay组件
- 新建的通用错误显示组件
- 支持不同类型的错误（error, warning, info）
- 内置操作按钮（重试、注册、升级等）
- 可关闭的错误提示

## 测试覆盖

错误处理逻辑已包含完整的单元测试：
- 传统格式错误处理
- 新格式错误处理
- 429错误的专门处理
- 用户类型区分
- 边界情况处理

运行测试：
```bash
npm test -- --testPathPatterns=errorHandling.test.ts
```

## 最佳实践

1. **始终使用handleApiError**: 确保所有API错误都通过统一的错误处理函数处理
2. **区分错误类型**: 对于429错误使用ErrorDisplay组件，其他错误可使用toast
3. **提供操作建议**: 在限额错误时提供明确的解决方案（注册、升级等）
4. **保持友好语气**: 错误消息应该清晰、友好，包含适当的emoji
5. **测试覆盖**: 为新的错误场景添加相应的测试用例

## 迁移指南

### 从旧错误处理迁移

```typescript
// 旧方式
catch (error) {
  const message = error.response?.data?.detail || '请求失败';
  showToast(message, 'error');
}

// 新方式
catch (error) {
  const message = handleApiError(error);
  if (message.includes('次数已用完')) {
    setError(message); // 使用ErrorDisplay
  } else {
    showToast(message, 'error'); // 使用toast
  }
}
```

## 未来扩展

1. **更多错误码**: 可以根据需要添加更多专门的错误码处理
2. **国际化支持**: 可以为错误消息添加多语言支持
3. **错误上报**: 可以集成错误监控和上报系统
4. **智能重试**: 对于某些错误可以实现智能重试机制