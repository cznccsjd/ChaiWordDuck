import { test, expect, devices } from '@playwright/test';
import { TestHelpers } from './helpers/test-helpers';
import { TEST_WORDS, VIEWPORTS, TIME_CONFIG } from './fixtures/test-data';

/**
 * 响应式设计和跨浏览器测试
 * 测试不同设备和浏览器上的用户体验
 */

test.describe('响应式设计测试', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test.describe('桌面设备测试', () => {
    test('桌面浏览器完整功能测试', async ({ page }) => {
      console.log('🖥️ 开始桌面浏览器完整功能测试...');

      // 设置桌面视口
      await page.setViewportSize(VIEWPORTS.DESKTOP);

      await page.goto('/');
      await helpers.waitForPageLoad();

      // 验证桌面端布局
      await expect(page.getByRole('navigation')).toBeVisible();
      await expect(page.getByRole('link', { name: '首页' })).toBeVisible();
      await expect(page.getByRole('link', { name: '登录' })).toBeVisible();
      await expect(page.getByRole('link', { name: '注册' })).toBeVisible();

      // 验证内容区域布局
      await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
      await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();
      await expect(page.getByRole('button', { name: '开始拆解' })).toBeVisible();

      // 验证特性网格布局
      await expect(page.locator('.grid').filter({ hasText: '语言游戏' })).toBeVisible();

      // 测试单词查询功能
      const success = await helpers.runCompleteWordTest(TEST_WORDS.LONG_WORDS[0].word);
      expect(success).toBe(true);

      // 截图保存桌面视图
      await page.screenshot({
        path: 'test-results/responsive-desktop-full.png',
        fullPage: true
      });

      console.log('✅ 桌面浏览器完整功能测试通过');
    });

    test('桌面视口尺寸变化测试', async ({ page }) => {
      console.log('📏 开始桌面视口尺寸变化测试...');

      const desktopViewports = [
        { width: 1920, height: 1080, name: 'Full HD' },
        { width: 1440, height: 900, name: 'MacBook Pro' },
        { width: 1366, height: 768, name: 'Small Desktop' },
        { width: 1280, height: 720, name: 'HD' }
      ];

      for (const viewport of desktopViewports) {
        console.log(`测试视口: ${viewport.name} (${viewport.width}x${viewport.height})`);

        await page.setViewportSize(viewport);
        await page.goto('/');
        await helpers.waitForPageLoad();

        // 验证关键元素仍然可见和可交互
        await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();
        await expect(page.getByRole('button', { name: '开始拆解' })).toBeVisible();

        // 测试输入功能
        await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('responsive-test');
        await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toHaveValue('responsive-test');

        // 截图保存
        await page.screenshot({
          path: `test-results/responsive-desktop-${viewport.name.toLowerCase().replace(' ', '-')}.png`,
          fullPage: false
        });
      }

      console.log('✅ 桌面视口尺寸变化测试通过');
    });
  });

  test.describe('平板设备测试', () => {
    test.use({ ...devices['iPad Pro'] });

    test('iPad Pro响应式测试', async ({ page }) => {
      console.log('📱 开始iPad Pro响应式测试...');

      await page.goto('/');
      await helpers.waitForPageLoad();

      // 验证平板端布局
      await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
      await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();

      // 验证特性网格可能已调整为2列布局
      await expect(page.locator('.grid').filter({ hasText: '语言游戏' })).toBeVisible();

      // 测试单词查询功能
      const success = await helpers.runCompleteWordTest(TEST_WORDS.LONG_WORDS[0].word);
      expect(success).toBe(true);

      // 截图保存平板视图
      await page.screenshot({
        path: 'test-results/responsive-tablet-ipad-pro.png',
        fullPage: true
      });

      console.log('✅ iPad Pro响应式测试通过');
    });
  });

  // 移动设备测试
  test.describe('移动设备测试', () => {
    test.use({ ...devices['iPhone 12'] });

    test('iPhone 12移动端测试', async ({ page }) => {
      console.log('📱 开始iPhone 12移动端测试...');

      await page.goto('/');
      await helpers.waitForPageLoad();

      // 验证移动端布局
      await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
      await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();

      // 验证移动端导航（可能是汉堡菜单）
      const mobileMenuButton = page.locator('button').filter({ has: page.locator('svg') }).first();
      if (await mobileMenuButton.count() > 0) {
        await expect(mobileMenuButton).toBeVisible();
        console.log('✅ 检测到移动端汉堡菜单');
      }

      // 验证特性卡片可能是垂直布局
      await expect(page.locator('text=语言游戏')).toBeVisible();
      await expect(page.locator('text=拆解记忆')).toBeVisible();
      await expect(page.locator('text=创意秘籍')).toBeVisible();

      // 测试移动端输入体验（使用tap）
      await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('mobile-test');
      await page.getByRole('button', { name: '开始拆解' }).tap();

      await helpers.waitForAIResponse();
      await helpers.verifyWordDecomposition('mobile-test');

      // 截图保存移动视图
      await page.screenshot({
        path: 'test-results/responsive-mobile-iphone-12.png',
        fullPage: true
      });

      console.log('✅ iPhone 12移动端测试通过');
    });

    test('移动端横屏测试', async ({ page }) => {
      console.log('📱 开始移动端横屏测试...');

      // 设置横屏视口
      await page.setViewportSize({ width: 844, height: 390 }); // iPhone 12 横屏

      await page.goto('/');
      await helpers.waitForPageLoad();

      // 验证横屏布局
      await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
      await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();

      // 测试横屏下的交互
      await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('landscape-test');
      await page.getByRole('button', { name: '开始拆解' }).tap();

      await helpers.waitForAIResponse();

      // 截图保存横屏视图
      await page.screenshot({
        path: 'test-results/responsive-mobile-landscape.png',
        fullPage: true
      });

      console.log('✅ 移动端横屏测试通过');
    });
  });

  // 小屏设备测试
  test.describe('小屏设备测试', () => {
    test.use({ ...devices['Pixel 5'] });

    test('Android小屏设备测试', async ({ page }) => {
      console.log('📱 开始Android小屏设备测试...');

      await page.goto('/');
      await helpers.waitForPageLoad();

      // 验证小屏设备布局
      await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
      await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();

      // 验证内容在小屏上的可读性
      const title = page.getByRole('heading', { name: '拆词鸭' });
      await expect(title).toBeVisible();

      // 测试小屏输入体验
      await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('small-screen-test');
      await page.getByRole('button', { name: '开始拆解' }).tap();

      await helpers.waitForAIResponse();

      // 截图保存小屏视图
      await page.screenshot({
        path: 'test-results/responsive-small-android.png',
        fullPage: true
      });

      console.log('✅ Android小屏设备测试通过');
    });
  });
});

