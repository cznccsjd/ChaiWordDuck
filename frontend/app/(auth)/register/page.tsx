'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button, Input, useToast } from '@/components/ui';
import { register } from '@/lib/api/auth';
import { useAuthStore } from '@/lib/store/auth';
import { isValidEmail, validatePassword } from '@/lib/utils';

export default function RegisterPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<{
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});
  const [passwordStrength, setPasswordStrength] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const handlePasswordChange = (password: string) => {
    setFormData({ ...formData, password });
    const validation = validatePassword(password);
    setPasswordStrength(validation.message);
  };

  const validateForm = () => {
    const newErrors: {
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    if (!formData.email) {
      newErrors.email = '请输入邮箱';
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = '邮箱格式不正确';
    }

    const passwordValidation = validatePassword(formData.password);
    if (!passwordValidation.isValid) {
      newErrors.password = passwordValidation.message;
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '请确认密码';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致';
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
      const response = await register({
        email: formData.email,
        password: formData.password,
      });

      setAuth(response.user, response.access_token);
      showToast('注册成功！欢迎加入拆词鸭！', 'success');
      router.push('/');
    } catch (error: any) {
      showToast(error.message || '注册失败，请稍后重试', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-yellow-50 to-white flex items-center justify-center px-4 py-10">
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
            加入拆词鸭
          </h1>
          <p className="text-gray-600">
            注册即可获得每天3次查询机会
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
              placeholder="至少8位，包含字母和数字"
              value={formData.password}
              onChange={(e) => handlePasswordChange(e.target.value)}
              error={errors.password}
              helperText={passwordStrength}
              disabled={isLoading}
            />

            <Input
              type="password"
              label="确认密码"
              placeholder="请再次输入密码"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              error={errors.confirmPassword}
              disabled={isLoading}
            />

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? '注册中...' : '注册'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              已有账号？{' '}
              <Link href="/login" className="text-purple-500 hover:text-purple-600 font-semibold">
                立即登录
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
