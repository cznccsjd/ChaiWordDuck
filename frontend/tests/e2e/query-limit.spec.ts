import { test, expect } from '@playwright/test';
import { TestHelpers } from './helpers/test-helpers';
import { TEST_WORDS, TEST_USERS, TIME_CONFIG, ERROR_MESSAGES } from './fixtures/test-data';

/**
 * 用户查询限制功能测试
 * 测试游客模式的查询次数限制和提示功能
 */

test.describe('用户查询限制功能测试', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
    await page.goto('/');
    await helpers.waitForPageLoad();
  });

  test('游客用户查询限制验证', async ({ page }) => {
    console.log('🚫 开始测试游客用户查询限制...');

    const guestUser = TEST_USERS.GUEST;
    const testWords = [
      TEST_WORDS.SIMPLE.word,
      TEST_WORDS.LONG_WORDS[0].word,
      TEST_WORDS.LONG_WORDS[1].word,
      TEST_WORDS.LONG_WORDS[2].word // 这应该触发限制
    ];

    let queryCount = 0;
    let limitReached = false;

    for (let i = 0; i < testWords.length; i++) {
      const word = testWords[i];
      queryCount++;
      console.log(`执行第${queryCount}次查询: ${word}`);

      // 清理之前的状态
      if (i > 0) {
        await helpers.cleanup();
      }

      // 执行查询
      const startTime = Date.now();
      const success = await helpers.runCompleteWordTest(word);
      const totalTime = Date.now() - startTime;

      console.log(`第${queryCount}次查询结果: ${success ? '成功' : '失败'} (${totalTime}ms)`);

      // 检查是否显示查询限制提示
      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT); // 等待UI更新
      await helpers.verifyGuestQueryLimit();

      // 检查页面内容，看是否有限制相关的提示
      const limitTexts = [
        '查询次数已达限制',
        '注册账号获得更多',
        '每日查询限制',
        '游客限制',
        '请注册'
      ];

      let limitDetected = false;
      for (const text of limitTexts) {
        const element = page.locator(`text=${text}`);
        if (await element.count() > 0) {
          limitDetected = true;
          limitReached = true;
          console.log(`🚫 [E2E] 检测到限制提示: ${text}`);
          break;
        }
      }

      // 截图保存每次查询的结果
      await page.screenshot({
        path: `test-results/query-limit-test-${queryCount}-${limitDetected ? 'limited' : 'allowed'}.png`,
        fullPage: false
      });

      // 如果检测到限制，记录并跳出循环
      if (limitDetected) {
        console.log(`✅ [E2E] 查询限制在第${queryCount}次查询时触发`);
        break;
      }

      // 等待状态稳定
      await page.waitForTimeout(TIME_CONFIG.MEDIUM_WAIT);
    }

    // 验证查询限制逻辑
    console.log(`📊 查询限制测试总结:`);
    console.log(`  - 总查询次数: ${queryCount}`);
    console.log(`  - 限制是否触发: ${limitReached ? '是' : '否'}`);
    console.log(`  - 预期限制次数: ${guestUser.expected_queries_limit}`);

    // 记录测试结果到文件
    const testResult = {
      timestamp: new Date().toISOString(),
      totalQueries: queryCount,
      limitReached: limitReached,
      expectedLimit: guestUser.expected_queries_limit,
      testPassed: limitReached && queryCount <= guestUser.expected_queries_limit + 1
    };

    console.log('✅ 游客用户查询限制测试完成', testResult);
  });

  test('查询限制提示信息验证', async ({ page }) => {
    console.log('💬 开始测试查询限制提示信息...');

    // 快速消耗查询次数（使用简单单词）
    const quickWords = [TEST_WORDS.SIMPLE.word, 'test', 'demo'];

    for (let i = 0; i < quickWords.length; i++) {
      const word = quickWords[i];
      console.log(`快速查询 ${i + 1}: ${word}`);

      await helpers.cleanup();
      await helpers.submitWord(word);
      await helpers.waitForAIResponse();
      await helpers.verifyWordDecomposition(word);

      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
    }

    // 现在尝试查询一个长单词，很可能会触发限制
    const longWord = TEST_WORDS.LONG_WORDS[0].word;
    console.log(`尝试查询长单词（预期触发限制）: ${longWord}`);

    await helpers.cleanup();
    await helpers.submitWord(longWord);

    // 等待响应和可能的限制提示
    await page.waitForTimeout(TIME_CONFIG.MEDIUM_WAIT);

    // 检查具体的限制提示内容
    const expectedMessages = [
      ERROR_MESSAGES.RATE_LIMIT,
      '查询次数已达限制',
      '注册账号',
      '每日3次',
      '游客用户'
    ];

    let foundMessages = [];
    for (const message of expectedMessages) {
      const element = page.locator(`text=${message}`);
      if (await element.count() > 0) {
        foundMessages.push(message);
        console.log(`✅ [E2E] 找到限制提示: ${message}`);
      }
    }

    // 检查是否有引导用户注册的链接或按钮
    const registerElements = [
      page.getByRole('link', { name: '注册' }),
      page.getByRole('button', { name: '注册' }),
      page.locator('a[href="/register"]')
    ];

    for (const element of registerElements) {
      if (await element.count() > 0) {
        console.log(`✅ [E2E] 找到注册引导元素`);
        break;
      }
    }

    // 截图保存限制提示状态
    await page.screenshot({
      path: 'test-results/query-limit-message-detail.png',
      fullPage: false
    });

    console.log(`📝 找到的限制提示信息:`, foundMessages);
    console.log('✅ 查询限制提示信息验证完成');
  });

  test('页面刷新后查询限制保持测试', async ({ page }) => {
    console.log('🔄 开始测试页面刷新后查询限制保持...');

    // 执行几次查询
    const initialQueries = [TEST_WORDS.SIMPLE.word, TEST_WORDS.LONG_WORDS[0].word];

    for (const word of initialQueries) {
      console.log(`初始查询: ${word}`);
      await helpers.cleanup();
      await helpers.submitWord(word);
      await helpers.waitForAIResponse();
      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
    }

    // 刷新页面
    console.log('刷新页面...');
    await page.reload();
    await helpers.waitForPageLoad();

    // 再次查询，验证限制是否仍然有效
    console.log('页面刷新后继续查询...');
    await helpers.submitWord(TEST_WORDS.LONG_WORDS[1].word);
    await helpers.waitForAIResponse();

    // 检查是否还有查询限制
    await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
    await helpers.verifyGuestQueryLimit();

    console.log('✅ 页面刷新后查询限制保持测试完成');
  });

  test('查询限制友好性验证', async ({ page }) => {
    console.log('😊 开始测试查询限制友好性...');

    // 快速消耗查询次数
    for (let i = 0; i < 3; i++) {
      const word = `test${i}`;
      console.log(`消耗查询次数 ${i + 1}: ${word}`);

      await helpers.cleanup();
      await helpers.submitWord(word);
      await helpers.waitForAIResponse();
      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
    }

    // 尝试第4次查询
    console.log('尝试第4次查询（预期触发限制）...');
    await helpers.cleanup();
    await helpers.submitWord(TEST_WORDS.LONG_WORDS[0].word);

    // 等待限制响应
    await page.waitForTimeout(TIME_CONFIG.MEDIUM_WAIT);

    // 验证限制提示是否友好（不显示技术错误，而是用户友好的提示）
    const unfriendlyMessages = [
      '500',
      'Internal Server Error',
      'Rate limit exceeded',
      'API error',
      'Database error'
    ];

    const friendlyMessages = [
      '注册账号',
      '更多查询机会',
      '每日查询',
      '请注册',
      '游客限制'
    ];

    let hasUnfriendly = false;
    let hasFriendly = false;

    for (const message of unfriendlyMessages) {
      if (await page.locator(`text=${message}`).count() > 0) {
        hasUnfriendly = true;
        console.log(`❌ [E2E] 发现不友好的错误消息: ${message}`);
      }
    }

    for (const message of friendlyMessages) {
      if (await page.locator(`text=${message}`).count() > 0) {
        hasFriendly = true;
        console.log(`✅ [E2E] 发现友好的提示消息: ${message}`);
      }
    }

    // 验证友好的UI元素
    const friendlyUI = [
      '🦆', // 鸭子表情
      '😊', // 表情符号
      '💡', // 提示符号
      '✓', // 勾选符号
      '立即注册',
      '了解更多'
    ];

    for (const ui of friendlyUI) {
      if (await page.locator(`text=${ui}`).count() > 0) {
        console.log(`✅ [E2E] 发现友好的UI元素: ${ui}`);
      }
    }

    // 截图保存友好性测试结果
    await page.screenshot({
      path: 'test-results/query-limit-friendliness.png',
      fullPage: false
    });

    // 验证结果
    expect(hasUnfriendly).toBe(false);
    expect(hasFriendly).toBe(true);

    console.log('✅ 查询限制友好性验证完成');
  });

  test('查询计数显示验证', async ({ page }) => {
    console.log('🔢 开始测试查询计数显示...');

    // 检查页面是否显示剩余查询次数
    const countSelectors = [
      'text=/查询次数/',
      'text=/剩余/',
      'text=/\\d+次/',
      'text=/今日/',
      '[data-testid="query-count"]'
    ];

    let countDisplayFound = false;
    for (const selector of countSelectors) {
      const element = page.locator(selector);
      if (await element.count() > 0) {
        countDisplayFound = true;
        console.log(`✅ [E2E] 找到查询计数显示: ${selector}`);
        break;
      }
    }

    // 执行一次查询后，检查计数是否更新
    console.log('执行查询并检查计数更新...');
    await helpers.submitWord(TEST_WORDS.SIMPLE.word);
    await helpers.waitForAIResponse();
    await page.waitForTimeout(TIME_CONFIG.MEDIUM_WAIT);

    // 再次检查计数显示
    for (const selector of countSelectors) {
      const element = page.locator(selector);
      if (await element.count() > 0) {
        const text = await element.textContent();
        console.log(`📊 [E2E] 查询计数显示: ${text}`);
        break;
      }
    }

    console.log(`查询计数显示${countDisplayFound ? '已找到' : '未找到'}`);
    console.log('✅ 查询计数显示验证完成');
  });

  test('限制后的行为验证', async ({ page }) => {
    console.log('⏹️ 开始测试限制后的用户行为...');

    // 消耗查询次数
    const wordsToConsume = ['word1', 'word2', 'word3'];

    for (const word of wordsToConsume) {
      await helpers.cleanup();
      await helpers.submitWord(word);
      await helpers.waitForAIResponse();
      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
    }

    // 尝试超出限制的查询
    console.log('尝试超出限制的查询...');
    await helpers.cleanup();
    await helpers.submitWord(TEST_WORDS.LONG_WORDS[0].word);
    await page.waitForTimeout(TIME_CONFIG.MEDIUM_WAIT);

    // 验证限制后的页面状态
    const afterLimitChecks = [
      { name: '输入框是否仍然可用', selector: 'input[placeholder*="单词"]', shouldExist: true },
      { name: '提交按钮是否仍然可用', selector: 'button:has-text("拆解")', shouldExist: true },
      { name: '注册链接是否突出显示', selector: 'a[href="/register"]', shouldExist: true },
      { name: '登录链接是否仍然可用', selector: 'a[href="/login"]', shouldExist: true }
    ];

    for (const check of afterLimitChecks) {
      const element = page.locator(check.selector);
      const exists = await element.count() > 0;
      console.log(`${check.name}: ${exists ? '是' : '否'}`);
    }

    // 尝试点击注册链接
    const registerLink = page.locator('a[href="/register"]');
    if (await registerLink.count() > 0) {
      console.log('点击注册链接...');
      await registerLink.click();
      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);

      // 验证是否跳转到注册页面
      const currentUrl = page.url();
      if (currentUrl.includes('/register')) {
        console.log('✅ [E2E] 成功跳转到注册页面');
      } else {
        console.log('⚠️ [E2E] 未能跳转到注册页面');
      }

      // 返回首页继续测试
      await page.goto('/');
      await helpers.waitForPageLoad();
    }

    console.log('✅ 限制后的行为验证完成');
  });
});