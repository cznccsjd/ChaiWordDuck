import apiClient, { handleApiError } from './client';
import type { WordManual, WordManualApiResponse, QueryLimit, ApiResponse } from '@/types';

// 查询单词
export async function queryWord(word: string): Promise<WordManual> {
  try {
    const response = await apiClient.get<ApiResponse<WordManualApiResponse>>(`/words/query/${word}`);
    if (!response.data.success || !response.data.data) {
      throw new Error('查询失败');
    }
    // 数据字段映射：将后端的camelCase转换为前端的snake_case
    const apiData = response.data.data;
    return {
      id: apiData.id,
      word: apiData.word,
      phonetic: apiData.phonetic,
      part_of_speech: apiData.partOfSpeech,
      core_game: apiData.coreGame,
      scene_formal: apiData.scenarioFormal,
      scene_daily: apiData.scenarioCasual,
      etymology: apiData.etymologyBreakdown || '',
      common_mistakes: apiData.commonMistakes,
      memory_trick: apiData.memoryTrick,
      is_golden: apiData.isGolden,
      created_at: apiData.created_at,
    };
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
    const response = await apiClient.get<ApiResponse<WordManualApiResponse>>(`/words/${wordId}`);
    if (!response.data.success || !response.data.data) {
      throw new Error('获取单词详情失败');
    }
    // 数据字段映射：将后端的camelCase转换为前端的snake_case
    const apiData = response.data.data;
    return {
      id: apiData.id,
      word: apiData.word,
      phonetic: apiData.phonetic,
      part_of_speech: apiData.partOfSpeech,
      core_game: apiData.coreGame,
      scene_formal: apiData.scenarioFormal,
      scene_daily: apiData.scenarioCasual,
      etymology: apiData.etymologyBreakdown || '',
      common_mistakes: apiData.commonMistakes,
      memory_trick: apiData.memoryTrick,
      is_golden: apiData.isGolden,
      created_at: apiData.created_at,
    };
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}
