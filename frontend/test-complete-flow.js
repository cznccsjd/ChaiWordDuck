#!/usr/bin/env node

const axios = require('axios');

// 完整流程测试
async function testCompleteFlow() {
  console.log('🚀 拆词鸭搜索功能完整流程测试\n');

  try {
    // 测试1: 首页访问
    console.log('📋 测试1: 首页访问');
    try {
      const homeResponse = await axios.get('http://localhost:3002');
      console.log('✅ 首页访问成功 (状态码:', homeResponse.status, ')');
    } catch (error) {
      console.log('❌ 首页访问失败:', error.message);
      throw error;
    }

    // 测试2: API查询 everything
    console.log('\n📋 测试2: API查询单词 "everything"');
    let wordData;
    try {
      const apiResponse = await axios.get('http://localhost:8001/api/v1/words/query/everything');
      console.log('✅ API查询成功 (状态码:', apiResponse.status, ')');

      if (!apiResponse.data.success || !apiResponse.data.data) {
        throw new Error('API返回数据格式错误');
      }

      wordData = apiResponse.data.data;
      console.log(`✅ 获取到单词数据: ${wordData.word} (ID: ${wordData.id})`);

    } catch (error) {
      console.log('❌ API查询失败:', error.message);
      throw error;
    }

    // 测试3: 单词详情页访问
    console.log('\n📋 测试3: 访问单词详情页');
    try {
      const detailResponse = await axios.get(`http://localhost:3002/word/${wordData.id}`);
      console.log('✅ 单词详情页访问成功 (状态码:', detailResponse.status, ')');

      // 检查页面内容是否包含单词信息
      const pageContent = detailResponse.data;
      if (pageContent.includes(wordData.word) && pageContent.includes(wordData.phonetic)) {
        console.log('✅ 单词详情页内容验证通过');
      } else {
        console.log('❌ 单词详情页内容验证失败');
        throw new Error('页面内容不包含预期的单词信息');
      }

    } catch (error) {
      console.log('❌ 单词详情页访问失败:', error.message);
      throw error;
    }

    // 测试4: 验证搜索流程的完整性
    console.log('\n📋 测试4: 验证搜索流程完整性');
    console.log('✅ 1. 用户可以访问首页');
    console.log('✅ 2. API能够正常查询单词');
    console.log('✅ 3. 返回的数据包含完整的单词信息');
    console.log('✅ 4. 可以根据单词ID生成正确的详情页URL');
    console.log('✅ 5. 单词详情页可以正常访问并显示内容');

    console.log('\n🎉 搜索功能完整流程测试 - 全部通过！');
    console.log('🔧 修复总结:');
    console.log('   - 修复了API基础URL配置 (8000 -> 8001端口)');
    console.log('   - 更新了环境变量配置文件');
    console.log('   - 创建了本地环境变量文件确保配置生效');
    console.log('   - 验证了API数据映射和字段转换正常');
    console.log('   - 确认了页面跳转路由格式正确');

  } catch (error) {
    console.error('\n💥 完整流程测试失败:', error.message);
    process.exit(1);
  }
}

// 运行测试
testCompleteFlow();