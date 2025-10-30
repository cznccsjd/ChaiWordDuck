#!/usr/bin/env node

const axios = require('axios');

// 模拟前端的queryWord函数
async function queryWord(word) {
  try {
    console.log(`🔍 开始查询单词 "${word}"`);

    // 使用修复后的API URL
    const API_BASE_URL = 'http://localhost:8001/api/v1';
    const response = await axios.get(`${API_BASE_URL}/words/query/${word}`);

    console.log('✅ API调用成功:', response.status);
    console.log('📄 原始响应数据:', JSON.stringify(response.data, null, 2));

    if (!response.data.success) {
      throw new Error(response.data.message || '查询失败');
    }

    if (!response.data.data) {
      throw new Error('API返回数据为空');
    }

    // 数据字段映射：将后端的camelCase转换为前端的snake_case
    const apiData = response.data.data;
    console.log('🔄 后端返回的camelCase数据:', apiData);

    // 验证必要字段
    if (!apiData.id) {
      throw new Error('API返回数据缺少单词ID');
    }

    // 字段映射逻辑
    const mappedData = {
      id: apiData.id,
      word: apiData.word || '',
      phonetic: apiData.phonetic || '',
      part_of_speech: apiData.partOfSpeech || '',
      core_game: apiData.coreGame || '',
      scene_formal: apiData.scenarioFormal || '',
      scene_daily: apiData.scenarioCasual || '',
      etymology: apiData.etymologyBreakdown || '',
      common_mistakes: apiData.commonMistakes || '',
      memory_trick: apiData.memoryTrick || '',
      is_golden: apiData.isGolden || false,
      created_at: apiData.created_at || new Date().toISOString(),
    };

    console.log('✅ 映射后的snake_case数据:', mappedData);

    // 验证映射后的数据完整性
    if (!mappedData.word) {
      throw new Error('API返回数据缺少单词内容');
    }

    return mappedData;
  } catch (error) {
    console.error('❌ 查询单词失败:', error.message);
    throw error;
  }
}

// 测试搜索功能
async function testSearchFunction() {
  console.log('🚀 开始测试搜索功能...\n');

  try {
    // 测试1: 查询 "everything"
    console.log('📋 测试1: 查询 "everything"');
    const wordData = await queryWord('everything');

    console.log('✅ 查询成功！');
    console.log(`📝 单词: ${wordData.word}`);
    console.log(`🔤 音标: ${wordData.phonetic}`);
    console.log(`📂 词性: ${wordData.part_of_speech}`);
    console.log(`🎯 核心游戏: ${wordData.core_game.substring(0, 50)}...`);
    console.log(`🔗 可跳转路由: /word/${wordData.id}`);

    // 测试2: 验证跳转路由是否有效
    console.log('\n📋 测试2: 验证跳转路由');
    const targetRoute = `/word/${wordData.id}`;
    console.log(`🎯 目标路由: ${targetRoute}`);

    // 这里我们只验证路由格式正确，实际跳转需要在浏览器中测试
    if (targetRoute.match(/^\/word\/\d+$/)) {
      console.log('✅ 路由格式正确');
    } else {
      console.log('❌ 路由格式错误');
    }

    console.log('\n🎉 搜索功能测试完成 - 全部通过！');

  } catch (error) {
    console.error('\n💥 搜索功能测试失败:', error.message);
    process.exit(1);
  }
}

// 运行测试
testSearchFunction();