'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { getFavorites, removeFavorite } from '@/lib/api/favorites';
import { useAuthStore } from '@/lib/store/auth';
import { useToast, formatDate } from '@/lib/utils';
import type { Favorite } from '@/types';

export default function FavoritesPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { showToast } = useToast();
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // 登录检查
  useEffect(() => {
    if (!user) {
      showToast('请先登录', 'info');
      router.push('/login');
    }
  }, [user, router, showToast]);

  // 数据加载
  useEffect(() => {
    if (!user) return;

    const loadFavorites = async () => {
      setIsLoading(true);
      try {
        const data = await getFavorites();
        setFavorites(data);
      } catch (error) {
        console.error('Failed to load favorites:', error);
        showToast('加载收藏失败', 'error');
      } finally {
        setIsLoading(false);
      }
    };

    loadFavorites();
  }, [user, showToast]);

  const handleRemoveFavorite = async (favoriteId: number) => {
    try {
      await removeFavorite(favoriteId);
      setFavorites(favorites.filter((fav) => fav.id !== favoriteId));
      showToast('已取消收藏', 'success');
    } catch (error) {
      console.error('Failed to remove favorite:', error);
      showToast('取消收藏失败', 'error');
    }
  };

  // 过滤收藏列表
  const filteredFavorites = favorites.filter((fav) => {
    if (!searchQuery) return true;
    return fav.word_manual.word.toLowerCase().includes(searchQuery.toLowerCase());
  });

  // 如果用户未登录，不渲染内容（useEffect会处理跳转）
  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-yellow-50 to-white">
      <Navbar />

      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* 页面标题 */}
          <div className="mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
              我的收藏
            </h1>
            <p className="text-gray-600">
              共收藏了 {favorites.length} 个单词
            </p>
          </div>

          {/* 搜索框 */}
          {favorites.length > 0 && (
            <div className="mb-6">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索收藏的单词..."
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-yellow-400 focus:outline-none transition-colors"
              />
            </div>
          )}

          {/* 加载状态 */}
          {isLoading && (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500" />
            </div>
          )}

          {/* 空状态 */}
          {!isLoading && favorites.length === 0 && (
            <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
              <div className="text-6xl mb-4">📚</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                还没有收藏的单词
              </h2>
              <p className="text-gray-600 mb-6">
                去首页搜索单词，遇到喜欢的单词就收藏起来吧！
              </p>
              <Link href="/">
                <button className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold px-8 py-3 rounded-lg transition-colors shadow-md hover:shadow-lg">
                  去搜索
                </button>
              </Link>
            </div>
          )}

          {/* 收藏列表 */}
          {!isLoading && filteredFavorites.length > 0 && (
            <div className="space-y-4">
              {filteredFavorites.map((favorite) => (
                <div
                  key={favorite.id}
                  className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-6"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* 单词标题 */}
                      <Link href={`/word/${favorite.word_id}`}>
                        <h3 className="text-2xl font-bold text-gray-900 hover:text-yellow-600 transition-colors mb-2">
                          {favorite.word_manual.word}
                        </h3>
                      </Link>

                      {/* 音标和词性 */}
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-gray-600">
                          {favorite.word_manual.phonetic}
                        </span>
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-sm">
                          {favorite.word_manual.part_of_speech}
                        </span>
                      </div>

                      {/* 核心游戏摘要 */}
                      <p className="text-gray-700 mb-3 line-clamp-2">
                        {favorite.word_manual.core_game}
                      </p>

                      {/* 收藏时间 */}
                      <p className="text-sm text-gray-500">
                        收藏于 {formatDate(favorite.created_at)}
                      </p>
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex flex-col gap-2 ml-4">
                      <Link href={`/word/${favorite.word_id}`}>
                        <button className="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-medium rounded-lg transition-colors shadow-sm text-sm">
                          查看详情
                        </button>
                      </Link>
                      <button
                        onClick={() => handleRemoveFavorite(favorite.id)}
                        className="px-4 py-2 bg-gray-100 hover:bg-red-50 text-gray-700 hover:text-red-600 font-medium rounded-lg transition-colors text-sm flex items-center justify-center gap-1"
                        title="取消收藏"
                      >
                        <span>🗑️</span>
                        <span>取消</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 搜索无结果 */}
          {!isLoading && favorites.length > 0 && filteredFavorites.length === 0 && (
            <div className="bg-white rounded-xl p-12 text-center">
              <div className="text-4xl mb-4">🔍</div>
              <p className="text-gray-600">
                没有找到匹配的单词
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
