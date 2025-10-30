import { test, expect } from '@playwright/test';

test.describe('MCP Integration Test', () => {
  test('基础页面加载测试', async ({ page }) => {
    // 启动开发服务器后测试主页
    await page.goto('/');

    // 检查页面是否正确加载
    await expect(page).toHaveTitle(/拆词鸭/);

    // 检查基本元素是否存在
    const mainElement = page.locator('main, body');
    await expect(mainElement).toBeVisible();
  });

  test('MCP 连通性验证', async ({ page }) => {
    // 这个测试用于验证 MCP 工具可以正常工作
    await page.goto('/');

    // 截图用于验证
    await page.screenshot({ path: 'test-results/mcp-test-screenshot.png' });

    // 检查控制台错误
    page.on('console', (message) => {
      if (message.type() === 'error') {
        console.log('Console error:', message.text());
      }
    });

    // 等待页面稳定
    await page.waitForTimeout(1000);

    // 验证页面结构
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});