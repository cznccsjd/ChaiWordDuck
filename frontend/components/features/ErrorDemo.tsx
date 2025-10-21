'use client';

import { useState } from 'react';
import { Button } from '@/components/ui';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';

// 预定义的错误消息用于演示
const errorMessages = {
  legacyError: '这是一个传统的错误消息',
  newFormatError: '输入数据验证失败',
  guestLimitError: '🦆 游客体验次数已用完！\n注册账号可享受每天3次免费查询，还能收藏喜欢的单词哦！',
  userLimitError: '📚 今日查询次数已用完！\n明天会自动重置，或升级高级版享受无限查询权限～',
  networkError: '网络连接失败，请检查网络后重试',
  serverError: '服务器内部错误，请稍后重试'
};

export function ErrorDemo() {
  const [currentError, setCurrentError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<string>('');

  const showError = (type: string) => {
    const message = errorMessages[type as keyof typeof errorMessages];
    setCurrentError(message);
    setErrorType(type);
  };

  const clearError = () => {
    setCurrentError(null);
    setErrorType('');
  };

  const getErrorTypeLabel = (type: string) => {
    switch (type) {
      case 'legacyError':
        return '传统格式错误';
      case 'newFormatError':
        return '新格式错误';
      case 'guestLimitError':
        return '游客限额错误 (429)';
      case 'userLimitError':
        return '用户限额错误 (429)';
      case 'networkError':
        return '网络错误';
      case 'serverError':
        return '服务器错误';
      default:
        return '未知错误';
    }
  };

  const getErrorType = (type: string): 'error' | 'warning' | 'info' => {
    if (type.includes('Limit') || type.includes('Error')) {
      return type.includes('Limit') ? 'warning' : 'error';
    }
    return 'error';
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">错误处理演示</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {Object.entries(errorMessages).map(([key, message]) => (
          <Button
            key={key}
            onClick={() => showError(key)}
            variant="outline"
            className="text-left justify-start h-auto p-4"
          >
            <div>
              <div className="font-medium">{getErrorTypeLabel(key)}</div>
              <div className="text-xs text-gray-500 mt-1">
                {key.includes('Limit') ? '429 状态码' : '其他错误'}
              </div>
            </div>
          </Button>
        ))}
      </div>

      {currentError && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-700">
              当前错误: {getErrorTypeLabel(errorType)}
            </h3>
            <Button
              size="sm"
              variant="outline"
              onClick={clearError}
            >
              清除错误
            </Button>
          </div>

          <ErrorDisplay
            message={currentError}
            onRetry={() => {
              alert('重试功能演示 - 在实际应用中会重新尝试操作');
            }}
            onDismiss={clearError}
            type={getErrorType(errorType)}
          />

          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-700 mb-2">错误类型说明:</h4>
            <div className="text-sm text-gray-600 space-y-2">
              <p><strong>{getErrorTypeLabel(errorType)}</strong></p>
              <p>{currentError}</p>
              {errorType.includes('Limit') && (
                <p className="text-blue-600">
                  💡 提示: 这种错误类型会显示操作按钮（注册、升级等）
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {!currentError && (
        <div className="text-center text-gray-500 py-8">
          <div className="mb-4">
            <div className="text-4xl mb-2">🔧</div>
            <p>点击上方按钮来演示不同类型的错误处理</p>
          </div>
          <div className="text-sm text-gray-400">
            <p>• 限额错误会显示警告样式和操作按钮</p>
            <p>• 其他错误会显示错误样式和重试按钮</p>
            <p>• 所有错误都可以关闭</p>
          </div>
        </div>
      )}
    </div>
  );
}