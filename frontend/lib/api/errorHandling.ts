import axios, { AxiosError } from 'axios';

// 错误类型定义
export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
  };
}

export interface LegacyErrorResponse {
  detail?: string;
  message?: string;
}

// 429错误码常量
export const ERROR_CODES = {
  AI_GENERATION_LIMIT_EXCEEDED: 'AI_GENERATION_LIMIT_EXCEEDED',
} as const;

// 辅助函数：处理 API 错误
export function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse | LegacyErrorResponse>;

    // 处理429状态码的特殊错误
    if (axiosError.response?.status === 429) {
      return handle429Error(axiosError.response.data as ApiErrorResponse);
    }

    // 尝试新的错误格式 {success: false, error: {code, message}}
    const newFormatData = axiosError.response?.data as ApiErrorResponse;
    if (newFormatData && !newFormatData.success && newFormatData.error) {
      return newFormatData.error.message;
    }

    // 兼容旧的错误格式 {detail?: string; message?: string}
    const legacyData = axiosError.response?.data as LegacyErrorResponse;
    return legacyData?.detail || legacyData?.message || '请求失败，请稍后重试';
  }
  return '未知错误，请稍后重试';
}

// 处理429错误的专门函数
function handle429Error(errorData: ApiErrorResponse): string {
  const { code, message } = errorData.error;

  switch (code) {
    case ERROR_CODES.AI_GENERATION_LIMIT_EXCEEDED:
      // 根据用户类型提供不同的提示
      return getLimitExceededMessage(message);
    default:
      return message || '请求过于频繁，请稍后重试';
  }
}

// 根据错误消息提供更友好的提示
function getLimitExceededMessage(originalMessage: string): string {
  // 可以根据实际需要进一步定制消息
  if (originalMessage.includes('游客') || originalMessage.includes('guest')) {
    return `🦆 游客体验次数已用完！
注册账号可享受每天3次免费查询，还能收藏喜欢的单词哦！`;
  } else if (originalMessage.includes('升级') || originalMessage.includes('premium')) {
    return `📚 今日查询次数已用完！
明天会自动重置，或升级高级版享受无限查询权限～`;
  }

  // 默认友好提示
  return `⏰ 今日查询次数已用完！
明天会自动重置继续学习之旅～`;
}