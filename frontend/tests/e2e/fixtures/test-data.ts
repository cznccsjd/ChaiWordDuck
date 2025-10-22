/**
 * 测试数据配置
 * 包含用于E2E测试的各种测试用例数据
 */

export const TEST_WORDS = {
  // 简单单词（应该成功）
  SIMPLE: {
    word: 'hello',
    description: '简单单词测试'
  },

  // 长单词（>=8字母，应该是主要测试目标）
  LONG_WORDS: [
    {
      word: 'beautiful',
      description: '8字母长单词',
      expected_parts: 2
    },
    {
      word: 'comprehensive',
      description: '12字母长单词',
      expected_parts: 3
    },
    {
      word: 'internationalization',
      description: '20字母超长单词',
      expected_parts: 4
    }
  ],

  // 边界情况
  EDGE_CASES: {
    empty: '',
    whitespace: '   ',
    short: 'hi',
    exact_boundary: 'testing', // 7字母，边界情况
    just_over_boundary: 'amazing', // 7字母，接近边界
    valid_minimum: 'computer' // 8字母，最小有效长度
  },

  // 特殊字符
  SPECIAL_CHARS: {
    with_numbers: 'hello123',
    with_hyphen: 'well-known',
    with_apostrophe: "can't",
    mixed: "test-word123"
  }
};

export const TEST_USERS = {
  // 游客用户（未登录）
  GUEST: {
    type: 'guest',
    expected_queries_limit: 3,
    description: '游客用户限制测试'
  }
};

export const TEST_SCENARIOS = {
  // 网络延迟测试
  NETWORK_LATENCY: {
    slow_connection: { delay: 2000, description: '慢速网络测试' },
    timeout_simulation: { delay: 30000, description: '超时模拟测试' }
  },

  // API错误模拟
  API_ERRORS: {
    server_error: { status: 500, description: '服务器错误' },
    rate_limit: { status: 429, description: '请求频率限制' },
    not_found: { status: 404, description: 'API不存在' }
  }
};

export const VIEWPORTS = {
  // 响应式测试视口
  DESKTOP: { width: 1920, height: 1080, name: 'Desktop' },
  TABLET: { width: 768, height: 1024, name: 'Tablet' },
  MOBILE: { width: 375, height: 667, name: 'Mobile' }
};

export const TIME_CONFIG = {
  // 超时配置（毫秒）
  DEFAULT_TIMEOUT: 10000,
  NAVIGATION_TIMEOUT: 30000,
  API_RESPONSE_TIMEOUT: 45000, // 后端有20秒延迟，加上缓冲
  RETRY_DELAY: 5000,
  SHORT_WAIT: 1000,
  MEDIUM_WAIT: 3000,
  LONG_WAIT: 10000
};

export const ERROR_MESSAGES = {
  // 期望看到的错误消息
  NETWORK_ERROR: '网络错误，请稍后重试',
  TIMEOUT_ERROR: '请求超时，请检查网络连接',
  RATE_LIMIT: '查询次数已达限制，请注册账号获得更多查询机会',
  INVALID_INPUT: '请输入有效的单词（至少2个字符）',
  SHORT_WORD: '请输入至少8个字母的长单词',
  SERVER_ERROR: '服务器错误，请稍后重试'
};

export const SUCCESS_SELECTORS = {
  // 成功状态的CSS选择器
  WORD_DECOMPOSITION: '[data-testid="word-decomposition"]',
  WORD_STORY: '[data-testid="word-story"]',
  WORD_EXAMPLES: '[data-testid="word-examples"]',
  MEMORY_TECHNIQUES: '[data-testid="memory-techniques"]'
};

export const ERROR_SELECTORS = {
  // 错误状态的CSS选择器
  ERROR_MESSAGE: '[data-testid="error-message"]',
  LOADING_SPINNER: '[data-testid="loading-spinner"]',
  RETRY_BUTTON: '[data-testid="retry-button"]'
};

export const INTERACTION_SELECTORS = {
  // 交互元素选择器
  WORD_INPUT: '[data-testid="word-input"]',
  SUBMIT_BUTTON: '[data-testid="submit-button"]',
  LOGIN_BUTTON: '[data-testid="login-button"]',
  REGISTER_BUTTON: '[data-testid="register-button"]',
  QUERY_COUNT_DISPLAY: '[data-testid="query-count"]'
};