'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store/auth';
import { Button } from '@/components/ui';

export function Navbar() {
  const { user, clearAuth } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const handleLogout = () => {
    clearAuth();
    setIsUserMenuOpen(false);
  };

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center space-x-2 font-bold text-xl text-gray-900 hover:text-yellow-500 transition-colors"
          >
            <span className="text-2xl">🦆</span>
            <span>拆词鸭</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="/"
              className="text-gray-700 hover:text-yellow-500 transition-colors font-medium"
            >
              首页
            </Link>
            {user && (
              <Link
                href="/favorites"
                className="text-gray-700 hover:text-yellow-500 transition-colors font-medium"
              >
                我的收藏
              </Link>
            )}
          </div>

          {/* Desktop User Menu */}
          <div className="hidden md:flex items-center space-x-4">
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center space-x-2 text-gray-700 hover:text-yellow-500 transition-colors"
                >
                  <span className="font-medium">{user.email}</span>
                  <svg
                    className={`w-4 h-4 transition-transform ${isUserMenuOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Dropdown Menu */}
                {isUserMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setIsUserMenuOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-20 border border-gray-100">
                      <Link
                        href="/settings"
                        className="block px-4 py-2 text-gray-700 hover:bg-yellow-50 transition-colors"
                        onClick={() => setIsUserMenuOpen(false)}
                      >
                        个人设置
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-yellow-50 transition-colors"
                      >
                        退出登录
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="outline" size="sm">
                    登录
                  </Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">
                    注册
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden text-gray-700 hover:text-yellow-500 transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {isMobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden pb-4 border-t border-gray-100 mt-2">
            <div className="flex flex-col space-y-3 pt-4">
              <Link
                href="/"
                className="text-gray-700 hover:text-yellow-500 transition-colors font-medium px-2 py-2"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                首页
              </Link>
              {user && (
                <>
                  <Link
                    href="/favorites"
                    className="text-gray-700 hover:text-yellow-500 transition-colors font-medium px-2 py-2"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    我的收藏
                  </Link>
                  <Link
                    href="/settings"
                    className="text-gray-700 hover:text-yellow-500 transition-colors font-medium px-2 py-2"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    个人设置
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout();
                      setIsMobileMenuOpen(false);
                    }}
                    className="text-left text-gray-700 hover:text-yellow-500 transition-colors font-medium px-2 py-2"
                  >
                    退出登录
                  </button>
                </>
              )}
              {!user && (
                <div className="flex space-x-3 px-2">
                  <Link href="/login" className="flex-1">
                    <Button variant="outline" className="w-full">
                      登录
                    </Button>
                  </Link>
                  <Link href="/register" className="flex-1">
                    <Button className="w-full">
                      注册
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
