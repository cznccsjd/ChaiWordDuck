import { test as base, Page, BrowserContext } from '@playwright/test';
import { TestHelpers } from '../helpers/test-helpers';

/**
 * 测试设置和扩展
 * 提供全局测试配置和自定义 fixtures
 */

// 扩展测试 fixtures
export interface TestFixtures {
  helpers: TestHelpers;
  page: Page;
  context: BrowserContext;
}

// 自定义测试上下文
export const test = base.extend<TestFixtures>({
  // 自定义BrowserContext配置
  context: async ({ browser }, use) => {
    // 创建带有用户代理的BrowserContext
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    });

    await use(context);

    // 清理context
    await context.close();
  },

  // 为每个测试创建 helpers 实例
  helpers: async ({ page, context }, use) => {
    const helpers = new TestHelpers(page);

    // 设置测试前的全局配置
    await setupTestEnvironment(page, context);

    await use(helpers);

    // 测试后的清理工作
    await cleanupTestEnvironment(page);
  },

  // 自定义页面配置
  page: async ({ page }, use) => {
    // 设置页面默认配置
    await configurePage(page);

    await use(page);
  }
});

/**
 * 设置测试环境
 */
async function setupTestEnvironment(page: Page, context: BrowserContext) {
  console.log('🔧 [E2E] 设置测试环境...');

  // 设置默认视口
  await page.setViewportSize({ width: 1280, height: 720 });

  // 监听控制台错误
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('❌ [E2E] 控制台错误:', msg.text());
    }
  });

  // 监听页面错误
  page.on('pageerror', error => {
    console.log('❌ [E2E] 页面错误:', error.message);
  });

  // 监听请求失败
  page.on('requestfailed', request => {
    console.log('❌ [E2E] 请求失败:', request.url(), request.failure()?.errorText);
  });

  // 设置自定义超时
  page.setDefaultTimeout(30000);

  console.log('✅ [E2E] 测试环境设置完成');
}

/**
 * 配置页面
 */
async function configurePage(page: Page) {
  // 设置时区
  await page.evaluate(() => {
    // 设置为北京时间
    (window as any).playwright = {
      timezone: 'Asia/Shanghai'
    };
  });

  // 禁用动画（提高测试稳定性）
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-delay: 0.01ms !important;
        transition-duration: 0.01ms !important;
        transition-delay: 0.01ms !important;
      }
    `
  });

  // 添加测试标识
  await page.addStyleTag({
    content: `
      body::before {
        content: 'TEST_MODE';
        position: fixed;
        top: 0;
        right: 0;
        background: rgba(255, 0, 0, 0.8);
        color: white;
        padding: 2px 6px;
        font-size: 10px;
        z-index: 999999;
        pointer-events: none;
      }
    `
  });
}

/**
 * 清理测试环境
 */
async function cleanupTestEnvironment(page: Page) {
  console.log('🧹 [E2E] 清理测试环境...');

  try {
    // 清除所有定时器
    await page.evaluate(() => {
      const highestId = window.setTimeout(() => {}, 0);
      for (let i = 0; i < highestId; i++) {
        window.clearTimeout(i);
        window.clearInterval(i);
      }
    });

    // 清除localStorage和sessionStorage
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // 重置页面状态
    await page.reload();

    console.log('✅ [E2E] 测试环境清理完成');
  } catch (error) {
    console.log('⚠️ [E2E] 清理测试环境时出错:', error);
  }
}

/**
 * 创建测试结果目录
 */
export async function ensureTestResultsDirectory() {
  const fs = require('fs');
  const path = require('path');

  const directories = [
    'test-results',
    'test-results/screenshots',
    'test-results/videos',
    'test-results/traces',
    'test-results/reports'
  ];

  directories.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      console.log(`📁 创建目录: ${dir}`);
    }
  });
}

/**
 * 生成测试数据
 */
export async function generateTestData() {
  console.log('📝 [E2E] 生成测试数据...');

  const testData = {
    timestamp: new Date().toISOString(),
    testSession: `session-${Date.now()}`,
    environment: process.env.NODE_ENV || 'test',
    browserVersion: await getBrowserVersion(),
    testWords: [
      'beautiful',
      'comprehensive',
      'internationalization',
      'hello',
      'test'
    ]
  };

  return testData;
}

/**
 * 获取浏览器版本信息
 */
async function getBrowserVersion() {
  const puppeteer = require('puppeteer');
  try {
    const browser = await puppeteer.launch();
    const version = await browser.version();
    await browser.close();
    return version;
  } catch {
    return 'unknown';
  }
}

/**
 * 测试前的全局设置
 */
test.beforeAll(async () => {
  console.log('🚀 [E2E] 开始测试前的全局设置...');

  // 确保测试结果目录存在
  await ensureTestResultsDirectory();

  // 生成测试数据
  const testData = await generateTestData();
  console.log('📊 [E2E] 测试数据:', testData);

  console.log('✅ [E2E] 全局设置完成');
});

/**
 * 测试后的全局清理
 */
test.afterAll(async () => {
  console.log('🏁 [E2E] 开始测试后的全局清理...');

  // 这里可以添加全局清理逻辑
  // 比如清理测试数据库、关闭资源等

  console.log('✅ [E2E] 全局清理完成');
});

// 导出默认配置
export const config = {
  retries: 2,
  timeout: 60000,
  expect: {
    timeout: 10000
  },
  use: {
    actionTimeout: 10000,
    navigationTimeout: 30000,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure'
  }
};

// 重新导出所有 Playwright 测试函数
export { expect, devices } from '@playwright/test';