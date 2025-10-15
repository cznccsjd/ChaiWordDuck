'use client';

import { Navbar } from '@/components/layout/Navbar';
import { SearchBox } from '@/components/features/SearchBox';
import { useQueryLimit } from '@/lib/hooks/useQueryLimit';

export default function HomePage() {
  const { remaining, total, is_guest, isLoading, refresh } = useQueryLimit();

  return (
    <div className="min-h-screen bg-gradient-to-b from-yellow-50 to-white">
      <Navbar />

      <main className="container mx-auto px-4 py-8 sm:py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="mb-6">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-gray-900 mb-4 flex items-center justify-center gap-3">
              <span className="text-5xl sm:text-6xl md:text-7xl">🦆</span>
              <span>拆词鸭</span>
            </h1>
            <p className="text-lg sm:text-xl md:text-2xl text-gray-600 font-medium">
              让长单词变得有故事、可拆解、能记住
            </p>
          </div>

          {/* 产品特色 */}
          <div className="max-w-3xl mx-auto mb-8">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm sm:text-base">
              <div className="bg-white/50 backdrop-blur-sm rounded-lg px-4 py-3">
                <div className="text-2xl mb-1">🎮</div>
                <div className="font-semibold text-gray-800">语言游戏</div>
                <div className="text-gray-600 text-xs sm:text-sm">让单词变有趣</div>
              </div>
              <div className="bg-white/50 backdrop-blur-sm rounded-lg px-4 py-3">
                <div className="text-2xl mb-1">🔧</div>
                <div className="font-semibold text-gray-800">拆解记忆</div>
                <div className="text-gray-600 text-xs sm:text-sm">词根变故事</div>
              </div>
              <div className="bg-white/50 backdrop-blur-sm rounded-lg px-4 py-3">
                <div className="text-2xl mb-1">💡</div>
                <div className="font-semibold text-gray-800">创意秘籍</div>
                <div className="text-gray-600 text-xs sm:text-sm">过目不忘</div>
              </div>
            </div>
          </div>
        </div>

        {/* Search Section */}
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-6 text-center">
              开始学习长单词
            </h2>

            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500" />
              </div>
            ) : (
              <SearchBox
                remainingQueries={remaining}
                totalQueries={total}
                isGuest={is_guest}
                onSearch={refresh}
              />
            )}
          </div>

          {/* 引导注册 - 仅游客显示 */}
          {is_guest && (
            <div className="mt-6 bg-gradient-to-r from-purple-50 to-yellow-50 rounded-xl p-6 text-center">
              <p className="text-gray-700 mb-4">
                <span className="font-semibold">注册账号</span>可获得：
              </p>
              <ul className="text-sm text-gray-600 space-y-2 mb-4">
                <li>✓ 每天3次查询机会</li>
                <li>✓ 收藏喜欢的单词</li>
                <li>✓ 查看学习历史记录</li>
              </ul>
              <a
                href="/register"
                className="inline-block bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold px-8 py-3 rounded-lg transition-colors shadow-md hover:shadow-lg"
              >
                立即注册
              </a>
            </div>
          )}
        </div>

        {/* 产品介绍 */}
        <div className="mt-16 max-w-4xl mx-auto">
          <h3 className="text-2xl font-bold text-gray-900 text-center mb-8">
            为什么选择拆词鸭？
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="text-3xl mb-3">🎯</div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">
                专注长单词
              </h4>
              <p className="text-gray-600 text-sm">
                专门针对8字母以上的长单词，解决成人英语学习的最大痛点
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="text-3xl mb-3">📖</div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">
                五步学习法
              </h4>
              <p className="text-gray-600 text-sm">
                核心游戏、双场景对照、词根拆解、犯规警告、通关秘籍，系统化记忆
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="text-3xl mb-3">🎨</div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">
                故事化记忆
              </h4>
              <p className="text-gray-600 text-sm">
                将枯燥的词根拆解变成有趣的故事，让单词变得生动可记
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="text-3xl mb-3">⚡</div>
              <h4 className="text-lg font-semibold text-gray-800 mb-2">
                科学复习
              </h4>
              <p className="text-gray-600 text-sm">
                基于艾宾浩斯遗忘曲线的智能复习提醒，确保长期记忆
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 mt-16 py-8">
        <div className="container mx-auto px-4 text-center text-gray-600 text-sm">
          <p>&copy; 2025 拆词鸭 ChaiWord Duck. 让长单词变得可记住。</p>
        </div>
      </footer>
    </div>
  );
}
