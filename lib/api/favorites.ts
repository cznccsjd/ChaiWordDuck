import apiClient, { handleApiError } from './client';
import type { Favorite, ApiResponse } from '@/types';

// 收藏单词
export async function addFavorite(wordId: number): Promise<Favorite> {
  try {
    const response = await apiClient.post<Favorite>('/favorites', { word_id: wordId });
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}

// 取消收藏
export async function removeFavorite(favoriteId: number): Promise<void> {
  try {
    await apiClient.delete(`/favorites/${favoriteId}`);
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}

// 获取收藏列表
export async function getFavorites(): Promise<Favorite[]> {
  try {
    const response = await apiClient.get<Favorite[]>('/favorites');
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}

// 检查单词是否已收藏
export async function checkFavorite(wordId: number): Promise<boolean> {
  try {
    const response = await apiClient.get<{ is_favorited: boolean }>(`/favorites/check/${wordId}`);
    return response.data.is_favorited;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}
