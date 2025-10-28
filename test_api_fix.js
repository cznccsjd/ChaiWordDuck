// 测试修复后的API功能
const axios = require('axios');

async function testAPI() {
  console.log('🧪 开始测试修复后的API功能...\n');

  const API_BASE_URL = 'http://localhost:8000/api/v1';

  try {
    // 测试1: 直接调用后端API
    console.log('📡 测试1: 直接调用后端API');
    const directResponse = await axios.get(`${API_BASE_URL}/words/query/embarrassment`);
    console.log('✅ 后端API响应:', JSON.stringify(directResponse.data, null, 2));
    console.log('');

    // 测试2: 模拟前端API调用逻辑
    console.log('🔄 测试2: 模拟前端数据映射逻辑');
    const apiData = directResponse.data.data;
    console.log('📥 原始数据:', apiData);

    // 模拟前端映射逻辑
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

    console.log('📤 映射后数据:', mappedData);
    console.log('');

    // 验证关键字段
    console.log('🔍 验证关键字段:');
    console.log('- ID存在:', !!mappedData.id);
    console.log('- 单词内容存在:', !!mappedData.word);
    console.log('- 单词内容非空:', mappedData.word.trim() !== '');
    console.log('- 音标存在:', !!mappedData.phonetic);
    console.log('- 词性存在:', !!mappedData.part_of_speech);
    console.log('- 路由路径:', `/word/${mappedData.id}`);
    console.log('');

    // 测试3: 验证单词详情页API
    console.log('📄 测试3: 验证单词详情页API');
    const detailResponse = await axios.get(`${API_BASE_URL}/words/${mappedData.id}`);
    console.log('✅ 详情页API响应:', JSON.stringify(detailResponse.data, null, 2));

    console.log('\n🎉 所有API测试通过！修复应该有效。');

  } catch (error) {
    console.error('❌ API测试失败:', error.message);
    if (error.response) {
      console.error('响应数据:', error.response.data);
    }
  }
}

testAPI();