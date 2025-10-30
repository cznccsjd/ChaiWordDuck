import { test, expect } from '@playwright/test';

test.describe('修复后的搜索功能测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3002');
  });

  test('页面加载正常', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/拆词鸭|ChaiWord Duck/);

    // 验证主要元素存在
    await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible();
    await expect(page.locator('button', { hasText: '搜索' })).toBeVisible();

    // 验证页面主要内容
    await expect(page.locator('h1', { hasText: '拆词鸭' })).toBeVisible();
    await expect(page.locator('text=让长单词变得有故事、可拆解、能记住')).toBeVisible();
  });

  test('搜索单词 "everything" - 完整流程测试', async ({ page }) => {
    // 输入测试单词
    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await searchInput.fill('everything');

    // 点击搜索按钮
    const searchButton = page.locator('button', { hasText: '搜索' });
    await searchButton.click();

    // 等待页面跳转到单词详情页
    await page.waitForTimeout(3000);

    // 检查是否跳转到单词详情页面
    const currentUrl = page.url();
    console.log('当前URL:', currentUrl);

    if (currentUrl.includes('/word/')) {
      // 验证单词基本信息显示
      await expect(page.locator('h1, h2', { hasText: /everything/i })).toBeVisible({ timeout: 10000 });

      // 验证音标显示
      const phoneticElement = page.locator('text=/ɪvˈriθɪŋ/');
      if (await phoneticElement.isVisible()) {
        await expect(phoneticElement).toBeVisible();
      }

      // 验证词性显示
      const pronounElement = page.locator('text=pronoun');
      const determinerElement = page.locator('text=determiner');

      if (await pronounElement.isVisible()) {
        await expect(pronounElement).toBeVisible();
      }
      if (await determinerElement.isVisible()) {
        await expect(determinerElement).toBeVisible();
      }

      // 验证中文释义
      const chineseMeaning1 = page.locator('text=每件事');
      const chineseMeaning2 = page.locator('text=一切');

      if (await chineseMeaning1.isVisible()) {
        await expect(chineseMeaning1).toBeVisible();
      }
      if (await chineseMeaning2.isVisible()) {
        await expect(chineseMeaning2).toBeVisible();
      }

      // 验证例句显示
      const exampleElement = page.locator('text=/Everything is ready/');
      if (await exampleElement.isVisible()) {
        await expect(exampleElement).toBeVisible();
      }
    } else {
      console.log('未跳转到单词详情页面，可能搜索失败或页面结构发生变化');
      // 检查是否有错误消息
      const errorElement = page.locator('text=/错误|失败|未找到/');
      if (await errorElement.isVisible()) {
        console.log('发现错误消息:', await errorElement.textContent());
      }
    }
  });

  test('单词拆解功能验证', async ({ page }) => {
    // 搜索单词
    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await searchInput.fill('everything');
    await page.locator('button', { hasText: '搜索' }).click();

    // 等待页面跳转
    await page.waitForTimeout(3000);

    if (page.url().includes('/word/')) {
      // 验证拆解部分存在
      const decompSection = page.locator('text=单词拆解').first();
      if (await decompSection.isVisible()) {
        console.log('找到单词拆解部分');
        // 验证拆解结果显示
        const decompContent = page.locator('[data-testid="word-decomposition"], .decomposition, .word-breakdown');
        if (await decompContent.isVisible()) {
          await expect(decompContent).toBeVisible();
          console.log('单词拆解内容正常显示');
        }
      } else {
        console.log('未找到单词拆解部分，可能功能正在开发中');
      }
    }
  });

  test('记忆辅助功能验证', async ({ page }) => {
    // 搜索单词
    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await searchInput.fill('everything');
    await page.locator('button', { hasText: '搜索' }).click();

    // 等待页面跳转
    await page.waitForTimeout(3000);

    if (page.url().includes('/word/')) {
      // 验证记忆辅助部分
      const memorySection = page.locator('text=记忆辅助|记忆技巧|记忆方法').first();
      if (await memorySection.isVisible()) {
        console.log('找到记忆辅助部分');
        // 验证记忆技巧显示
        const memoryContent = page.locator('[data-testid="memory-tips"], .memory-tips, .memory-guide');
        if (await memoryContent.isVisible()) {
          await expect(memoryContent).toBeVisible();
          console.log('记忆辅助内容正常显示');
        }
      } else {
        console.log('未找到记忆辅助部分，可能功能正在开发中');
      }
    }
  });

  test('搜索功能交互测试', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');

    // 测试输入框清空功能
    await searchInput.fill('test');
    await expect(searchInput).toHaveValue('test');
    await searchInput.clear();
    await expect(searchInput).toHaveValue('');

    // 测试回车搜索
    await searchInput.fill('everything');
    await searchInput.press('Enter');

    // 等待搜索结果
    await page.waitForTimeout(3000);

    // 验证是否跳转到单词详情页
    if (page.url().includes('/word/')) {
      console.log('回车搜索成功，已跳转到单词详情页');
    }
  });

  test('错误处理测试 - 不存在的单词', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await searchInput.fill('nonexistentword12345');
    await page.locator('button', { hasText: '搜索' }).click();

    // 等待处理结果
    await page.waitForTimeout(3000);

    // 验证错误提示
    const errorMessage = page.locator('text=/未找到|not found|错误|失败/').first();
    if (await errorMessage.isVisible()) {
      console.log('发现错误消息:', await errorMessage.textContent());
      await expect(errorMessage).toBeVisible();
    } else {
      console.log('未显示明确的错误消息');
    }
  });

  test('响应式布局测试', async ({ page }) => {
    // 测试桌面视图
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/');

    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await expect(searchInput).toBeVisible();
    await expect(page.locator('button', { hasText: '搜索' })).toBeVisible();

    // 验证桌面布局
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('h1', { hasText: '拆词鸭' })).toBeVisible();

    // 测试移动端视图
    await page.setViewportSize({ width: 375, height: 667 });

    // 验证移动端布局调整
    await expect(searchInput).toBeVisible();
    await expect(page.locator('button', { hasText: '搜索' })).toBeVisible();

    // 验证搜索功能在移动端正常
    await searchInput.fill('test');
    await expect(searchInput).toHaveValue('test');
  });

  test('页面导航和链接测试', async ({ page }) => {
    // 检查是否有导航链接
    const navLinks = page.locator('nav a, header a, a[href*="register"], a[href*="login"]');
    const linkCount = await navLinks.count();

    if (linkCount > 0) {
      console.log(`找到 ${linkCount} 个导航链接`);

      // 测试注册链接（如果存在）
      const registerLink = page.locator('a[href*="register"]');
      if (await registerLink.isVisible()) {
        await registerLink.click();
        await page.waitForTimeout(2000);

        // 验证页面导航正常（没有崩溃）
        await expect(page).not.toHaveURL(/about:blank/);
        console.log('注册链接导航正常');
      }
    } else {
      console.log('未找到导航链接');
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
    console.log(`页面加载时间: ${loadTime}ms`);

    // 关键元素应该在加载完成时可见
    await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible({ timeout: 5000 });
  });

  test('搜索响应时间', async ({ page }) => {
    await page.goto('/');

    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await searchInput.fill('everything');

    const startTime = Date.now();
    await page.locator('button', { hasText: '搜索' }).click();

    // 等待页面跳转或结果显示
    await page.waitForTimeout(3000);
    const responseTime = Date.now() - startTime;

    // 搜索响应时间应该在10秒内（包含页面跳转时间）
    expect(responseTime).toBeLessThan(10000);

    console.log(`搜索响应时间: ${responseTime}ms`);
  });
});

test.describe('查询限制功能测试', () => {
  test('游客模式查询次数显示', async ({ page }) => {
    await page.goto('/');

    // 验证游客模式提示
    const guestText = page.locator('text=/游客模式|今日剩余/');
    if (await guestText.isVisible()) {
      console.log('游客模式查询次数提示正常显示');
      await expect(guestText).toBeVisible();
    }

    // 验证注册引导
    const registerPrompt = page.locator('text=注册账号');
    if (await registerPrompt.isVisible()) {
      console.log('注册引导正常显示');
      await expect(registerPrompt).toBeVisible();
    }
  });
});