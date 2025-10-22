import { test, expect, devices } from '@playwright/test';
import { TestHelpers } from './helpers/test-helpers';
import { TEST_WORDS, TIME_CONFIG, VIEWPORTS } from './fixtures/test-data';

/**
 * 拆词鸭首页E2E测试
 * 测试页面加载、基础功能和用户交互
 */

test.describe('拆词鸭首页功能测试', () => {
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
    await expect(page.getByRole('heading', { name: '拆词鸭' })).toBeVisible();
    await expect(page.getByText('让长单词变得有故事、可拆解、能记住')).toBeVisible();

    // 验证输入框和按钮
    await expect(page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful')).toBeVisible();
    await expect(page.getByRole('button', { name: '开始拆解' })).toBeVisible();

    // 验证导航栏
    await expect(page.getByRole('link', { name: '首页' })).toBeVisible();
    await expect(page.getByRole('link', { name: '登录' })).toBeVisible();
    await expect(page.getByRole('link', { name: '注册' })).toBeVisible();

    // 验证特性介绍
    await expect(page.getByText('语言游戏')).toBeVisible();
    await expect(page.getByText('拆解记忆')).toBeVisible();
    await expect(page.getByText('创意秘籍')).toBeVisible();

    // 记录性能指标
    await helpers.recordPerformanceMetrics('首页加载');

    // 截图保存
    await page.screenshot({ path: 'test-results/homepage-loaded.png', fullPage: true });

    console.log('✅ 首页加载测试通过');
  });

  test('输入框功能验证', async ({ page }) => {
    console.log('📝 开始测试输入框功能...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    const input = page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful');

    // 测试输入框占位符
    await expect(input).toHaveAttribute('placeholder', '输入您想学习英语长单词，比如：beautiful');

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

  test('提交按钮状态验证', async ({ page }) => {
    console.log('🔘 开始测试提交按钮状态...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    const input = page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful');
    const submitButton = page.getByRole('button', { name: '开始拆解' });

    // 初始状态：按钮应该可用
    await expect(submitButton).toBeEnabled();

    // 输入内容后按钮状态
    await input.fill('test');
    await expect(submitButton).toBeEnabled();

    // 清空内容后按钮状态
    await input.fill('');
    await expect(submitButton).toBeEnabled(); // 前端验证可能允许空输入

    // 测试按钮点击
    await input.fill(TEST_WORDS.SIMPLE.word);
    await submitButton.click();

    // 点击后应该显示加载状态或结果
    await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);

    console.log('✅ 提交按钮状态测试通过');
  });

  test('页面导航功能验证', async ({ page }) => {
    console.log('🧭 开始测试页面导航功能...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    // 测试注册链接
    await page.getByRole('link', { name: '注册' }).click();
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

  test('页面内容完整性验证', async ({ page }) => {
    console.log('📄 开始测试页面内容完整性...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    // 验证"为什么选择拆词鸭"部分
    await expect(page.getByRole('heading', { name: '为什么选择拆词鸭？' })).toBeVisible();
    await expect(page.getByText('专注长单词')).toBeVisible();
    await expect(page.getByText('五步学习法')).toBeVisible();
    await expect(page.getByText('故事化记忆')).toBeVisible();
    await expect(page.getByText('科学复习')).toBeVisible();

    // 验证页脚
    await expect(page.getByText('© 2025 拆词鸭 ChaiWord Duck')).toBeVisible();

    // 检查没有404错误
    await helpers.checkConsoleErrors();

    console.log('✅ 页面内容完整性测试通过');
  });

  test('响应式设计验证', async ({ page }) => {
    console.log('📱 开始测试响应式设计...');

    // 测试桌面视图
    await helpers.testResponsiveDesign(VIEWPORTS.DESKTOP);

    // 测试平板视图
    await helpers.testResponsiveDesign(VIEWPORTS.TABLET);

    // 测试手机视图
    await helpers.testResponsiveDesign(VIEWPORTS.MOBILE);

    console.log('✅ 响应式设计测试通过');
  });

  test('性能基准测试', async ({ page }) => {
    console.log('⚡ 开始性能基准测试...');

    const startTime = Date.now();

    await page.goto('/');
    await helpers.waitForPageLoad();

    const loadTime = Date.now() - startTime;

    // 页面加载时间应该在合理范围内（5秒内）
    expect(loadTime).toBeLessThan(5000);

    // 记录详细性能指标
    await helpers.recordPerformanceMetrics('性能基准测试');

    console.log(`✅ 性能基准测试通过，加载时间: ${loadTime}ms`);
  });

  test('SEO和可访问性验证', async ({ page }) => {
    console.log('🔍 开始SEO和可访问性测试...');

    await page.goto('/');

    // 验证meta标签
    await expect(page.locator('meta[name="description"]')).toHaveAttribute(
      'content',
      '专注于成人英语长单词学习的创新教育产品'
    );

    // 验证lang属性
    await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN');

    // 验证viewport设置
    await expect(page.locator('meta[name="viewport"]')).toHaveAttribute(
      'content',
      'width=device-width, initial-scale=1, maximum-scale=5'
    );

    // 验证标题层次结构
    const h1s = page.locator('h1');
    await expect(h1s).toHaveCount(1); // 应该只有一个h1

    // 验证图片alt属性（如果有图片的话）
    // await expect(page.locator('img')).toHaveAttribute('alt');

    console.log('✅ SEO和可访问性测试通过');
  });
});

// 移动设备专门测试
test.describe('移动设备专门测试', () => {
  test.use({ ...devices['iPhone 12'] });

  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('iPhone 12上的首页功能', async ({ page }) => {
    console.log('📱 开始iPhone 12专门测试...');

    await page.goto('/');
    await helpers.waitForPageLoad();

    // 验证移动端特有的UI元素
    await expect(page.getByRole('button').filter({ hasText: '登录' })).toBeVisible();
    await expect(page.getByRole('button').filter({ hasText: '注册' })).toBeVisible();

    // 测试移动端输入体验
    await page.getByPlaceholder('输入您想学习英语长单词，比如：beautiful').fill('mobiletest');

    // 测试移动端按钮点击
    await page.getByRole('button', { name: '开始拆解' }).tap(); // 使用tap而不是click

    // 等待响应
    await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);

    console.log('✅ iPhone 12专门测试通过');
  });
});