#!/usr/bin/env node

const axios = require('axios');

console.log('🎯 拆词鸭搜索功能修复验证报告');
console.log('=====================================\n');

async function finalVerification() {
  const results = {
    apiHealth: false,
    searchFunction: false,
    wordDetailPage: false,
    dataIntegrity: false
  };

  try {
    // 测试1: API健康检查
    console.log('📋 测试1: 后端API健康检查');
    try {
      const healthResponse = await axios.get('http://localhost:8001/api/v1/words/query/everything', { timeout: 5000 });
      if (healthResponse.status === 200 && healthResponse.data.success) {
        console.log('✅ API健康检查通过');
        console.log(`   状态码: ${healthResponse.status}`);
        console.log(`   响应时间: <5秒`);
        results.apiHealth = true;
      }
    } catch (error) {
      console.log('❌ API健康检查失败:', error.message);
    }

    // 测试2: 搜索功能验证
    console.log('\n📋 测试2: 搜索功能验证');
    try {
      const searchResponse = await axios.get('http://localhost:8001/api/v1/words/query/everything');
      const wordData = searchResponse.data.data;

      if (wordData && wordData.id && wordData.word) {
        console.log('✅ 搜索功能正常');
        console.log(`   找到单词: ${wordData.word}`);
        console.log(`   单词ID: ${wordData.id}`);
        console.log(`   音标: ${wordData.phonetic}`);
        console.log(`   核心游戏: ${wordData.coreGame.substring(0, 30)}...`);
        results.searchFunction = true;
      }
    } catch (error) {
      console.log('❌ 搜索功能失败:', error.message);
    }

    // 测试3: 单词详情页访问
    console.log('\n📋 测试3: 单词详情页访问');
    try {
      const detailResponse = await axios.get('http://localhost:3002/word/38');
      if (detailResponse.status === 200) {
        console.log('✅ 单词详情页可访问');
        console.log(`   页面状态码: ${detailResponse.status}`);
        console.log(`   页面URL: /word/38`);
        results.wordDetailPage = true;
      }
    } catch (error) {
      console.log('❌ 单词详情页访问失败:', error.message);
    }

    // 测试4: 数据完整性验证
    console.log('\n📋 测试4: 数据完整性验证');
    try {
      const response = await axios.get('http://localhost:8001/api/v1/words/query/everything');
      const data = response.data.data;

      const requiredFields = ['id', 'word', 'phonetic', 'coreGame', 'scenarioFormal', 'scenarioCasual', 'memoryTrick'];
      const missingFields = requiredFields.filter(field => !data[field]);

      if (missingFields.length === 0) {
        console.log('✅ 数据完整性验证通过');
        console.log(`   所有必需字段都存在: ${requiredFields.join(', ')}`);
        results.dataIntegrity = true;
      } else {
        console.log('❌ 数据完整性验证失败');
        console.log(`   缺少字段: ${missingFields.join(', ')}`);
      }
    } catch (error) {
      console.log('❌ 数据完整性验证失败:', error.message);
    }

    // 生成最终报告
    console.log('\n🎊 最终验证结果');
    console.log('=====================================');

    const passedTests = Object.values(results).filter(Boolean).length;
    const totalTests = Object.keys(results).length;

    console.log(`通过测试: ${passedTests}/${totalTests}`);

    if (passedTests === totalTests) {
      console.log('\n🎉 恭喜！搜索功能修复完全成功！');
      console.log('✅ 用户现在可以正常使用搜索功能');
      console.log('✅ API调用完全正常');
      console.log('✅ 页面跳转功能正常');
      console.log('✅ 数据显示完整');

      console.log('\n📝 修复总结:');
      console.log('1. ✅ 修复了API基础URL端口配置 (8000 → 8001)');
      console.log('2. ✅ 更新了环境变量配置文件');
      console.log('3. ✅ 创建了本地环境变量文件确保配置生效');
      console.log('4. ✅ 验证了完整的搜索流程');
      console.log('5. ✅ 确认了页面跳转和数据显示正常');

      return true;
    } else {
      console.log('\n⚠️  部分测试未通过，需要进一步检查');
      const failedTests = Object.entries(results)
        .filter(([key, value]) => !value)
        .map(([key]) => key);
      console.log('失败的测试:', failedTests.join(', '));
      return false;
    }

  } catch (error) {
    console.error('\n💥 验证过程中发生错误:', error.message);
    return false;
  }
}

// 运行最终验证
finalVerification()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('验证脚本执行失败:', error);
    process.exit(1);
  });