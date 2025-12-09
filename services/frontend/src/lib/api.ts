import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Создаем экземпляр axios с базовыми настройками
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерсептор для добавления токена к запросам
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерсептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Токен истек или невалиден
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        // Перенаправление через Next.js router произойдет в компонентах
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Конвертирует ошибку API в читаемую строку.
 * Гарантирует, что всегда возвращается строка, а не объект.
 * 
 * @param err - Объект ошибки (обычно AxiosError)
 * @param defaultMessage - Сообщение по умолчанию
 * @returns Строка с описанием ошибки
 */
export function formatApiError(err: unknown, defaultMessage: string = 'Произошла ошибка'): string {
  // Проверяем что err является объектом с нужными полями
  if (!err || typeof err !== 'object') {
    return defaultMessage;
  }

  const error = err as any; // Используем any для доступа к полям после проверки

  // Если у ошибки есть response.data.detail
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    // Если detail - объект с полем message (например, {code, message})
    if (typeof detail === 'object' && detail !== null) {
      if (detail.message && typeof detail.message === 'string') {
        return detail.message;
      }
      if (detail.error && typeof detail.error === 'string') {
        return detail.error;
      }
      // Если объект без известных полей - возвращаем дефолтное сообщение
      // (чтобы не раскрывать внутреннюю структуру ошибки пользователю)
      return defaultMessage;
    }
    
    // Если detail - строка, возвращаем её
    if (typeof detail === 'string') {
      return detail;
    }
  }
  
  // Если есть response.data.error
  if (error.response?.data?.error && typeof error.response.data.error === 'string') {
    return error.response.data.error;
  }
  
  // Если есть response.data как строка
  if (error.response?.data && typeof error.response.data === 'string') {
    return error.response.data;
  }
  
  // Если есть message в самой ошибке
  if (error.message && typeof error.message === 'string') {
    return error.message;
  }
  
  // Возвращаем сообщение по умолчанию
  return defaultMessage;
}

/**
 * Извлекает код ошибки из ответа API, если он доступен.
 * 
 * @param err - Объект ошибки
 * @returns Код ошибки или null
 */
export function getApiErrorCode(err: unknown): string | null {
  if (!err || typeof err !== 'object') {
    return null;
  }

  const error = err as any;

  // Проверяем наличие кода в response.data.detail
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    if (typeof detail === 'object' && detail !== null && detail.code) {
      return String(detail.code);
    }
  }

  // Проверяем наличие кода напрямую в response.data
  if (error.response?.data?.code) {
    return String(error.response.data.code);
  }

  return null;
}

export default api;
