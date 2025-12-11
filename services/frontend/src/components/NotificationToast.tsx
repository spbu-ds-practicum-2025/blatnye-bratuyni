'use client';

import { useEffect, useState } from 'react';

interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
}

interface NotificationToastProps {
  notification: Notification | null;
  onClose: () => void;
}

// // push: Компонент для отображения всплывающих уведомлений
export default function NotificationToast({ notification, onClose }: NotificationToastProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (notification) {
      setIsVisible(true);
      // Автоматически скрываем уведомление через 5 секунд
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onClose, 300); // Даем время на анимацию исчезновения
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [notification, onClose]);

  if (!notification) return null;

  // Определяем цвет фона в зависимости от типа уведомления
  const getBackgroundColor = () => {
    switch (notification.type) {
      case 'booking_created':
        return 'bg-green-500';
      case 'booking_cancelled':
        return 'bg-red-500';
      case 'booking_extended':
        return 'bg-blue-500';
      case 'zone_closed':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div
      className={`fixed top-4 right-4 z-50 max-w-sm w-full transform transition-all duration-300 ${
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      }`}
    >
      <div className={`${getBackgroundColor()} text-white rounded-lg shadow-lg p-4`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-bold text-lg mb-1">{notification.title}</h3>
            <p className="text-sm">{notification.message}</p>
          </div>
          <button
            onClick={() => {
              setIsVisible(false);
              setTimeout(onClose, 300);
            }}
            className="ml-4 text-white hover:text-gray-200 flex-shrink-0"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
