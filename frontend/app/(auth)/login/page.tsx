'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button, Input, useToast } from '@/components/ui';
import { login } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/store/auth';
import { isValidEmail } from '@/lib/utils';

export default function LoginPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [isLoading, setIsLoading] = useState(false);

  const validateForm = () => {
    const newErrors: { email?: string; password?: string } = {};

    if (!formData.email) {
      newErrors.email = '请输入邮箱';
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = '邮箱格式不正确';
    }

    if (!formData.password) {
      newErrors.password = '请输入密码';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await login({
        email: formData.email,
        password: formData.password,
      });

      setAuth(response.user, response.access_token);
      showToast('登录成功！', 'success');
      router.push('/');
    } catch (error: any) {
      showToast(error.message || '登录失败，请稍后重试', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-yellow-50 to-white flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo - 可点击返回首页 */}
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center space-x-2 font-bold text-xl text-gray-900 hover:text-yellow-500 transition-colors group"
          >
            <span className="text-2xl">🦆</span>
            <span>拆词鸭</span>
          </Link>
        </div>

        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            欢迎回来！
          </h1>
          <p className="text-gray-600">
            登录拆词鸭，继续你的学习之旅
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-md p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              type="email"
              label="邮箱"
              placeholder="请输入邮箱"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              error={errors.email}
              disabled={isLoading}
            />

            <Input
              type="password"
              label="密码"
              placeholder="请输入密码"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              error={errors.password}
              disabled={isLoading}
            />

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? '登录中...' : '登录'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              还没有账号？{' '}
              <Link href="/register" className="text-purple-500 hover:text-purple-600 font-semibold">
                立即注册
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
