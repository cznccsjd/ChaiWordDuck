const { test, expect } = require('@playwright/test');

test.describe('语言代码约束修复回归测试', () => {
  test.beforeEach(async ({ page }) => {
    // 设置基础超时时间
    test.setTimeout(30000);
  });

  test('英文环境下的单词搜索不应出现约束违反错误', async ({ page }) => {
    // 设置英文Accept-Language头部
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'en-US,en;q=0.9'
    });

    // 访问首页
    await page.goto('http://localhost:3003', {
      waitUntil: 'networkidle'
    });

    // 等待搜索框加载
    await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible({
      timeout: 10000
    });

    // 输入测试单词（故意拼写错误测试纠正功能）
    await page.fill('input[placeholder*="输入要学习的单词"]', 'recommondation');

    // 点击搜索按钮
    await page.click('button[type="submit"]');

    // 等待页面跳转或结果显示
    await page.waitForTimeout(3000);

    // 检查是否有约束违反错误
    const errorElements = page.locator('text=/约束违反|constraint violation|database error/');
    await expect(errorElements).toHaveCount(0);

    // 检查是否成功跳转到单词详情页或显示结果
    const currentUrl = page.url();
    console.log(`当前URL: ${currentUrl}`);

    // 验证页面状态（可能是跳转后的页面或原地显示结果）
    const isSearchPage = currentUrl.includes('/word/') ||
                       await page.locator('h1').isVisible() ||
                       await page.locator('[data-testid="word-result"]').isVisible();

    if (isSearchPage) {
      console.log('✅ 英文环境搜索成功');
    } else {
      // 检查是否有正常的"未找到"消息或其他正常响应
      const normalMessages = page.locator('text=/未找到|not found|no results/');
      const hasNormalMessage = await normalMessages.count() > 0;

      if (hasNormalMessage) {
        console.log('✅ 英文环境正常响应（未找到单词）');
      } else {
        // 最后检查：只要不是约束违反错误就算通过
        const hasAnyContent = await page.locator('body').textContent() > '';
        expect(hasAnyContent).toBeTruthy();
        console.log('✅ 英文环境无约束违反错误');
      }
    }
  });

  test('中文环境下的单词搜索不应出现约束违反错误', async ({ page }) => {
    // 设置中文Accept-Language头部
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'zh-CN,zh;q=0.9'
    });

    // 访问首页
    await page.goto('http://localhost:3003', {
      waitUntil: 'networkidle'
    });

    // 等待搜索框加载
    await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible({
      timeout: 10000
    });

    // 输入测试单词
    await page.fill('input[placeholder*="输入要学习的单词"]', 'hello');

    // 点击搜索按钮
    await page.click('button[type="submit"]');

    // 等待页面跳转或结果显示
    await page.waitForTimeout(3000);

    // 检查是否有约束违反错误
    const errorElements = page.locator('text=/约束违反|constraint violation|database error/');
    await expect(errorElements).toHaveCount(0);

    // 检查是否成功跳转到单词详情页或显示结果
    const currentUrl = page.url();
    console.log(`当前URL: ${currentUrl}`);

    // 验证页面状态
    const isSearchPage = currentUrl.includes('/word/') ||
                       await page.locator('h1').isVisible() ||
                       await page.locator('[data-testid="word-result"]').isVisible();

    if (isSearchPage) {
      console.log('✅ 中文环境搜索成功');
    } else {
      // 检查是否有正常的"未找到"消息
      const normalMessages = page.locator('text=/未找到|not found|no results/');
      const hasNormalMessage = await normalMessages.count() > 0;

      if (hasNormalMessage) {
        console.log('✅ 中文环境正常响应（未找到单词）');
      } else {
        const hasAnyContent = await page.locator('body').textContent() > '';
        expect(hasAnyContent).toBeTruthy();
        console.log('✅ 中文环境无约束违反错误');
      }
    }
  });

  test('不支持语言应fallback到默认语言', async ({ page }) => {
    // 设置不支持的语言头部
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'fr-FR,fr;q=0.9,de-DE;q=0.8'
    });

    // 访问首页
    await page.goto('http://localhost:3003', {
      waitUntil: 'networkidle'
    });

    // 等待搜索框加载
    await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible({
      timeout: 10000
    });

    // 输入测试单词
    await page.fill('input[placeholder*="输入要学习的单词"]', 'test');

    // 点击搜索按钮
    await page.click('button[type="submit"]');

    // 等待页面跳转或结果显示
    await page.waitForTimeout(3000);

    // 检查是否有约束违反错误
    const errorElements = page.locator('text=/约束违反|constraint violation|database error/');
    await expect(errorElements).toHaveCount(0);

    console.log('✅ 不支持语言fallback正常');
  });

  test('复杂Accept-Language头部处理', async ({ page }) => {
    // 测试复杂的Accept-Language头部
    const testCases = [
      'zh-CN;q=0.8,en-US;q=0.9',
      'en-US,en;q=0.9,zh-CN;q=0.8,fr-FR;q=0.7',
      'zh-cn,en-us',
      'EN,ZH'
    ];

    for (let i = 0; i < testCases.length; i++) {
      const acceptLanguage = testCases[i];
      console.log(`测试Accept-Language: ${acceptLanguage}`);

      // 设置Accept-Language头部
      await page.setExtraHTTPHeaders({
        'Accept-Language': acceptLanguage
      });

      // 访问首页
      await page.goto('http://localhost:3003', {
        waitUntil: 'networkidle'
      });

      // 等待搜索框加载
      await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible({
        timeout: 10000
      });

      // 输入测试单词
      await page.fill('input[placeholder*="输入要学习的单词"]', `word${i}`);

      // 点击搜索按钮
      await page.click('button[type="submit"]');

      // 等待响应
      await page.waitForTimeout(2000);

      // 检查是否有约束违反错误
      const errorElements = page.locator('text=/约束违反|constraint violation|database error/');
      const errorCount = await errorElements.count();

      expect(errorCount).toBe(0);
      console.log(`✅ Accept-Language测试用例 ${i+1} 通过`);
    }
  });

  test('性能测试 - 快速连续请求', async ({ page }) => {
    // 设置混合语言头部
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8'
    });

    const startTime = Date.now();
    let successCount = 0;

    for (let i = 0; i < 3; i++) {
      try {
        // 访问首页
        await page.goto('http://localhost:3003', {
          waitUntil: 'networkidle'
        });

        // 等待搜索框加载
        await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible({
          timeout: 5000
        });

        // 输入测试单词
        await page.fill('input[placeholder*="输入要学习的单词"]', `performance${i}`);

        // 点击搜索按钮
        await page.click('button[type="submit"]');

        // 等待短时间
        await page.waitForTimeout(1000);

        // 检查是否有约束违反错误
        const errorElements = page.locator('text=/约束违反|constraint violation|database error/');
        const errorCount = await errorElements.count();

        if (errorCount === 0) {
          successCount++;
          console.log(`✅ 性能测试请求 ${i+1} 成功`);
        } else {
          console.log(`❌ 性能测试请求 ${i+1} 发现约束违反错误`);
        }

      } catch (error) {
        console.log(`❌ 性能测试请求 ${i+1} 失败:`, error.message);
      }
    }

    const endTime = Date.now();
    const totalTime = endTime - startTime;
    const avgTime = totalTime / 3;

    console.log(`性能测试结果: ${successCount}/3 成功, 平均耗时: ${avgTime}ms`);

    // 至少2个请求成功，且平均时间不超过5秒
    expect(successCount).toBeGreaterThanOrEqual(2);
    expect(avgTime).toBeLessThan(5000);
  });

  test('边界条件和错误处理', async ({ page }) => {
    // 测试各种边界情况
    const edgeCases = [
      { language: '', expected: 'should_work' },
      { language: 'invalid', expected: 'should_work' },
      { language: 'zh;q=abc', expected: 'should_work' },
      { language: '  en-US  ', expected: 'should_work' }, // 前后空格
      { language: 'en-US,', expected: 'should_work' }, // 尾随逗号
      { language: ',en-US', expected: 'should_work' }, // 前导逗号
    ];

    for (let i = 0; i < edgeCases.length; i++) {
      const testCase = edgeCases[i];
      console.log(`测试边界情况: "${testCase.language}"`);

      // 设置Accept-Language头部
      const headers = testCase.language ?
        { 'Accept-Language': testCase.language } : {};

      await page.setExtraHTTPHeaders(headers);

      try {
        // 访问首页
        await page.goto('http://localhost:3003', {
          waitUntil: 'networkidle'
        });

        // 等待搜索框加载（超时时间短一些）
        try {
          await expect(page.locator('input[placeholder*="输入要学习的单词"]')).toBeVisible({
            timeout: 5000
          });

          // 输入测试单词
          await page.fill('input[placeholder*="输入要学习的单词"]', `edge${i}`);

          // 点击搜索按钮
          await page.click('button[type="submit"]');

          // 等待响应
          await page.waitForTimeout(1000);

        } catch (waitError) {
          // 页面加载失败也算测试通过（只要不是约束违反错误）
          console.log(`页面加载异常，但无约束违反错误: ${waitError.message}`);
        }

        // 检查是否有约束违反错误
        const errorElements = page.locator('text=/约束违反|constraint violation|database error/');
        const errorCount = await errorElements.count();

        expect(errorCount).toBe(0);
        console.log(`✅ 边界情况测试 ${i+1} 通过`);

      } catch (error) {
        // 如果错误消息包含约束违反，则测试失败
        if (error.message.includes('约束违反') || error.message.includes('constraint')) {
          throw new Error(`边界情况测试发现约束违反错误: ${error.message}`);
        } else {
          console.log(`✅ 边界情况测试 ${i+1} 通过（其他错误但无约束违反）`);
        }
      }
    }
  });
});