test.describe('跨浏览器兼容性测试', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
    await page.goto('/');
    await helpers.waitForPageLoad();
  });

  test('Chromium浏览器兼容性', async ({ page, browserName }) => {
    console.log(`🌐 开始${browserName}浏览器兼容性测试...`);

    // 验证基本功能
    await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
    await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();

    // 测试JavaScript功能
    await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('chromium-test');
    await page.getByRole('button', { name: '开始拆解' }).click();

    await helpers.waitForAIResponse();

    // 验证浏览器特有的CSS渲染
    const computedStyle = await page.locator('body').evaluate((el) => {
      return window.getComputedStyle(el).fontFamily;
    });
    console.log(`${browserName} 字体设置:`, computedStyle);

    // 截图保存
    await page.screenshot({
      path: `test-results/browser-${browserName}.png`,
      fullPage: true
    });

    console.log(`✅ ${browserName}浏览器兼容性测试通过`);
  });

  test('Firefox浏览器兼容性', async ({ page, browserName }) => {
    console.log(`🦊 开始${browserName}浏览器兼容性测试...`);

    // Firefox特定测试
    await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();

    // 测试表单提交（Firefox可能有不同的表单处理）
    await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('firefox-test');
    await page.getByRole('button', { name: '开始拆解' }).click();

    await helpers.waitForAIResponse();

    // 检查Firefox特有的CSS支持
    const cssGridSupported = await page.locator('.grid').evaluate((el) => {
      return window.getComputedStyle(el).display === 'grid';
    });
    console.log(`Firefox CSS Grid支持:`, cssGridSupported);

    await page.screenshot({
      path: `test-results/browser-${browserName}.png`,
      fullPage: true
    });

    console.log(`✅ ${browserName}浏览器兼容性测试通过`);
  });

  test('WebKit/Safari浏览器兼容性', async ({ page, browserName }) => {
    console.log(`🍏 开始${browserName}浏览器兼容性测试...`);

    await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();

    // Safari特定测试（WebKit）
    await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('safari-test');
    await page.getByRole('button', { name: '开始拆解' }).click();

    await helpers.waitForAIResponse();

    // 检查Safari特有的渲染特性
    const backdropFilter = await page.locator('body').evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.backdropFilter || style.webkitBackdropFilter;
    });
    console.log(`Safari backdrop-filter支持:`, !!backdropFilter);

    await page.screenshot({
      path: `test-results/browser-${browserName}.png`,
      fullPage: true
    });

    console.log(`✅ ${browserName}浏览器兼容性测试通过`);
  });
});

