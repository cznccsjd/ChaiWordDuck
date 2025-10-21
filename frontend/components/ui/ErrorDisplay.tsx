'use client';

import { Button } from './Button';
import { useRouter } from 'next/navigation';

interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  type?: 'error' | 'warning' | 'info';
}

export function ErrorDisplay({
  message,
  onRetry,
  onDismiss,
  type = 'error'
}: ErrorDisplayProps) {
  const router = useRouter();

  // 检查是否是限额相关的错误
  const isLimitError = message.includes('次数已用完') ||
                       message.includes('体验次数已用完') ||
                       message.includes('查询次数已用完');

  // 检查是否是游客相关错误
  const isGuestError = message.includes('游客') ||
                       message.includes('注册');

  const getBackgroundColor = () => {
    switch (type) {
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-red-50 border-red-200';
    }
  };

  const getTextColor = () => {
    switch (type) {
      case 'warning':
        return 'text-amber-800';
      case 'info':
        return 'text-blue-800';
      default:
        return 'text-red-800';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '❌';
    }
  };

  const handleRegister = () => {
    router.push('/register');
  };

  const handleUpgrade = () => {
    // 这里可以添加升级页面的路由
    // router.push('/pricing');
    // 暂时显示提示
    alert('高级版功能即将上线，敬请期待！');
  };

  return (
    <div className={`rounded-lg border p-4 ${getBackgroundColor()}`}>
      <div className="flex items-start gap-3">
        <span className="text-lg flex-shrink-0">{getIcon()}</span>

        <div className="flex-1 min-w-0">
          <p className={`text-sm ${getTextColor()} whitespace-pre-line`}>
            {message}
          </p>

          {/* 限额错误时显示操作按钮 */}
          {isLimitError && (
            <div className="mt-3 flex flex-wrap gap-2">
              {isGuestError && (
                <Button
                  size="sm"
                  onClick={handleRegister}
                  className="text-xs px-3 py-1.5"
                >
                  立即注册
                </Button>
              )}

              {!isGuestError && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleUpgrade}
                  className="text-xs px-3 py-1.5"
                >
                  升级高级版
                </Button>
              )}

              {onRetry && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={onRetry}
                  className="text-xs px-3 py-1.5"
                >
                  稍后重试
                </Button>
              )}
            </div>
          )}

          {/* 非限额错误的通用操作 */}
          {!isLimitError && onRetry && (
            <div className="mt-3">
              <Button
                size="sm"
                variant="outline"
                onClick={onRetry}
                className="text-xs px-3 py-1.5"
              >
                重试
              </Button>
            </div>
          )}
        </div>

        {onDismiss && (
          <button
            onClick={onDismiss}
            className={`flex-shrink-0 p-1 rounded-md hover:bg-black/5 transition-colors ${getTextColor()}`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}