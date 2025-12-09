'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { authService } from '@/lib/auth';
import { formatApiError } from '@/lib/api';

function ResetForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailFromQuery = searchParams.get('email') || '';
  
  const [formData, setFormData] = useState({
    email: emailFromQuery,
    code: '',
    new_password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (emailFromQuery) {
      setFormData(prev => ({ ...prev, email: emailFromQuery }));
    }
  }, [emailFromQuery]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.new_password !== formData.confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    if (formData.new_password.length < 6) {
      setError('Пароль должен быть не менее 6 символов');
      return;
    }

    setLoading(true);

    try {
      await authService.reset({
        email: formData.email,
        code: formData.code,
        new_password: formData.new_password,
      });
      
      setSuccess(true);
      
      // Перенаправляем на страницу входа через 2 секунды
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (err: any) {
      // Конвертируем ошибку API в строку для безопасного отображения
      const errorMessage = formatApiError(err, 'Неверный код восстановления');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <div className="rounded-md bg-green-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">
                    Пароль успешно изменен!
                  </h3>
                  <div className="mt-2 text-sm text-green-700">
                    <p>Перенаправление на страницу входа...</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Сброс пароля
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Введите код из письма и новый пароль
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-700">{error}</div>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="ivan@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="code" className="block text-sm font-medium text-gray-700">
                Код восстановления
              </label>
              <div className="mt-1">
                <input
                  id="code"
                  name="code"
                  type="text"
                  required
                  maxLength={6}
                  value={formData.code}
                  onChange={handleChange}
                  className="input-field text-center text-2xl tracking-widest"
                  placeholder="000000"
                />
              </div>
              <p className="mt-2 text-sm text-gray-500">
                Код из 6 цифр
              </p>
            </div>

            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">
                Новый пароль
              </label>
              <div className="mt-1">
                <input
                  id="new_password"
                  name="new_password"
                  type="password"
                  required
                  value={formData.new_password}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="Минимум 6 символов"
                />
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Подтвердите пароль
              </label>
              <div className="mt-1">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="Повторите пароль"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Сброс пароля...' : 'Сбросить пароль'}
              </button>
            </div>

            <div className="text-sm text-center">
              <Link href="/login" className="font-medium text-primary-600 hover:text-primary-500">
                Вернуться к входу
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function ResetPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Загрузка...</div>
      </div>
    }>
      <ResetForm />
    </Suspense>
  );
}
