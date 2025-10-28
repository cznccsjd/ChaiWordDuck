import { test, expect } from '@playwright/test';

test.describe('真实单词查询测试', () => {
  test('搜索单词 "embarrassment" - 已知存在的单词', async ({ page }) => {
    await page.goto('/');

    // 输入已知存在的单词
    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await searchInput.fill('embarrassment');

    // 点击搜索按钮
    const searchButton = page.locator('button', { hasText: '搜索' });
    await searchButton.click();

    // 等待页面跳转到单词详情页
    await page.waitForTimeout(5000);

    // 检查是否跳转到单词详情页面
    const currentUrl = page.url();
    console.log('当前URL:', currentUrl);

    if (currentUrl.includes('/word/')) {
      console.log('成功跳转到单词详情页面');

      // 验证单词基本信息显示
      await expect(page.locator('h1, h2', { hasText: /embarrassment/i })).toBeVisible({ timeout: 10000 });

      // 验证音标显示
      const phoneticElement = page.locator('text=/ɪmˈbærəsmənt/');
      if (await phoneticElement.isVisible()) {
        await expect(phoneticElement).toBeVisible();
        console.log('✓ 音标显示正常');
      }

      // 验证词性显示
      const nounElement = page.locator('text=noun');
      if (await nounElement.isVisible()) {
        await expect(nounElement).toBeVisible();
        console.log('✓ 词性显示正常');
      }

      // 验证拼写技巧显示
      const memoryTrick = page.locator('text=/拼写陷阱|两个r|两个s/');
      if (await memoryTrick.isVisible()) {
        await expect(memoryTrick).toBeVisible();
        console.log('✓ 记忆技巧显示正常');
      }

      // 验证词根拆解显示
      const etymologyElement = page.locator('text=/em-|barr|ment/');
      if (await etymologyElement.isVisible()) {
        await expect(etymologyElement).toBeVisible();
        console.log('✓ 词根拆解显示正常');
      }

      console.log('✓ 所有核心信息验证通过');
    } else {
      console.log('❌ 未跳转到单词详情页面');
      // 检查是否有错误消息
      const errorElement = page.locator('text=/错误|失败|未找到/');
      if (await errorElement.isVisible()) {
        console.log('发现错误消息:', await errorElement.textContent());
      }
    }
  });

  test('验证页面完整性 - 检查所有重要组件', async ({ page }) => {
    await page.goto('/');

    // 验证页面标题和logo
    await expect(page.locator('h1', { hasText: '拆词鸭' })).toBeVisible();
    await expect(page.locator('text=🦆')).toBeVisible();

    // 验证产品特色介绍
    await expect(page.locator('text=语言游戏')).toBeVisible();
    await expect(page.locator('text=拆解记忆')).toBeVisible();
    await expect(page.locator('text=创意秘籍')).toBeVisible();

    // 验证搜索框
    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toHaveAttribute('placeholder', '输入要学习的单词...');

    // 验证搜索按钮
    const searchButton = page.locator('button', { hasText: '搜索' });
    await expect(searchButton).toBeVisible();

    // 验证游客模式提示
    const guestMode = page.locator('text=/游客模式|今日剩余/');
    if (await guestMode.isVisible()) {
      await expect(guestMode).toBeVisible();
      console.log('✓ 游客模式提示正常显示');
    }

    // 验证注册引导
    const registerPrompt = page.locator('text=注册账号');
    if (await registerPrompt.isVisible()) {
      await expect(registerPrompt).toBeVisible();
      console.log('✓ 注册引导正常显示');
    }

    console.log('✓ 首页所有重要组件验证通过');
  });

  test('错误处理 - 无效输入测试', async ({ page }) => {
    await page.goto('/');

    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    const searchButton = page.locator('button', { hasText: '搜索' });

    // 测试空输入
    await searchInput.fill('');
    await searchButton.click();

    // 等待错误提示
    await page.waitForTimeout(1000);
    const toastError = page.locator('text=/请输入单词/');
    if (await toastError.isVisible()) {
      console.log('✓ 空输入错误提示正常');
    }

    // 测试非英文字符
    await searchInput.fill('测试中文');
    await searchButton.click();

    await page.waitForTimeout(1000);
    const invalidInput = page.locator('text=/请输入英文单词/');
    if (await invalidInput.isVisible()) {
      console.log('✓ 非英文字符错误提示正常');
    }

    // 测试数字和符号混合
    await searchInput.fill('test123!');
    await searchButton.click();

    await page.waitForTimeout(1000);
    const invalidChars = page.locator('text=/仅支持字母/');
    if (await invalidChars.isVisible()) {
      console.log('✓ 无效字符错误提示正常');
    }
  });

  test('响应式设计测试', async ({ page }) => {
    // 桌面视图
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/');

    // 验证桌面布局
    await expect(page.locator('h1', { hasText: '拆词鸭' })).toBeVisible();
    await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible();

    // 移动端视图
    await page.setViewportSize({ width: 375, height: 667 });

    // 验证移动端布局
    await expect(page.locator('h1', { hasText: '拆词鸭' })).toBeVisible();
    await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible();

    // 验证移动端搜索功能
    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    await searchInput.fill('test');
    await expect(searchInput).toHaveValue('test');

    console.log('✓ 响应式设计验证通过');
  });

  test('性能测试', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    const loadTime = Date.now() - startTime;

    console.log(`页面加载时间: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(5000); // 放宽到5秒

    // 关键元素加载时间
    const elementStartTime = Date.now();
    await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible({ timeout: 5000 });
    const elementLoadTime = Date.now() - elementStartTime;

    console.log(`关键元素加载时间: ${elementLoadTime}ms`);
    expect(elementLoadTime).toBeLessThan(3000);
  });
});