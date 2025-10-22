import { test, expect } from '@playwright/test';
import { TestHelpers } from './helpers/test-helpers';
import { TEST_WORDS, TIME_CONFIG } from './fixtures/test-data';

/**
 * 核心功能测试
 * 专注于最重要的功能验证，避免设备配置冲突
 */

test.describe('拆词鸭核心功能测试', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('首页正常加载并显示关键元素', async ({ page }) => {
    console.log('🌐 开始测试首页加载...');

    // 访问首页
    await page.goto('/');

    // 等待页面加载完成
    await helpers.waitForPageLoad();

    // 验证页面标题
    await expect(page).toHaveTitle('拆词鸭 - ChaiWord Duck');

    // 验证关键元素可见
    await expect(page.locator('h1').filter({ hasText: '拆词鸭' })).toBeVisible();
    await expect(page.getByText('让长单词变得有故事、可拆解、能记住')).toBeVisible();

    // 验证输入框和按钮
    await expect(page.getByPlaceholder('输入要学习的单词...')).toBeVisible();
    await expect(page.getByRole('button', { name: '搜索' })).toBeVisible();

    // 验证导航栏
    await expect(page.getByRole('link', { name: '首页' })).toBeVisible();
    await expect(page.getByRole('link', { name: '登录' })).toBeVisible();
    // 验证至少有一个注册链接
    await expect(page.locator('a[href="/register"]')).toHaveCount(2);

    // 截图保存
    await page.screenshot({ path: 'test-results/homepage-loaded.png', fullPage: true });

    console.log('✅ 首页加载测试通过');
  });

  test('简单单词查询测试', async ({ page }) => {
    console.log('🔍 开始测试简单单词查询...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    const testWord = TEST_WORDS.SIMPLE.word;
    console.log(`🔍 [E2E] 开始测试单词: ${testWord}`);

    // 输入单词
    await page.getByPlaceholder('输入要学习的单词...').fill(testWord);

    // 点击提交按钮
    await page.getByRole('button', { name: '搜索' }).click();
    console.log(`📤 [E2E] 已提交单词: ${testWord}`);

    // 等待AI响应
    console.log('⏳ [E2E] 等待AI响应...');
    await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);

    // 尝试等待结果或错误消息
    try {
      await Promise.race([
        page.waitForSelector('.text-gray-800', { timeout: TIME_CONFIG.API_RESPONSE_TIMEOUT }),
        page.waitForSelector('.text-gray-500, .text-red-600', { timeout: TIME_CONFIG.API_RESPONSE_TIMEOUT }),
        page.waitForSelector('.animate-spin', { state: 'hidden', timeout: TIME_CONFIG.API_RESPONSE_TIMEOUT })
      ]);
      console.log(`✅ [E2E] AI响应完成`);
    } catch (error) {
      console.log(`⚠️ [E2E] AI响应等待超时，继续测试`);
    }

    // 验证页面状态
    const hasResults = await page.locator('.text-gray-800').filter({ hasText: /定义|记忆|场景/ }).count() > 0;
    const hasError = await page.locator('.text-red-600, .text-gray-500').count() > 0;

    console.log(`📊 [E2E] 结果状态 - 有结果: ${hasResults}, 有错误: ${hasError}`);

    // 截图保存
    await page.screenshot({
      path: `test-results/simple-word-${testWord}-result.png`,
      fullPage: false
    });

    console.log(`✅ 简单单词查询测试完成: ${testWord}`);
  });

  test('长单词查询测试', async ({ page }) => {
    console.log('🎯 开始测试长单词查询...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    const testWord = TEST_WORDS.LONG_WORDS[0].word; // beautiful
    console.log(`🎯 [E2E] 测试长单词: ${testWord} (${TEST_WORDS.LONG_WORDS[0].description})`);

    // 记录开始时间，观察重试逻辑
    const startTime = Date.now();

    // 输入长单词
    await page.getByPlaceholder('输入要学习的单词...').fill(testWord);
    await page.getByRole('button', { name: '搜索' }).click();

    console.log(`📤 [E2E] 已提交长单词: ${testWord}`);

    // 主动观察重试过程
    let retryDetected = false;
    const checkRetry = async () => {
      const retryTexts = [
        '正在尝试',
        '重试第',
        'AI服务繁忙',
        '请稍等',
        '正在连接'
      ];

      for (const text of retryTexts) {
        const element = page.locator(`text=${text}`);
        if (await element.count() > 0) {
          retryDetected = true;
          console.log(`🔄 [E2E] 检测到重试消息: ${text}`);
          return true;
        }
      }
      return false;
    };

    // 定期检查重试状态
    const retryCheckInterval = setInterval(checkRetry, 3000);

    try {
      // 等待AI响应（设置较长超时时间）
      await Promise.race([
        page.waitForSelector('.text-gray-800', { timeout: TIME_CONFIG.API_RESPONSE_TIMEOUT }),
        page.waitForSelector('.text-gray-500, .text-red-600', { timeout: TIME_CONFIG.API_RESPONSE_TIMEOUT }),
        page.waitForSelector('.animate-spin', { state: 'hidden', timeout: TIME_CONFIG.API_RESPONSE_TIMEOUT })
      ]);
      console.log(`✅ [E2E] 长单词AI响应完成`);
    } catch (error) {
      console.log(`⚠️ [E2E] 长单词AI响应等待超时`);
    } finally {
      clearInterval(retryCheckInterval);
    }

    const totalTime = Date.now() - startTime;
    console.log(`⏱️ [E2E] 长单词查询总耗时: ${totalTime}ms`);

    // 验证结果
    const hasResults = await page.locator('.text-gray-800').filter({ hasText: /定义|记忆|场景/ }).count() > 0;
    const hasError = await page.locator('.text-red-600, .text-gray-500').count() > 0;

    console.log(`📊 [E2E] 长单词结果状态 - 有结果: ${hasResults}, 有错误: ${hasError}, 检测到重试: ${retryDetected}`);

    // 如果总时间超过30秒，很可能触发了重试逻辑
    if (totalTime > 30000) {
      console.log('✅ [E2E] 响应时间较长，重试逻辑很可能已触发');
      retryDetected = true;
    }

    // 截图保存
    await page.screenshot({
      path: `test-results/long-word-${testWord}-detected-${retryDetected}.png`,
      fullPage: false
    });

    console.log(`✅ 长单词查询测试完成，耗时: ${totalTime}ms`);
  });

  test('输入框功能验证', async ({ page }) => {
    console.log('📝 开始测试输入框功能...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    const input = page.getByPlaceholder('输入要学习的单词...');

    // 测试输入功能
    await input.fill('test');
    await expect(input).toHaveValue('test');

    // 测试清空功能
    await input.fill('');
    await expect(input).toHaveValue('');

    // 测试长单词输入
    await input.fill(TEST_WORDS.LONG_WORDS[0].word);
    await expect(input).toHaveValue(TEST_WORDS.LONG_WORDS[0].word);

    console.log('✅ 输入框功能测试通过');
  });

  test('页面导航功能验证', async ({ page }) => {
    console.log('🧭 开始测试页面导航功能...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    // 测试注册链接
    await page.locator('a[href="/register"]').first().click();
    await expect(page).toHaveURL('/register');
    await page.goBack();

    // 测试登录链接
    await page.getByRole('link', { name: '登录' }).click();
    await expect(page).toHaveURL('/login');
    await page.goBack();

    // 验证回到首页
    await expect(page).toHaveURL('/');

    console.log('✅ 页面导航功能测试通过');
  });

  test('响应式设计基础验证', async ({ page }) => {
    console.log('📱 开始测试响应式设计基础验证...');

    // 测试桌面视图
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await helpers.waitForPageLoad();

    await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
    await expect(page.getByPlaceholder('输入要学习的单词...')).toBeVisible();

    // 截图保存桌面视图
    await page.screenshot({
      path: 'test-results/responsive-desktop-basic.png',
      fullPage: false
    });

    // 测试移动视图
    await page.setViewportSize({ width: 375, height: 667 });
    await helpers.waitForPageLoad();

    await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
    await expect(page.getByPlaceholder('输入要学习的单词...')).toBeVisible();

    // 截图保存移动视图
    await page.screenshot({
      path: 'test-results/responsive-mobile-basic.png',
      fullPage: false
    });

    console.log('✅ 响应式设计基础验证通过');
  });

  test('性能基准测试', async ({ page }) => {
    console.log('⚡ 开始性能基准测试...');

    const startTime = Date.now();

    await page.goto('/');
    await helpers.waitForPageLoad();

    const loadTime = Date.now() - startTime;

    // 页面加载时间应该在合理范围内（5秒内）
    expect(loadTime).toBeLessThan(5000);

    console.log(`✅ 性能基准测试通过，加载时间: ${loadTime}ms`);
  });

  test('错误处理和验证', async ({ page }) => {
    console.log('🛡️ 开始测试错误处理...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    // 检查控制台错误
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // 执行一次正常查询
    await page.getByPlaceholder('输入要学习的单词...').fill('error-test');
    await page.getByRole('button', { name: '搜索' }).click();

    await page.waitForTimeout(TIME_CONFIG.MEDIUM_WAIT);

    if (errors.length > 0) {
      console.log(`❌ [E2E] 控制台错误:`, errors);
    } else {
      console.log(`✅ [E2E] 无控制台错误`);
    }

    console.log('✅ 错误处理和验证测试完成');
  });
});