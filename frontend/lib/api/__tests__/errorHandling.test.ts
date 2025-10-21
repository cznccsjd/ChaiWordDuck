import { handleApiError, ERROR_CODES } from '../errorHandling';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Error Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('handleApiError', () => {
    it('should handle legacy error format with detail field', () => {
      const error = {
        response: {
          data: {
            detail: 'Legacy error message'
          },
          status: 400
        }
      };

      mockedAxios.isAxiosError.mockReturnValue(true);
      const result = handleApiError(error as any);

      expect(result).toBe('Legacy error message');
    });

    it('should handle legacy error format with message field', () => {
      const error = {
        response: {
          data: {
            message: 'Legacy message field'
          },
          status: 400
        }
      };

      mockedAxios.isAxiosError.mockReturnValue(true);
      const result = handleApiError(error as any);

      expect(result).toBe('Legacy message field');
    });

    it('should handle new API error format', () => {
      const error = {
        response: {
          data: {
            success: false,
            error: {
              code: 'SOME_ERROR',
              message: 'New format error message'
            }
          },
          status: 400
        }
      };

      mockedAxios.isAxiosError.mockReturnValue(true);
      const result = handleApiError(error as any);

      expect(result).toBe('New format error message');
    });

    it('should handle 429 error with AI_GENERATION_LIMIT_EXceeded code', () => {
      const error = {
        response: {
          data: {
            success: false,
            error: {
              code: ERROR_CODES.AI_GENERATION_LIMIT_EXCEEDED,
              message: '游客查询次数已用完'
            }
          },
          status: 429
        }
      };

      mockedAxios.isAxiosError.mockReturnValue(true);
      const result = handleApiError(error as any);

      expect(result).toContain('游客体验次数已用完');
      expect(result).toContain('注册账号可享受每天3次免费查询');
    });

    it('should handle 429 error for registered users', () => {
      const error = {
        response: {
          data: {
            success: false,
            error: {
              code: ERROR_CODES.AI_GENERATION_LIMIT_EXCEEDED,
              message: '用户查询次数已用完，请升级高级版'
            }
          },
          status: 429
        }
      };

      mockedAxios.isAxiosError.mockReturnValue(true);
      const result = handleApiError(error as any);

      expect(result).toContain('今日查询次数已用完');
      expect(result).toContain('升级高级版享受无限查询权限');
    });

    it('should handle generic 429 error', () => {
      const error = {
        response: {
          data: {
            success: false,
            error: {
              code: 'RATE_LIMIT_EXCEEDED',
              message: 'Too many requests'
            }
          },
          status: 429
        }
      };

      mockedAxios.isAxiosError.mockReturnValue(true);
      const result = handleApiError(error as any);

      expect(result).toBe('Too many requests');
    });

    it('should fall back to default message for unknown errors', () => {
      const error = {
        response: {
          data: {},
          status: 500
        }
      };

      mockedAxios.isAxiosError.mockReturnValue(true);
      const result = handleApiError(error as any);

      expect(result).toBe('请求失败，请稍后重试');
    });

    it('should handle non-axios errors', () => {
      const error = new Error('Network error');

      mockedAxios.isAxiosError.mockReturnValue(false);
      const result = handleApiError(error);

      expect(result).toBe('未知错误，请稍后重试');
    });

    it('should provide friendly default message for 429 errors without specific code', () => {
      const error = {
        response: {
          data: {
            success: false,
            error: {
              code: 'UNKNOWN_429_ERROR',
              message: ''
            }
          },
          status: 429
        }
      };

      mockedAxios.isAxiosError.mockReturnValue(true);
      const result = handleApiError(error as any);

      // 对于未知的429错误，应该返回原始消息或默认消息
      expect(result).toBe('请求过于频繁，请稍后重试');
    });
  });

  describe('ERROR_CODES', () => {
    it('should have correct error codes', () => {
      expect(ERROR_CODES.AI_GENERATION_LIMIT_EXCEEDED).toBe('AI_GENERATION_LIMIT_EXCEEDED');
    });
  });
});