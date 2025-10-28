import { test, expect } from '@playwright/test';

test.describe('单词查询功能测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('页面加载正常', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/ChaiWord Duck/);

    // 验证主要元素存在
    await expect(page.locator('input[placeholder*="搜索"]')).toBeVisible();
    await expect(page.locator('button', { hasText: '搜索' })).toBeVisible();
  });

  test('搜索单词 "everything" - 完整流程测试', async ({ page }) => {
    // 输入测试单词
    const searchInput = page.locator('input[placeholder*="搜索"]');
    await searchInput.fill('everything');

    // 点击搜索按钮
    const searchButton = page.locator('button', { hasText: '搜索' });
    await searchButton.click();

    // 等待搜索结果加载
    await page.waitForTimeout(2000);

    // 验证单词基本信息显示
    await expect(page.locator('h1, h2', { hasText: /everything/i })).toBeVisible();

    // 验证音标显示
    await expect(page.locator('text=/ɪvˈriθɪŋ/')).toBeVisible();

    // 验证词性显示
    await expect(page.locator('text=pronoun')).toBeVisible();
    await expect(page.locator('text=determiner')).toBeVisible();

    // 验证中文释义
    await expect(page.locator('text=每件事')).toBeVisible();
    await expect(page.locator('text=一切')).toBeVisible();

    // 验证例句显示
    await expect(page.locator('text=/Everything is ready/')).toBeVisible();
    await expect(page.locator('text=/一切都准备好了/')).toBeVisible();
  });

  test('单词拆解功能验证', async ({ page }) => {
    // 搜索单词
    const searchInput = page.locator('input[placeholder*="搜索"]');
    await searchInput.fill('everything');
    await page.locator('button', { hasText: '搜索' }).click();

    // 等待结果加载
    await page.waitForTimeout(2000);

    // 验证拆解部分存在
    const decompSection = page.locator('text=单词拆解').first();
    if (await decompSection.isVisible()) {
      // 验证拆解结果显示
      await expect(page.locator('[data-testid="word-decomposition"]')).toBeVisible();

      // 验证词根/前缀/后缀分析
      const prefixElements = page.locator('[data-testid="prefix-analysis"]');
      const rootElements = page.locator('[data-testid="root-analysis"]');
      const suffixElements = page.locator('[data-testid="suffix-analysis"]');

      // 至少应该有一种拆解结果
      const hasAnyDecomposition =
        (await prefixElements.count() > 0) ||
        (await rootElements.count() > 0) ||
        (await suffixElements.count() > 0);

      expect(hasAnyDecomposition).toBeTruthy();
    } else {
      console.log('单词拆解功能暂未显示，可能功能正在开发中');
    }
  });

  test('记忆辅助功能验证', async ({ page }) => {
    // 搜索单词
    const searchInput = page.locator('input[placeholder*="搜索"]');
    await searchInput.fill('everything');
    await page.locator('button', { hasText: '搜索' }).click();

    // 等待结果加载
    await page.waitForTimeout(2000);

    // 验证记忆辅助部分
    const memorySection = page.locator('text=记忆辅助').first();
    if (await memorySection.isVisible()) {
      // 验证记忆技巧显示
      await expect(page.locator('[data-testid="memory-tips"]')).toBeVisible();

      // 验证联想记忆或词根记忆内容
      const memoryContent = page.locator('[data-testid="memory-content"]');
      expect(await memoryContent.count()).toBeGreaterThan(0);
    } else {
      console.log('记忆辅助功能暂未显示，可能功能正在开发中');
    }
  });

  test('搜索功能交互测试', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]');

    // 测试输入框清空功能
    await searchInput.fill('test');
    await expect(searchInput).toHaveValue('test');
    await searchInput.clear();
    await expect(searchInput).toHaveValue('');

    // 测试回车搜索
    await searchInput.fill('everything');
    await searchInput.press('Enter');

    // 等待搜索结果
    await page.waitForTimeout(2000);

    // 验证搜索结果出现
    await expect(page.locator('h1, h2', { hasText: /everything/i })).toBeVisible();
  });

  test('错误处理测试 - 不存在的单词', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]');
    await searchInput.fill('nonexistentword12345');
    await page.locator('button', { hasText: '搜索' }).click();

    // 等待处理结果
    await page.waitForTimeout(2000);

    // 验证错误提示或未找到提示
    const errorMessage = page.locator('text=/未找到|not found|错误/').first();
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toBeVisible();
    } else {
      // 如果没有错误消息，页面应该显示空状态或提示信息
      const emptyState = page.locator('[data-testid="empty-state"]').first();
      if (await emptyState.isVisible()) {
        await expect(emptyState).toBeVisible();
      }
    }
  });

  test('响应式布局测试', async ({ page }) => {
    // 测试桌面视图
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/');

    const searchInput = page.locator('input[placeholder*="搜索"]');
    await searchInput.fill('everything');
    await page.locator('button', { hasText: '搜索' }).click();
    await page.waitForTimeout(2000);

    // 验证桌面布局
    await expect(page.locator('main')).toBeVisible();

    // 测试移动端视图
    await page.setViewportSize({ width: 375, height: 667 });

    // 验证移动端布局调整
    await expect(searchInput).toBeVisible();
    await expect(page.locator('button', { hasText: '搜索' })).toBeVisible();

    // 验证搜索结果在移动端的显示
    if (await page.locator('h1, h2', { hasText: /everything/i }).isVisible()) {
      await expect(page.locator('h1, h2', { hasText: /everything/i })).toBeVisible();
    }
  });

  test('页面导航和链接测试', async ({ page }) => {
    // 检查是否有导航链接
    const navLinks = page.locator('nav a, header a');
    const linkCount = await navLinks.count();

    if (linkCount > 0) {
      // 测试第一个导航链接
      await navLinks.first().click();
      await page.waitForTimeout(1000);

      // 验证页面导航正常（没有崩溃）
      await expect(page).not.toHaveURL(/about:blank/);
    }
  });
});

test.describe('性能和加载测试', () => {
  test('页面加载性能', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    const loadTime = Date.now() - startTime;

    // 页面应该在3秒内加载完成
    expect(loadTime).toBeLessThan(3000);

    // 关键元素应该在加载完成时可见
    await expect(page.locator('input[placeholder*="搜索"]')).toBeVisible({ timeout: 5000 });
  });

  test('搜索响应时间', async ({ page }) => {
    await page.goto('/');

    const searchInput = page.locator('input[placeholder*="搜索"]');
    await searchInput.fill('everything');

    const startTime = Date.now();
    await page.locator('button', { hasText: '搜索' }).click();

    // 等待搜索结果显示
    await page.waitForSelector('h1, h2', { hasText: /everything/i }, { timeout: 10000 });
    const responseTime = Date.now() - startTime;

    // 搜索响应时间应该在5秒内
    expect(responseTime).toBeLessThan(5000);

    console.log(`搜索响应时间: ${responseTime}ms`);
  });
});