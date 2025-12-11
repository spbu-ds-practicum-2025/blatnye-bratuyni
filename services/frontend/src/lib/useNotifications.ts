'use client';

import { useState, useCallback } from 'react';

interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
}

let notificationCounter = 0;

// // push: Hook для управления уведомлениями пользователя
export function useNotifications() {
  const [currentNotification, setCurrentNotification] = useState<Notification | null>(null);
  const [notificationHistory, setNotificationHistory] = useState<Notification[]>([]);

  // Показать новое уведомление
  const showNotification = useCallback((title: string, message: string, type: string = 'info') => {
    notificationCounter++;
    const notification: Notification = {
      id: notificationCounter,
      title,
      message,
      type,
    };
    
    setCurrentNotification(notification);
    setNotificationHistory((prev) => [notification, ...prev]);
  }, []);

  // Закрыть текущее уведомление
  const closeNotification = useCallback(() => {
    setCurrentNotification(null);
  }, []);

  return {
    currentNotification,
    notificationHistory,
    showNotification,
    closeNotification,
  };
}
