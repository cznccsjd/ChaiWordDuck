export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-yellow-50 to-white">
      <div className="container mx-auto px-4 py-10">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            拆词鸭 ChaiWord Duck
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            让长单词变得有故事、可拆解、能记住
          </p>

          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-xl shadow-md p-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                搜索单词
              </h2>

              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="输入要学习的单词..."
                  className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-yellow-400 focus:outline-none transition-colors"
                />
                <button className="px-8 py-3 bg-yellow-400 text-gray-900 font-semibold rounded-lg hover:bg-yellow-500 active:bg-yellow-600 transition-colors shadow-brand">
                  搜索
                </button>
              </div>

              <p className="mt-4 text-sm text-gray-500">
                游客模式：今日剩余 1/1 次查询
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
