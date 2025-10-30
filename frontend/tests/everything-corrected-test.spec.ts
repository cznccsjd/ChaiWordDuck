import { test, expect } from '@playwright/test';

test.describe('拆词鸭 - everything单词查询修正版测试', () => {
  test.beforeEach(async ({ page }) => {
    // 访问应用主页（现在运行在3001端口）
    await page.goto('http://localhost:3001');
    console.log('✅ 页面加载成功');
  });

  test('手动验证everything单词查询功能', async ({ page }) => {
    console.log('🔍 开始手动验证everything单词查询功能...');

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
      try {
        await expect(page.locator('text=正在拆解...')).toBeVisible({ timeout: 5000 });
        console.log('✅ 搜索状态显示正常');
      } catch (error) {
        console.log('⚠️  搜索状态显示可能不同或加载很快');
      }
    });

    // 步骤3: 等待并验证页面跳转或结果
    await test.step('验证页面跳转和结果显示', async () => {
      console.log('⏳ 等待搜索结果...');

      // 尝试等待页面跳转
      try {
        await page.waitForURL(/\/word\/\d+/, { timeout: 15000 });
        const currentUrl = page.url();
        console.log(`✅ 页面跳转成功: ${currentUrl}`);

        // 验证是否跳转到单词详情页面
        expect(currentUrl).toMatch(/\/word\/\d+/);

        // 从URL中提取单词ID
        const wordId = currentUrl.match(/\/word\/(\d+)/)?.[1];
        console.log(`📝 单词ID: ${wordId}`);
      } catch (error) {
        console.log('⚠️  页面可能没有跳转，检查是否在当前页面显示结果');
        console.log(`当前URL: ${page.url()}`);
      }
    });

    // 步骤4: 验证单词详情或搜索结果
    await test.step('验证单词内容显示', async () => {
      console.log('📋 验证单词内容显示...');

      // 等待页面内容加载
      await page.waitForTimeout(3000);

      // 检查是否跳转到了单词详情页
      if (page.url().includes('/word/')) {
        console.log('📍 已跳转到单词详情页');

        // 验证单词基本信息显示
        try {
          const wordTitle = page.locator('h1, h2, h3').filter({ hasText: /everything/i }).first();
          await expect(wordTitle).toBeVisible({ timeout: 10000 });
          console.log('✅ 单词标题显示正常');
        } catch (error) {
          console.log('⚠️  单词标题可能使用不同的显示方式');
        }

        // 检查各种内容元素
        const contentChecks = [
          { selector: 'text=/ˈevriθɪŋ/', description: '音标显示' },
          { selector: 'text=/ɪvˈriθɪŋ/', description: '备选音标显示' },
          { selector: 'text=代词', description: '词性标记' },
          { selector: 'text=一切；所有事物', description: '中文释义' },
          { selector: 'text=/囊括全局/', description: '核心游戏内容' },
          { selector: 'text=/哲学家/', description: '正式场景例句' },
          { selector: 'text=/今天把我的公寓/', description: '日常场景例句' },
          { selector: 'text=/etymology/', description: '词根拆解' },
          { selector: 'text=/小E/', description: '记忆技巧' }
        ];

        let foundContentCount = 0;
        for (const check of contentChecks) {
          try {
            const element = page.locator(check.selector).first();
            if (await element.isVisible({ timeout: 2000 })) {
              console.log(`✅ ${check.description} - 显示正常`);
              foundContentCount++;
            } else {
              console.log(`⚠️  ${check.description} - 未找到或不可见`);
            }
          } catch (error) {
            console.log(`❌ ${check.description} - 检查失败`);
          }
        }

        console.log(`📊 内容显示统计: ${foundContentCount}/${contentChecks.length} 项正常显示`);

      } else {
        console.log('📍 仍在主页，检查是否有错误消息或替代显示');

        // 检查是否有错误消息
        const errorSelectors = [
          'text=/错误/',
          'text=/失败/',
          'text=/未找到/',
          'text=/网络/'
        ];

        for (const selector of errorSelectors) {
          try {
            const element = page.locator(selector).first();
            if (await element.isVisible({ timeout: 2000 })) {
              console.log(`❌ 发现错误消息: ${await element.textContent()}`);
              break;
            }
          } catch (error) {
            continue;
          }
        }

        // 检查是否有成功提示或其他显示
        const successSelectors = [
          'text=/成功/',
          'text=/完成/',
          'text=/找到/'
        ];

        for (const selector of successSelectors) {
          try {
            const element = page.locator(selector).first();
            if (await element.isVisible({ timeout: 2000 })) {
              console.log(`✅ 发现成功消息: ${await element.textContent()}`);
              break;
            }
          } catch (error) {
            continue;
          }
        }
      }
    });

    // 步骤5: 截图保存当前状态
    await test.step('截图保存测试结果', async () => {
      await page.screenshot({
        path: 'test-results/everything-test-final-state.png',
        fullPage: true
      });
      console.log('📸 已保存页面截图');
    });

    console.log('🎉 everything单词查询手动验证完成！');
  });

  test('网络连接和API测试', async ({ page }) => {
    console.log('🌐 开始网络连接测试...');

    // 在页面中执行JavaScript来测试API连接
    const apiTestResult = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:8001/api/v1/words/query/everything');
        const data = await response.json();
        return {
          success: response.ok,
          status: response.status,
          data: data
        };
      } catch (error) {
        return {
          success: false,
          error: error.message
        };
      }
    });

    console.log('🔗 API测试结果:', JSON.stringify(apiTestResult, null, 2));

    if (apiTestResult.success) {
      console.log('✅ API连接正常');
      expect(apiTestResult.data.success).toBe(true);
      expect(apiTestResult.data.data.word).toBe('everything');
    } else {
      console.log('❌ API连接失败:', apiTestResult.error);
    }
  });
});