import apiClient, { handleApiError } from './client';
import type { WordManual, QueryLimit, ApiResponse } from '@/types';

// 查询单词
export async function queryWord(word: string): Promise<WordManual> {
  try {
    const response = await apiClient.get<WordManual>(`/words/query/${word}`);
    return response.data;
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
    const response = await apiClient.get<WordManual>(`/words/${wordId}`);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}
