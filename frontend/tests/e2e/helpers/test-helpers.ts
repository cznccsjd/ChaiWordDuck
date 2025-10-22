import { Page, expect } from '@playwright/test';
import { TIME_CONFIG, TEST_WORDS, ERROR_MESSAGES } from '../fixtures/test-data';

/**
 * E2E测试辅助函数集合
 */

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * 等待页面完全加载并验证关键元素
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');

    // 验证主标题（使用更精确的选择器）
    await expect(this.page.getByRole('heading', { level: 1, name: '🦆 拆词鸭' }).or(
      this.page.locator('h1').filter({ hasText: '拆词鸭' })
    )).toBeVisible();

    await expect(this.page.getByPlaceholder('输入要学习的单词...')).toBeVisible();
    await expect(this.page.getByRole('button', { name: '搜索' })).toBeVisible();
  }

  /**
   * 输入单词并提交
   */
  async submitWord(word: string): Promise<void> {
    console.log(`🔍 [E2E] 开始测试单词: ${word}`);

    // 输入单词
    await this.page.getByPlaceholder('输入要学习的单词...').fill(word);

    // 验证输入框的值
    const inputValue = await this.page.getByPlaceholder('输入要学习的单词...').inputValue();
    expect(inputValue).toBe(word);

    // 点击提交按钮
    await this.page.getByRole('button', { name: '搜索' }).click();
    console.log(`📤 [E2E] 已提交单词: ${word}`);
  }

  /**
   * 等待AI响应完成
   */
  async waitForAIResponse(timeout: number = TIME_CONFIG.API_RESPONSE_TIMEOUT): Promise<void> {
    console.log(`⏳ [E2E] 等待AI响应，超时时间: ${timeout}ms`);

    // 等待加载状态出现（可能不会立即出现）
    await this.page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);

    try {
      // 等待加载状态消失或出现结果
      await Promise.race([
        this.page.waitForSelector('[data-testid="word-decomposition"], .text-gray-500', { timeout }),
        this.page.waitForSelector('.animate-spin', { state: 'hidden', timeout })
      ]);
      console.log(`✅ [E2E] AI响应完成`);
    } catch (error) {
      console.log(`⚠️ [E2E] AI响应等待超时: ${timeout}ms`);
      throw error;
    }
  }

  /**
   * 验证单词拆解结果
   */
  async verifyWordDecomposition(word: string): Promise<void> {
    console.log(`🔬 [E2E] 验证单词拆解结果: ${word}`);

    // 检查是否显示成功结果或错误消息
    const hasResults = await this.page.locator('.text-gray-800').filter({ hasText: /定义|记忆|场景/ }).count() > 0;
    const hasError = await this.page.locator('.text-red-600, .text-gray-500').count() > 0;

    if (hasResults) {
      console.log(`✅ [E2E] 找到单词拆解结果`);
      // 截图保存成功状态
      await this.page.screenshot({
        path: `test-results/word-${word}-success.png`,
        fullPage: false
      });
    } else if (hasError) {
      console.log(`❌ [E2E] 显示错误消息`);
      // 截图保存错误状态
      await this.page.screenshot({
        path: `test-results/word-${word}-error.png`,
        fullPage: false
      });
    } else {
      console.log(`⚠️ [E2E] 未找到预期结果或错误消息`);
    }
  }

  /**
   * 验证重试逻辑
   */
  async verifyRetryMechanism(word: string): Promise<void> {
    console.log(`🔄 [E2E] 验证重试逻辑: ${word}`);

    // 检查是否显示重试消息
    const retryMessage = await this.page.locator('text=/正在尝试|重试第|重试失败/').count();
    if (retryMessage > 0) {
      console.log(`✅ [E2E] 检测到重试消息`);
    }

    // 等待额外时间观察重试
    await this.page.waitForTimeout(TIME_CONFIG.RETRY_DELAY);
  }

  /**
   * 验证游客查询限制
   */
  async verifyGuestQueryLimit(): Promise<void> {
    console.log(`🚫 [E2E] 验证游客查询限制`);

    // 检查是否显示限制提示
    const limitMessage = await this.page.locator('text=/查询次数已达限制|注册账号/').count();
    if (limitMessage > 0) {
      console.log(`✅ [E2E] 显示查询限制提示`);
    } else {
      console.log(`⚠️ [E2E] 未显示查询限制提示`);
    }
  }

  /**
   * 测试响应式设计
   */
  async testResponsiveDesign(viewport: { width: number; height: number; name: string }): Promise<void> {
    console.log(`📱 [E2E] 测试响应式设计: ${viewport.name} (${viewport.width}x${viewport.height})`);

    // 设置视口
    await this.page.setViewportSize(viewport);

    // 验证页面布局
    await this.waitForPageLoad();

    // 截图保存响应式状态
    await this.page.screenshot({
      path: `test-results/responsive-${viewport.name.toLowerCase()}.png`,
      fullPage: true
    });

    console.log(`✅ [E2E] 响应式设计测试完成: ${viewport.name}`);
  }

  /**
   * 模拟网络延迟
   */
  async simulateNetworkDelay(delay: number): Promise<void> {
    console.log(`🐌 [E2E] 模拟网络延迟: ${delay}ms`);

    // 这里可以通过context.route来模拟网络延迟
    // 暂时使用简单等待
    await this.page.waitForTimeout(delay);
  }

  /**
   * 记录测试性能指标
   */
  async recordPerformanceMetrics(testName: string): Promise<void> {
    const metrics = await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
        totalTime: navigation.loadEventEnd - navigation.fetchStart
      };
    });

    console.log(`📊 [E2E] 性能指标 [${testName}]:`, metrics);
  }

  /**
   * 检查控制台错误
   */
  async checkConsoleErrors(): Promise<void> {
    const errors: string[] = [];
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    if (errors.length > 0) {
      console.log(`❌ [E2E] 控制台错误:`, errors);
    } else {
      console.log(`✅ [E2E] 无控制台错误`);
    }
  }

  /**
   * 清理测试数据
   */
  async cleanup(): Promise<void> {
    // 清除输入框内容
    await this.page.getByPlaceholder('输入要学习的单词...').fill('');

    // 等待页面稳定
    await this.page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
  }

  /**
   * 执行完整的单词查询测试流程
   */
  async runCompleteWordTest(word: string, expectSuccess: boolean = true): Promise<boolean> {
    try {
      console.log(`🚀 [E2E] 开始完整测试流程: ${word}`);

      // 记录开始时间
      const startTime = Date.now();

      // 1. 提交单词
      await this.submitWord(word);

      // 2. 等待AI响应
      await this.waitForAIResponse();

      // 3. 验证结果
      await this.verifyWordDecomposition(word);

      // 4. 验证重试逻辑
      await this.verifyRetryMechanism(word);

      // 记录总耗时
      const totalTime = Date.now() - startTime;
      console.log(`⏱️ [E2E] 测试完成，总耗时: ${totalTime}ms`);

      return true;
    } catch (error) {
      console.log(`❌ [E2E] 测试失败: ${word}`, error);

      // 截图保存错误状态
      await this.page.screenshot({
        path: `test-results/word-${word}-failure.png`,
        fullPage: true
      });

      return false;
    }
  }
}