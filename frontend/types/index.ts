// 用户类型
export interface User {
  id: number;
  email: string;
  is_premium: boolean;
  created_at: string;
}

// 单词手册类型
export interface WordManual {
  id: number;
  word: string;
  phonetic: string;
  part_of_speech: string;
  core_game: string;
  scene_formal: string;
  scene_daily: string;
  etymology: string;
  common_mistakes: string;
  memory_trick: string;
  is_golden: boolean;
  created_at: string;
}

// 收藏类型
export interface Favorite {
  id: number;
  user_id: number;
  word_id: number;
  word_manual: WordManual;
  created_at: string;
}

// 查询记录类型
export interface QueryLog {
  id: number;
  user_id: number | null;
  word_id: number;
  is_guest: boolean;
  created_at: string;
}

// 认证响应类型
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 查询限制信息类型
export interface QueryLimit {
  remaining: number;
  total: number;
  is_guest: boolean;
}
