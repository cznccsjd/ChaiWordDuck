import apiClient, { handleApiError } from './client';
import type { WordManual, WordManualApiResponse, QueryLimit, ApiResponse } from '@/types';

// 查询单词
export async function queryWord(word: string): Promise<WordManual> {
  try {
    const response = await apiClient.get<{success: boolean, data: WordManualApiResponse}>(`/words/query/${word}`);

    // 检查API响应格式
    if (!response.data.success || !response.data.data) {
      throw new Error('API返回数据格式错误');
    }

    // 转换字段命名格式：camelCase -> snake_case
    const apiData = response.data.data;
    const wordData: WordManual = {
      id: apiData.id,
      word: apiData.word,
      phonetic: apiData.phonetic || '',
      part_of_speech: apiData.partOfSpeech || '',
      core_game: apiData.coreGame,
      scene_formal: apiData.scenarioFormal,
      scene_daily: apiData.scenarioCasual,
      etymology: apiData.etymologyStory || apiData.etymologyBreakdown,
      common_mistakes: apiData.commonMistakes,
      memory_trick: apiData.memoryTrick,
      is_golden: apiData.isGolden,
      created_at: apiData.createdAt
    };

    return wordData;
  } catch (error) {
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
    const response = await apiClient.get<{success: boolean, data: WordManualApiResponse}>(`/words/${wordId}`);

    // 检查API响应格式
    if (!response.data.success || !response.data.data) {
      throw new Error('API返回数据格式错误');
    }

    // 转换字段命名格式：camelCase -> snake_case
    const apiData = response.data.data;
    const wordData: WordManual = {
      id: apiData.id,
      word: apiData.word,
      phonetic: apiData.phonetic || '',
      part_of_speech: apiData.partOfSpeech || '',
      core_game: apiData.coreGame,
      scene_formal: apiData.scenarioFormal,
      scene_daily: apiData.scenarioCasual,
      etymology: apiData.etymologyStory || apiData.etymologyBreakdown,
      common_mistakes: apiData.commonMistakes,
      memory_trick: apiData.memoryTrick,
      is_golden: apiData.isGolden,
      created_at: apiData.createdAt
    };

    return wordData;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}
