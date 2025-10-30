#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function testCompleteSearchFlow() {
  console.log('🚀 开始完整的搜索功能端到端测试...\n');

  let browser;
  try {
    // 启动浏览器
    browser = await puppeteer.launch({
      headless: false,  // 设置为true可以无头模式运行
      devtools: true    // 打开开发者工具
    });
    const page = await browser.newPage();

    // 步骤1: 访问首页
    console.log('📋 步骤1: 访问首页');
    await page.goto('http://localhost:3002');
    await page.waitForSelector('input[placeholder*="输入要学习的单词"]');
    console.log('✅ 首页加载成功');

    // 步骤2: 输入搜索单词
    console.log('\n📋 步骤2: 输入搜索单词 "everything"');
    const searchInput = await page.$('input[placeholder*="输入要学习的单词"]');
    await searchInput.type('everything');
    console.log('✅ 输入单词成功');

    // 步骤3: 点击搜索按钮
    console.log('\n📋 步骤3: 点击搜索按钮');
    const searchButton = await page.$('button[type="submit"]');
    await searchButton.click();
    console.log('✅ 点击搜索按钮');

    // 步骤4: 等待页面跳转
    console.log('\n📋 步骤4: 等待页面跳转到单词详情页');

    // 等待最多10秒，检查是否跳转到单词详情页
    try {
      await page.waitForFunction(
        () => window.location.pathname.includes('/word/'),
        { timeout: 10000 }
      );

      const currentUrl = page.url();
      console.log(`✅ 页面跳转成功: ${currentUrl}`);

      // 步骤5: 验证单词详情页内容
      console.log('\n📋 步骤5: 验证单词详情页内容');

      // 等待页面内容加载
      await page.waitForSelector('h1', { timeout: 5000 });

      // 检查单词标题
      const wordTitle = await page.$eval('h1', el => el.textContent);
      console.log(`✅ 单词标题: ${wordTitle}`);

      // 检查音标
      const phonetic = await page.$eval('p', el => el.textContent);
      console.log(`✅ 音标: ${phonetic}`);

      // 检查核心游戏部分
      const coreGame = await page.$eval('text=步骤1: 核心游戏', el => {
        const section = el.closest('div');
        return section.querySelector('p').textContent;
      });
      console.log(`✅ 核心游戏内容: ${coreGame.substring(0, 50)}...`);

      console.log('\n🎉 完整搜索功能测试 - 全部通过！');
      console.log('✅ 搜索表单正常工作');
      console.log('✅ API调用成功');
      console.log('✅ 页面跳转正常');
      console.log('✅ 单词详情页显示正确');

    } catch (error) {
      console.log('\n❌ 页面跳转失败或超时');

      // 检查是否有错误消息显示
      try {
        const errorElement = await page.$('text=/请求失败|错误|未找到/');
        if (errorElement) {
          const errorMessage = await page.evaluate(el => el.textContent, errorElement);
          console.log(`❌ 错误消息: ${errorMessage}`);
        }
      } catch (e) {
        console.log('❌ 未找到明确的错误消息');
      }

      // 获取当前URL
      const currentUrl = page.url();
      console.log(`📍 当前URL: ${currentUrl}`);

      throw new Error('搜索功能测试失败');
    }

  } catch (error) {
    console.error('\n💥 测试失败:', error.message);
    throw error;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// 运行测试
testCompleteSearchFlow()
  .then(() => {
    console.log('\n🎊 测试完成 - 搜索功能修复成功！');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n💥 测试失败:', error.message);
    process.exit(1);
  });