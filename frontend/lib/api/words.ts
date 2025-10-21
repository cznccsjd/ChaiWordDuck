import apiClient, { handleApiError } from './client';
import type { WordManual, WordManualApiResponse, QueryLimit, ApiResponse } from '@/types';

// 查询单词
export async function queryWord(word: string): Promise<WordManual> {
  try {
    console.log(`API: 开始查询单词 "${word}"`);
    const response = await apiClient.get<ApiResponse<WordManualApiResponse>>(`/words/query/${word}`);

    console.log('API: 原始响应数据:', response.data);

    if (!response.data.success) {
      throw new Error(response.data.message || '查询失败');
    }

    if (!response.data.data) {
      throw new Error('API返回数据为空');
    }

    // 数据字段映射：将后端的camelCase转换为前端的snake_case
    const apiData = response.data.data;
    console.log('API: 后端返回的camelCase数据:', apiData);

    // 验证必要字段
    if (!apiData.id) {
      throw new Error('API返回数据缺少单词ID');
    }

    const mappedData = {
      id: apiData.id,
      word: apiData.word,
      phonetic: apiData.phonetic || '',
      part_of_speech: apiData.partOfSpeech || '',
      core_game: apiData.coreGame,
      scene_formal: apiData.scenarioFormal,
      scene_daily: apiData.scenarioCasual,
      etymology: apiData.etymologyBreakdown,
      common_mistakes: apiData.commonMistakes,
      memory_trick: apiData.memoryTrick,
      is_golden: apiData.isGolden,
      created_at: apiData.created_at,
    };

    console.log('API: 映射后的snake_case数据:', mappedData);
    return mappedData;
  } catch (error) {
    console.error('API: 查询单词失败:', error);
    throw new Error(handleApiError(error));
  }
}

// 获取查询限制信息
export async function getQueryLimit(): Promise<QueryLimit> {
  try {
    const response = await apiClient.get<QueryLimit>('/words/query-limit');
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}

// 获取单词详情
export async function getWordById(wordId: number): Promise<WordManual> {
  try {
    console.log(`API: 获取单词详情 ID=${wordId}`);
    const response = await apiClient.get<ApiResponse<WordManualApiResponse>>(`/words/${wordId}`);

    console.log('API: 原始响应数据:', response.data);

    if (!response.data.success) {
      throw new Error(response.data.message || '获取单词详情失败');
    }

    if (!response.data.data) {
      throw new Error('API返回数据为空');
    }

    // 数据字段映射：将后端的camelCase转换为前端的snake_case
    const apiData = response.data.data;
    console.log('API: 后端返回的camelCase数据:', apiData);

    // 验证必要字段
    if (!apiData.id) {
      throw new Error('API返回数据缺少单词ID');
    }

    const mappedData = {
      id: apiData.id,
      word: apiData.word,
      phonetic: apiData.phonetic || '',
      part_of_speech: apiData.partOfSpeech || '',
      core_game: apiData.coreGame,
      scene_formal: apiData.scenarioFormal,
      scene_daily: apiData.scenarioCasual,
      etymology: apiData.etymologyBreakdown,
      common_mistakes: apiData.commonMistakes,
      memory_trick: apiData.memoryTrick,
      is_golden: apiData.isGolden,
      created_at: apiData.created_at,
    };

    console.log('API: 映射后的snake_case数据:', mappedData);
    return mappedData;
  } catch (error) {
    console.error('API: 获取单词详情失败:', error);
    throw new Error(handleApiError(error));
  }
}
