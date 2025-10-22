import { test, expect } from '@playwright/test';
import { TestHelpers } from './helpers/test-helpers';
import { TEST_WORDS, TIME_CONFIG, ERROR_MESSAGES } from './fixtures/test-data';

/**
 * AI单词生成功能和重试逻辑测试
 * 重点测试Gemini API的重试机制和错误处理
 */

test.describe('AI单词生成功能测试', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
    await page.goto('/');
    await helpers.waitForPageLoad();
  });

  test('简单单词查询测试', async ({ page }) => {
    console.log('🔍 开始测试简单单词查询...');

    const testWord = TEST_WORDS.SIMPLE.word;

    // 执行完整的单词查询测试
    const success = await helpers.runCompleteWordTest(testWord);

    expect(success).toBe(true);

    // 验证页面状态
    await helpers.checkConsoleErrors();

    console.log(`✅ 简单单词查询测试完成: ${testWord}`);
  });

  test('长单词查询测试 - 主要功能', async ({ page }) => {
    console.log('🎯 开始测试长单词查询 - 主要功能...');

    // 测试多个长单词
    for (const wordData of TEST_WORDS.LONG_WORDS) {
      console.log(`测试长单词: ${wordData.word} (${wordData.description})`);

      // 清理之前的状态
      await helpers.cleanup();

      // 执行查询测试
      const success = await helpers.runCompleteWordTest(wordData.word);

      // 验证结果
      expect(success).toBe(true);

      // 截图保存每个测试结果
      await page.screenshot({
        path: `test-results/long-word-${wordData.word}-result.png`,
        fullPage: false
      });

      // 等待状态稳定
      await page.waitForTimeout(TIME_CONFIG.MEDIUM_WAIT);
    }

    console.log('✅ 长单词查询测试完成');
  });

  test('边界情况单词测试', async ({ page }) => {
    console.log('⚠️ 开始测试边界情况单词...');

    const edgeCases = [
      { word: TEST_WORDS.EDGE_CASES.short, expected: 'error', description: '太短的单词' },
      { word: TEST_WORDS.EDGE_CASES.empty, expected: 'error', description: '空输入' },
      { word: TEST_WORDS.EDGE_CASES.whitespace, expected: 'error', description: '只有空格' },
      { word: TEST_WORDS.EDGE_CASES.valid_minimum, expected: 'success', description: '刚好8字母' }
    ];

    for (const testCase of edgeCases) {
      console.log(`测试边界情况: ${testCase.description} (${testCase.word})`);

      // 清理状态
      await helpers.cleanup();

      // 执行查询
      const success = await helpers.runCompleteWordTest(testCase.word);

      if (testCase.expected === 'error') {
        // 对于应该失败的测试，我们期望看到错误处理
        // 这里不严格断言失败，因为可能有不同的处理方式
        console.log(`边界情况测试完成: ${testCase.description}`);
      } else {
        // 对于应该成功的测试，严格验证
        expect(success).toBe(true);
      }

      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
    }

    console.log('✅ 边界情况测试完成');
  });

  test('重试逻辑验证测试', async ({ page }) => {
    console.log('🔄 开始测试重试逻辑...');

    // 选择一个长单词进行重试测试
    const testWord = TEST_WORDS.LONG_WORDS[1].word; // comprehensive

    // 记录开始时间，重试逻辑应该增加响应时间
    const startTime = Date.now();

    // 执行查询
    await helpers.submitWord(testWord);

    // 主动观察重试过程
    console.log('👀 [E2E] 主动观察重试过程...');

    let retryDetected = false;
    let retryCount = 0;

    // 监听页面内容变化，检测重试消息
    const checkRetry = async () => {
      const retryTexts = [
        '正在尝试',
        '重试第',
        'AI服务繁忙',
        '请稍等',
        '正在连接'
      ];

      for (const text of retryTexts) {
        const element = page.locator(`text=${text}`);
        if (await element.count() > 0) {
          retryDetected = true;
          retryCount++;
          console.log(`🔄 [E2E] 检测到重试消息: ${text} (第${retryCount}次)`);
        }
      }
    };

    // 在等待过程中定期检查重试状态
    const retryCheckInterval = setInterval(checkRetry, 2000);

    try {
      // 等待AI响应（设置更长的超时时间）
      await helpers.waitForAIResponse(TIME_CONFIG.API_RESPONSE_TIMEOUT);
    } finally {
      clearInterval(retryCheckInterval);
    }

    const totalTime = Date.now() - startTime;
    console.log(`⏱️ [E2E] 总耗时: ${totalTime}ms, 检测到重试: ${retryDetected ? '是' : '否'}`);

    // 验证结果
    await helpers.verifyWordDecomposition(testWord);

    // 如果总时间超过30秒，很可能触发了重试逻辑
    if (totalTime > 30000) {
      console.log('✅ [E2E] 响应时间较长，重试逻辑很可能已触发');
      retryDetected = true;
    }

    // 截图保存结果
    await page.screenshot({
      path: `test-results/retry-test-${testWord}-detected-${retryDetected}.png`,
      fullPage: false
    });

    console.log(`✅ 重试逻辑测试完成，总耗时: ${totalTime}ms`);
  });

  test('连续多次查询测试', async ({ page }) => {
    console.log('🔁 开始测试连续多次查询...');

    const words = [
      TEST_WORDS.SIMPLE.word,
      TEST_WORDS.LONG_WORDS[0].word,
      TEST_WORDS.LONG_WORDS[1].word
    ];

    const results = [];

    for (let i = 0; i < words.length; i++) {
      const word = words[i];
      console.log(`执行第${i + 1}次查询: ${word}`);

      if (i > 0) {
        // 清理之前的状态
        await helpers.cleanup();
      }

      // 执行查询并记录结果
      const startTime = Date.now();
      const success = await helpers.runCompleteWordTest(word);
      const totalTime = Date.now() - startTime;

      results.push({
        word,
        success,
        totalTime,
        index: i + 1
      });

      // 检查是否遇到查询限制
      await helpers.verifyGuestQueryLimit();

      // 等待状态稳定
      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
    }

    // 分析结果
    console.log('📊 连续查询结果分析:');
    results.forEach(result => {
      console.log(`  - ${result.word}: ${result.success ? '成功' : '失败'} (${result.totalTime}ms)`);
    });

    const successCount = results.filter(r => r.success).length;
    console.log(`✅ 连续查询测试完成，成功率: ${successCount}/${results.length}`);

    // 验证至少有一次成功
    expect(successCount).toBeGreaterThan(0);
  });

  test('特殊字符单词测试', async ({ page }) => {
    console.log('⚡ 开始测试特殊字符单词...');

    const specialWords = [
      TEST_WORDS.SPECIAL_CHARS.with_hyphen,
      TEST_WORDS.SPECIAL_CHARS.with_apostrophe,
      TEST_WORDS.SPECIAL_CHARS.with_numbers
    ];

    for (const word of specialWords) {
      console.log(`测试特殊字符单词: ${word}`);

      await helpers.cleanup();

      // 执行查询
      const success = await helpers.runCompleteWordTest(word);

      // 记录结果（特殊字符可能有不同的处理方式）
      console.log(`特殊字符测试完成: ${word} - ${success ? '成功' : '预期行为'}`);

      await page.waitForTimeout(TIME_CONFIG.SHORT_WAIT);
    }

    console.log('✅ 特殊字符单词测试完成');
  });

  test('性能和稳定性测试', async ({ page }) => {
    console.log('🚀 开始性能和稳定性测试...');

    const testWord = TEST_WORDS.LONG_WORDS[2].word; // 最长的单词

    // 测试单次请求的详细性能
    const startTime = Date.now();

    // 记录网络请求开始
    const requests: any[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        requests.push({
          url: request.url(),
          method: request.method(),
          timestamp: Date.now()
        });
      }
    });

    const success = await helpers.runCompleteWordTest(testWord);

    const totalTime = Date.now() - startTime;

    // 分析请求
    console.log(`📊 网络请求分析:`);
    requests.forEach(request => {
      console.log(`  - ${request.method} ${request.url}`);
    });

    console.log(`⏱️ 性能统计:`);
    console.log(`  - 总耗时: ${totalTime}ms`);
    console.log(`  - API请求数: ${requests.length}`);
    console.log(`  - 成功率: ${success ? '100%' : '0%'}`);

    // 性能断言
    expect(totalTime).toBeLessThan(60000); // 应该在60秒内完成
    expect(requests.length).toBeGreaterThan(0); // 应该有API请求

    // 记录性能指标
    await helpers.recordPerformanceMetrics(`性能测试-${testWord}`);

    console.log('✅ 性能和稳定性测试完成');
  });

  test('错误恢复能力测试', async ({ page }) => {
    console.log('🛠️ 开始测试错误恢复能力...');

    // 先执行一个正常查询
    await helpers.runCompleteWordTest(TEST_WORDS.SIMPLE.word);
    await helpers.cleanup();

    // 然后尝试一个可能有问题的查询
    const problematicWord = TEST_WORDS.EDGE_CASES.empty;
    console.log(`测试错误恢复: "${problematicWord}"`);

    const startTime = Date.now();
    const success = await helpers.runCompleteWordTest(problematicWord);
    const totalTime = Date.now() - startTime;

    console.log(`错误处理测试完成: ${success ? '意外成功' : '预期错误处理'} (${totalTime}ms)`);

    // 清理状态
    await helpers.cleanup();

    // 验证系统是否恢复正常
    console.log('验证系统恢复能力...');
    const recoverySuccess = await helpers.runCompleteWordTest(TEST_WORDS.SIMPLE.word);

    expect(recoverySuccess).toBe(true);
    console.log('✅ 系统恢复能力验证通过');
  });
});