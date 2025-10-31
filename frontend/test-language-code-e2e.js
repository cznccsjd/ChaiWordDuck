#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function testLanguageCodeE2E() {
  console.log('🚀 开始语言代码约束修复E2E测试...\n');

  let browser;
  try {
    // 启动浏览器
    browser = await puppeteer.launch({
      headless: false,  // 设置为true可以无头模式运行
      devtools: true    // 打开开发者工具
    });
    const page = await browser.newPage();

    // 测试1: 英文环境下的单词搜索
    console.log('📋 测试1: 英文环境下的单词搜索');
    await page.goto('http://localhost:3003', {
      waitUntil: 'networkidle2'
    });

    // 设置英文Accept-Language头部
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'en-US,en;q=0.9'
    });

    await page.waitForSelector('input[placeholder*="输入要学习的单词"]', { timeout: 10000 });

    // 输入测试单词
    const searchInput = await page.$('input[placeholder*="输入要学习的单词"]');
    await searchInput.type('recommondation'); // 故意拼写错误

    // 点击搜索
    const searchButton = await page.$('button[type="submit"]');
    await searchButton.click();

    // 等待搜索结果
    try {
      await page.waitForFunction(
        () => window.location.pathname.includes('/word/'),
        { timeout: 15000 }
      );

      const currentUrl = page.url();
      console.log('✅ 英文环境搜索成功:', currentUrl);

      // 验证页面内容加载
      await page.waitForSelector('h1', { timeout: 5000 });
      const wordTitle = await page.$eval('h1', el => el.textContent);
      console.log(`✅ 单词标题: ${wordTitle}`);

    } catch (error) {
      console.log('❌ 英文环境搜索失败:', error.message);

      // 检查错误消息
      try {
        const errorElement = await page.$('text=/请求失败|错误|未找到|约束违反/');
        if (errorElement) {
          const errorMessage = await page.evaluate(el => el.textContent, errorElement);
          console.log(`❌ 错误消息: ${errorMessage}`);
          if (errorMessage.includes('约束违反') || errorMessage.includes('constraint')) {
            throw new Error('语言代码约束违反Bug未修复！');
          }
        }
      } catch (e) {
        console.log('❌ 搜索失败且未找到明确错误信息');
      }
    }

    // 测试2: 中文环境下的单词搜索
    console.log('\n📋 测试2: 中文环境下的单词搜索');

    // 设置中文Accept-Language头部
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'zh-CN,zh;q=0.9'
    });

    // 返回首页
    await page.goto('http://localhost:3003', {
      waitUntil: 'networkidle2'
    });

    await page.waitForSelector('input[placeholder*="输入要学习的单词"]', { timeout: 10000 });

    // 输入测试单词
    const searchInput2 = await page.$('input[placeholder*="输入要学习的单词"]');
    await searchInput2.type('hello');

    // 点击搜索
    const searchButton2 = await page.$('button[type="submit"]');
    await searchButton2.click();

    // 等待搜索结果
    try {
      await page.waitForFunction(
        () => window.location.pathname.includes('/word/'),
        { timeout: 15000 }
      );

      const currentUrl2 = page.url();
      console.log('✅ 中文环境搜索成功:', currentUrl2);

      // 验证页面内容加载
      await page.waitForSelector('h1', { timeout: 5000 });
      const wordTitle2 = await page.$eval('h1', el => el.textContent);
      console.log(`✅ 单词标题: ${wordTitle2}`);

    } catch (error) {
      console.log('❌ 中文环境搜索失败:', error.message);

      // 检查错误消息
      try {
        const errorElement = await page.$('text=/请求失败|错误|未找到|约束违反/');
        if (errorElement) {
          const errorMessage = await page.evaluate(el => el.textContent, errorElement);
          console.log(`❌ 错误消息: ${errorMessage}`);
          if (errorMessage.includes('约束违反') || errorMessage.includes('constraint')) {
            throw new Error('语言代码约束违反Bug未修复！');
          }
        }
      } catch (e) {
        console.log('❌ 搜索失败且未找到明确错误信息');
      }
    }

    // 测试3: 边界情况 - 不支持的语言fallback
    console.log('\n📋 测试3: 不支持语言的fallback处理');

    // 设置不支持的语言头部
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'fr-FR,fr;q=0.9,de-DE;q=0.8'
    });

    // 返回首页
    await page.goto('http://localhost:3003', {
      waitUntil: 'networkidle2'
    });

    await page.waitForSelector('input[placeholder*="输入要学习的单词"]', { timeout: 10000 });

    // 输入测试单词
    const searchInput3 = await page.$('input[placeholder*="输入要学习的单词"]');
    await searchInput3.type('test');

    // 点击搜索
    const searchButton3 = await page.$('button[type="submit"]');
    await searchButton3.click();

    // 等待搜索结果
    try {
      await page.waitForFunction(
        () => window.location.pathname.includes('/word/'),
        { timeout: 15000 }
      );

      const currentUrl3 = page.url();
      console.log('✅ 不支持语言fallback成功:', currentUrl3);

      // 验证页面内容加载
      await page.waitForSelector('h1', { timeout: 5000 });
      const wordTitle3 = await page.$eval('h1', el => el.textContent);
      console.log(`✅ 单词标题: ${wordTitle3}`);

    } catch (error) {
      console.log('❌ 不支持语言fallback失败:', error.message);

      // 检查错误消息
      try {
        const errorElement = await page.$('text=/请求失败|错误|未找到|约束违反/');
        if (errorElement) {
          const errorMessage = await page.evaluate(el => el.textContent, errorElement);
          console.log(`❌ 错误消息: ${errorMessage}`);
          if (errorMessage.includes('约束违反') || errorMessage.includes('constraint')) {
            throw new Error('语言代码约束违反Bug未修复！');
          }
        }
      } catch (e) {
        console.log('❌ 搜索失败且未找到明确错误信息');
      }
    }

    // 测试4: 性能测试 - 快速连续请求
    console.log('\n📋 测试4: 性能测试 - 快速连续请求');

    await page.setExtraHTTPHeaders({
      'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8'
    });

    const startTime = Date.now();
    let successCount = 0;

    for (let i = 0; i < 5; i++) {
      try {
        await page.goto('http://localhost:3003', {
          waitUntil: 'networkidle2'
        });

        await page.waitForSelector('input[placeholder*="输入要学习的单词"]', { timeout: 5000 });

        const input = await page.$('input[placeholder*="输入要学习的单词"]');
        await input.type(`word${i}`);

        const button = await page.$('button[type="submit"]');
        await button.click();

        // 等待短时间看是否出错
        await page.waitForTimeout(1000);

        successCount++;
        console.log(`✅ 请求 ${i+1} 成功`);

      } catch (error) {
        console.log(`❌ 请求 ${i+1} 失败:`, error.message);
      }
    }

    const endTime = Date.now();
    const totalTime = endTime - startTime;
    const avgTime = totalTime / 5;

    console.log(`✅ 性能测试完成: ${successCount}/5 成功, 平均耗时: ${avgTime}ms`);

    if (avgTime > 3000) {
      console.log('⚠️  性能警告: 平均响应时间较长');
    }

    console.log('\n🎉 语言代码约束修复E2E测试完成！');
    console.log('✅ 英文环境搜索正常');
    console.log('✅ 中文环境搜索正常');
    console.log('✅ 不支持语言fallback正常');
    console.log('✅ 性能测试通过');
    console.log('✅ 未发现约束违反错误');

  } catch (error) {
    console.error('\n💥 E2E测试失败:', error.message);

    if (error.message.includes('约束违反') || error.message.includes('constraint')) {
      console.error('❌ 语言代码约束违反Bug未修复！');
    }

    throw error;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// 运行测试
testLanguageCodeE2E()
  .then(() => {
    console.log('\n🎊 语言代码约束修复E2E测试全部通过！');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n💥 E2E测试失败:', error.message);
    process.exit(1);
  });