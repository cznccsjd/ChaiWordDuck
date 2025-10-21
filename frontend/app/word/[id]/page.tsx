'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Navbar } from '@/components/layout/Navbar';
import { getWordById } from '@/lib/api/words';
import { addFavorite, removeFavorite } from '@/lib/api/favorites';
import { useAuthStore } from '@/lib/store/auth';
import { useToast } from '@/components/ui';
import type { WordManual } from '@/types';

interface WordDetailPageProps {
  params: {
    id: string;
  };
}

export default function WordDetailPage({ params }: WordDetailPageProps) {
  const router = useRouter();
  const { user } = useAuthStore();
  const { showToast } = useToast();
  const [word, setWord] = useState<WordManual | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFavorited, setIsFavorited] = useState(false);
  const [isFavoriting, setIsFavoriting] = useState(false);

  useEffect(() => {
    const loadWord = async () => {
      setIsLoading(true);
      console.log('单词详情页 - 接收到的路由参数:', params);
      console.log('单词详情页 - params.id:', params.id);

      try {
        const wordId = parseInt(params.id);
        console.log('单词详情页 - 转换后的wordId:', wordId);

        if (isNaN(wordId)) {
          console.error('单词ID转换失败:', params.id);
          showToast('无效的单词ID', 'error');
          router.push('/');
          return;
        }

        const wordData = await getWordById(wordId);
        console.log('单词详情页 - 从API获取的数据:', wordData);
        setWord(wordData);

        // TODO: 从API获取是否已收藏
        // 暂时设为false
        setIsFavorited(false);
      } catch (error) {
        console.error('Failed to load word:', error);
        showToast('加载单词失败，请稍后重试', 'error');
        router.push('/');
      } finally {
        setIsLoading(false);
      }
    };

    loadWord();
  }, [params.id, router, showToast]);

  const handleFavorite = async () => {
    if (!user) {
      showToast('请先登录', 'info');
      router.push('/login');
      return;
    }

    if (!word) return;

    setIsFavoriting(true);
    try {
      if (isFavorited) {
        // 取消收藏
        // TODO: removeFavorite需要favoriteId，但当前只有word.id
        // 需要后端提供以下任一方案:
        // 1. 添加 DELETE /favorites/by-word/{wordId} 端点
        // 2. checkFavorite返回 { is_favorited: boolean, favorite_id: number | null }
        // 临时方案: 引导用户从收藏页删除
        showToast('请从"我的收藏"页面取消收藏', 'info');
        return;
      } else {
        // 添加收藏
        await addFavorite(word.id);
        setIsFavorited(true);
        showToast('已收藏', 'success');
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
      showToast(isFavorited ? '取消收藏失败' : '收藏失败', 'error');
    } finally {
      setIsFavoriting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-yellow-50 to-white">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            {/* 骨架屏 */}
            <div className="animate-pulse">
              <div className="h-12 bg-gray-200 rounded w-1/2 mb-4" />
              <div className="h-6 bg-gray-200 rounded w-1/4 mb-8" />

              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="bg-white rounded-xl p-6 mb-4">
                  <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
                  <div className="h-24 bg-gray-200 rounded" />
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!word) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-yellow-50 to-white">
      <Navbar />

      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* 单词标题 */}
          <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8 mb-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 mb-2">
                  {word.word}
                </h1>
                <p className="text-lg sm:text-xl text-gray-600 mb-2">
                  {word.phonetic}
                </p>
                <span className="inline-block px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                  {word.part_of_speech}
                </span>
              </div>

              {/* 收藏按钮 */}
              <button
                onClick={handleFavorite}
                disabled={isFavoriting}
                className="ml-4 p-3 hover:bg-yellow-50 rounded-full transition-colors disabled:opacity-50"
                title={isFavorited ? '取消收藏' : '收藏'}
              >
                {isFavorited ? (
                  <span className="text-3xl">⭐</span>
                ) : (
                  <span className="text-3xl text-gray-400">☆</span>
                )}
              </button>
            </div>
          </div>

          {/* 五步学习法 */}

          {/* 步骤1: 核心游戏 */}
          <div className="bg-gradient-to-r from-yellow-100 to-yellow-50 rounded-xl p-6 mb-4 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-3xl">🎮</span>
              <span>步骤1: 核心游戏</span>
            </h2>
            <p className="text-gray-800 text-lg leading-relaxed">
              {word.core_game}
            </p>
          </div>

          {/* 步骤2: 双场景对照 */}
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-3xl">🎭</span>
              <span>步骤2: 双场景对照</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 思辨场景 */}
              <div className="bg-gradient-to-br from-purple-100 to-purple-50 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-purple-900 mb-3">
                  思辨场景（学术/正式）
                </h3>
                <p className="text-gray-800 leading-relaxed">
                  {word.scene_formal}
                </p>
              </div>

              {/* 生活场景 */}
              <div className="bg-gradient-to-br from-orange-100 to-orange-50 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-orange-900 mb-3">
                  生活场景（日常/口语）
                </h3>
                <p className="text-gray-800 leading-relaxed">
                  {word.scene_daily}
                </p>
              </div>
            </div>
          </div>

          {/* 步骤3: 词根拆解 */}
          <div className="bg-gradient-to-r from-gray-100 to-gray-50 rounded-xl p-6 mb-4 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-3xl">🔧</span>
              <span>步骤3: 词根拆解</span>
            </h2>
            <div className="space-y-4">
              {/* 词根可视化 */}
              <div className="bg-white rounded-lg p-4 font-mono text-lg text-center">
                <span className="font-bold text-purple-600">{word.word}</span>
              </div>

              {/* 词源故事 */}
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {word.etymology}
              </p>
            </div>
          </div>

          {/* 步骤4: 犯规警告 */}
          <div className="bg-white rounded-xl p-6 mb-4 shadow-sm border-2 border-red-200">
            <h2 className="text-2xl font-bold text-red-700 mb-4 flex items-center gap-2">
              <span className="text-3xl">⚠️</span>
              <span>步骤4: 犯规警告</span>
            </h2>
            <p className="text-gray-800 leading-relaxed">
              {word.common_mistakes}
            </p>
          </div>

          {/* 步骤5: 通关秘籍 */}
          <div className="bg-gradient-to-r from-green-100 to-green-50 rounded-xl p-6 mb-6 shadow-sm">
            <h2 className="text-2xl font-bold text-green-900 mb-4 flex items-center gap-2">
              <span className="text-3xl">💡</span>
              <span>步骤5: 通关秘籍</span>
            </h2>
            <p className="text-gray-800 text-lg leading-relaxed">
              {word.memory_trick}
            </p>
          </div>

          {/* 底部操作 */}
          <div className="bg-white rounded-xl p-6 shadow-sm text-center">
            <p className="text-gray-600 mb-4">
              发现内容有误？
              <button className="text-purple-600 hover:text-purple-700 font-medium ml-2 underline">
                点击反馈
              </button>
            </p>

            <button
              onClick={() => router.push('/')}
              className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold px-8 py-3 rounded-lg transition-colors shadow-md hover:shadow-lg"
            >
              返回首页
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