test.describe('交互式响应式测试', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('实时视口大小变化测试', async ({ page }) => {
    console.log('🔄 开始实时视口大小变化测试...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    // 测试动态视口变化
    const viewports = [
      { width: 1200, height: 800, name: '桌面' },
      { width: 768, height: 1024, name: '平板' },
      { width: 375, height: 667, name: '手机' },
      { width: 844, height: 390, name: '手机横屏' }
    ];

    for (const viewport of viewports) {
      console.log(`动态调整到: ${viewport.name} (${viewport.width}x${viewport.height})`);

      await page.setViewportSize(viewport);

      // 等待布局调整
      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);

      // 验证关键元素仍然可见
      await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
      await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();

      // 截图保存过渡状态
      await page.screenshot({
        path: `test-results/viewport-transition-${viewport.name}.png`,
        fullPage: false
      });
    }

    console.log('✅ 实时视口大小变化测试通过');
  });

  test('文本缩放和可访问性测试', async ({ page }) => {
    console.log('🔍 开始文本缩放和可访问性测试...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    // 测试不同的文本缩放级别
    const zoomLevels = [0.8, 1.0, 1.2, 1.5];

    for (const zoom of zoomLevels) {
      console.log(`测试文本缩放: ${zoom * 100}%`);

      await page.evaluate((level) => {
        document.documentElement.style.fontSize = `${level * 16}px`;
      }, zoom);

      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);

      // 验证文本仍然可读
      await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
      await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();

      // 测试输入功能
      await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill(`zoom-test-${zoom}`);
      await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toHaveValue(`zoom-test-${zoom}`);

      await page.screenshot({
        path: `test-results/text-zoom-${zoom}.png`,
        fullPage: false
      });
    }

    // 重置缩放
    await page.evaluate(() => {
      document.documentElement.style.fontSize = '';
    });

    console.log('✅ 文本缩放和可访问性测试通过');
  });

  test('高对比度和暗色模式测试', async ({ page }) => {
    console.log('🌓 开始高对比度和暗色模式测试...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    // 测试高对比度模式
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });

    // 验证暗色模式下的元素可见性
    await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
    await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();

    // 测试暗色模式下的功能
    await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('dark-mode-test');
    await page.getByRole('button', { name: '开始拆解' }).click();

    await helpers.waitForAIResponse();

    // 截图保存暗色模式
    await page.screenshot({
      path: 'test-results/dark-mode.png',
      fullPage: true
    });

    // 重置媒体模拟
    await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'no-preference' });

    console.log('✅ 高对比度和暗色模式测试通过');
  });
});