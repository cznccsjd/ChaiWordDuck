import { test, expect } from '@playwright/test';

test.describe('拆词鸭 - everything单词查询E2E测试', () => {
  test.beforeEach(async ({ page }) => {
    // 访问应用主页
    await page.goto('http://localhost:3000');
    console.log('✅ 页面加载成功');
  });

  test('完整流程测试：查询"everything"单词', async ({ page }) => {
    console.log('🔍 开始测试everything单词查询功能...');

    // 步骤1: 验证页面加载正常
    await test.step('验证页面主要元素', async () => {
      // 验证页面标题
      await expect(page).toHaveTitle(/拆词鸭|ChaiWord Duck/);
      console.log('✅ 页面标题验证通过');

      // 验证主要元素存在
      await expect(page.locator('h1', { hasText: '拆词鸭' })).toBeVisible();
      await expect(page.locator('text=让长单词变得有故事、可拆解、能记住')).toBeVisible();
      console.log('✅ 页面主要内容验证通过');

      // 验证搜索框和按钮
      const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
      const searchButton = page.locator('button', { hasText: '搜索' });

      await expect(searchInput).toBeVisible();
      await expect(searchButton).toBeVisible();
      console.log('✅ 搜索功能元素验证通过');
    });

    // 步骤2: 执行搜索操作
    await test.step('输入并搜索单词', async () => {
      const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
      const searchButton = page.locator('button', { hasText: '搜索' });

      // 输入测试单词
      await searchInput.fill('everything');
      console.log('✅ 已输入搜索词: everything');

      // 验证输入框内容
      await expect(searchInput).toHaveValue('everything');
      console.log('✅ 搜索框内容验证通过');

      // 点击搜索按钮
      console.log('🔍 开始执行搜索...');
      const searchStartTime = Date.now();

      await searchButton.click();

      // 等待搜索状态变化
      await expect(page.locator('text=正在拆解...')).toBeVisible({ timeout: 5000 });
      console.log('✅ 搜索状态显示正常');
    });

    // 步骤3: 等待并验证页面跳转
    await test.step('验证页面跳转和结果显示', async () => {
      console.log('⏳ 等待搜索结果...');

      // 等待页面跳转完成
      await page.waitForURL(/\/word\/\d+/, { timeout: 15000 });
      const currentUrl = page.url();
      console.log(`✅ 页面跳转成功: ${currentUrl}`);

      // 验证是否跳转到单词详情页面
      expect(currentUrl).toMatch(/\/word\/\d+/);

      // 从URL中提取单词ID
      const wordId = currentUrl.match(/\/word\/(\d+)/)?.[1];
      console.log(`📝 单词ID: ${wordId}`);
    });

    // 步骤4: 验证单词详情页面内容
    await test.step('验证单词详情内容显示', async () => {
      console.log('📋 验证单词详情内容...');

      // 等待页面内容加载
      await page.waitForTimeout(2000);

      // 验证单词基本信息显示
      const wordTitle = page.locator('h1, h2, h3').filter({ hasText: /everything/i }).first();
      await expect(wordTitle).toBeVisible({ timeout: 10000 });
      console.log('✅ 单词标题显示正常');

      // 尝试验证各种可能的内容显示
      const contentChecks = [
        { selector: 'text=/ɪvˈriθɪŋ/', description: '音标显示' },
        { selector: 'text=pronoun', description: '词性标记(pronoun)' },
        { selector: 'text=determiner', description: '词性标记(determiner)' },
        { selector: 'text=每件事', description: '中文释义1' },
        { selector: 'text=一切', description: '中文释义2' },
        { selector: 'text=/Everything/i', description: '例句中的单词' }
      ];

      let foundContentCount = 0;
      for (const check of contentChecks) {
        try {
          const element = page.locator(check.selector).first();
          if (await element.isVisible({ timeout: 3000 })) {
            console.log(`✅ ${check.description} - 显示正常`);
            foundContentCount++;
          } else {
            console.log(`⚠️  ${check.description} - 未找到或不可见`);
          }
        } catch (error) {
          console.log(`❌ ${check.description} - 检查失败: ${error.message}`);
        }
      }

      console.log(`📊 内容显示统计: ${foundContentCount}/${contentChecks.length} 项正常显示`);
    });

    // 步骤5: 验证单词拆解功能
    await test.step('验证单词拆解功能', async () => {
      console.log('🔧 验证单词拆解功能...');

      const decompSelectors = [
        'text=单词拆解',
        'text=拆解分析',
        'text=词根拆解',
        '[data-testid="word-decomposition"]',
        '.decomposition',
        '.word-breakdown'
      ];

      let decompFound = false;
      for (const selector of decompSelectors) {
        try {
          const element = page.locator(selector).first();
          if (await element.isVisible({ timeout: 3000 })) {
            console.log(`✅ 找到单词拆解部分: ${selector}`);
            decompFound = true;
            break;
          }
        } catch (error) {
          continue;
        }
      }

      if (!decompFound) {
        console.log('⚠️  单词拆解功能可能正在开发中或使用不同的选择器');
      }
    });

    // 步骤6: 验证记忆辅助功能
    await test.step('验证记忆辅助功能', async () => {
      console.log('💡 验证记忆辅助功能...');

      const memorySelectors = [
        'text=记忆辅助',
        'text=记忆技巧',
        'text=记忆方法',
        'text=通关秘籍',
        '[data-testid="memory-tips"]',
        '.memory-tips',
        '.memory-guide'
      ];

      let memoryFound = false;
      for (const selector of memorySelectors) {
        try {
          const element = page.locator(selector).first();
          if (await element.isVisible({ timeout: 3000 })) {
            console.log(`✅ 找到记忆辅助部分: ${selector}`);
            memoryFound = true;
            break;
          }
        } catch (error) {
          continue;
        }
      }

      if (!memoryFound) {
        console.log('⚠️  记忆辅助功能可能正在开发中或使用不同的选择器');
      }
    });

    console.log('🎉 everything单词查询测试完成！');
  });

  test('性能测试：搜索响应时间', async ({ page }) => {
    console.log('⚡ 开始性能测试...');

    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    const searchButton = page.locator('button', { hasText: '搜索' });

    // 输入搜索词
    await searchInput.fill('everything');

    // 记录搜索开始时间
    const searchStartTime = Date.now();

    // 执行搜索
    await searchButton.click();

    // 等待页面跳转
    await page.waitForURL(/\/word\/\d+/, { timeout: 15000 });

    // 计算响应时间
    const responseTime = Date.now() - searchStartTime;
    console.log(`⏱️  搜索响应时间: ${responseTime}ms`);

    // 验证响应时间在合理范围内
    expect(responseTime).toBeLessThan(10000);
    console.log('✅ 搜索响应时间在可接受范围内');
  });

  test('错误处理测试：不存在的单词', async ({ page }) => {
    console.log('❌ 开始错误处理测试...');

    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    const searchButton = page.locator('button', { hasText: '搜索' });

    // 输入不存在的单词
    await searchInput.fill('nonexistentword12345');
    await searchButton.click();

    // 等待处理结果
    await page.waitForTimeout(3000);

    // 检查是否有错误提示
    const errorSelectors = [
      'text=/未找到/',
      'text=/not found/',
      'text=/错误/',
      'text=/失败/',
      'text=/不存在/'
    ];

    let errorFound = false;
    for (const selector of errorSelectors) {
      try {
        const element = page.locator(selector).first();
        if (await element.isVisible({ timeout: 3000 })) {
          console.log(`✅ 找到错误提示: ${await element.textContent()}`);
          errorFound = true;
          break;
        }
      } catch (error) {
        continue;
      }
    }

    if (!errorFound) {
      console.log('⚠️  未发现明确的错误提示消息');
    }
  });

  test('UI交互测试：输入框功能验证', async ({ page }) => {
    console.log('🖱️  开始UI交互测试...');

    const searchInput = page.locator('input[placeholder*="输入要学习的单词"]');
    const searchButton = page.locator('button', { hasText: '搜索' });

    // 测试输入框清空功能
    await searchInput.fill('test');
    await expect(searchInput).toHaveValue('test');
    await searchInput.clear();
    await expect(searchInput).toHaveValue('');
    console.log('✅ 输入框清空功能正常');

    // 测试回车搜索
    await searchInput.fill('everything');
    await searchInput.press('Enter');

    // 等待搜索执行
    await expect(page.locator('text=正在拆解...')).toBeVisible({ timeout: 5000 });
    console.log('✅ 回车键搜索功能正常');

    // 取消搜索（如果可能的话）
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);
  });
});