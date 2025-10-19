import apiClient, { handleApiError } from './client';
import type { AuthResponse, User } from '@/types';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
}

// 用户注册
export async function register(credentials: RegisterCredentials): Promise<AuthResponse> {
  try {
    const response = await apiClient.post<AuthResponse>('/auth/register', credentials);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}

// 用户登录
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  try {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await apiClient.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}

// 获取当前用户信息
export async function getCurrentUser(): Promise<User> {
  try {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error));
  }
}

// 退出登录
export async function logout(): Promise<void> {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
}
