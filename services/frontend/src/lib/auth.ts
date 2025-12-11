import api from './api';
import {
  RegisterData,
  LoginData,
  ConfirmData,
  RecoverData,
  ResetData,
  LoginResponse,
} from '@/types';

export const authService = {
  // Регистрация
  async register(data: RegisterData): Promise<{ message: string }> {
    const response = await api.post('/users/register', data);
    return response.data;
  },

  // Подтверждение email
  async confirm(data: ConfirmData): Promise<{ message: string }> {
    const response = await api.post('/users/confirm', data);
    return response.data;
  },

  // Вход
  async login(data: LoginData): Promise<LoginResponse> {
    const response = await api.post('/users/login', data);
    const { access_token } = response.data;
    
    // Сохраняем токен в localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', access_token);
    }
    
    return response.data;
  },

  // Выход
  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  },

  // Получение токена
  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  },

  // Проверка авторизации
  isAuthenticated(): boolean {
    return !!this.getToken();
  },

  // Запрос восстановления пароля
  async recover(data: RecoverData): Promise<{ message: string }> {
    const response = await api.post('/users/recover', data);
    return response.data;
  },

  // Сброс пароля
  async reset(data: ResetData): Promise<{ message: string }> {
    const response = await api.post('/users/reset', data);
    return response.data;
  },
};
