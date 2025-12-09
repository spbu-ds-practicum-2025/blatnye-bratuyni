'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { bookingService, adminService, notificationService } from '@/lib/booking';
import { authService } from '@/lib/auth';
import { formatApiError } from '@/lib/api';
import { Zone } from '@/types';
import { formatMoscowTime, fromMoscowDatetimeLocal } from '@/lib/timezone';

export default function AdminPage() {
  const router = useRouter();
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [showBulkNotificationModal, setShowBulkNotificationModal] = useState(false);
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);

  const [createForm, setCreateForm] = useState({
    name: '',
    address: '',
    is_active: true,
    places_count: 10,
  });

  const [editForm, setEditForm] = useState({
    name: '',
    address: '',
    is_active: true,
  });

  const [closeForm, setCloseForm] = useState({
    reason: '',
    from_time: '',
    to_time: '',
  });

  // // уведомления: Форма для массовой рассылки
  const [bulkNotificationForm, setBulkNotificationForm] = useState({
    subject: '',
    text: '',
  });

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadZones();
  }, []);

  const loadZones = async () => {
    try {
      const zonesData = await adminService.getAdminZones();
      setZones(zonesData);
      setLoading(false);
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/login');
      } else {
        setError('Ошибка загрузки зон');
      }
      setLoading(false);
    }
  };

  const handleCreateZone = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminService.createZone(createForm);
      alert('Зона создана успешно');
      setShowCreateModal(false);
      setCreateForm({ name: '', address: '', is_active: true, places_count: 10 });
      loadZones();
    } catch (err: any) {
      // Конвертируем ошибку API в строку для безопасного отображения
      const errorMessage = formatApiError(err, 'Ошибка создания зоны');
      alert(errorMessage);
    }
  };

  const handleEditZone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedZone) return;

    try {
      await adminService.updateZone(selectedZone.id, editForm);
      alert('Зона обновлена успешно');
      setShowEditModal(false);
      setSelectedZone(null);
      loadZones();
    } catch (err: any) {
      // Конвертируем ошибку API в строку для безопасного отображения
      const errorMessage = formatApiError(err, 'Ошибка обновления зоны');
      alert(errorMessage);
    }
  };

  const handleDeleteZone = async (zoneId: number) => {
    if (!confirm('Вы уверены, что хотите удалить эту зону?')) {
      return;
    }

    try {
      await adminService.deleteZone(zoneId);
      alert('Зона удалена успешно');
      loadZones();
    } catch (err: any) {
      // Конвертируем ошибку API в строку для безопасного отображения
      const errorMessage = formatApiError(err, 'Ошибка удаления зоны');
      alert(errorMessage);
    }
  };

  const handleCloseZone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedZone) return;

    try {
      const affectedBookings = await adminService.closeZone(selectedZone.id, {
        reason: closeForm.reason,
        from_time: fromMoscowDatetimeLocal(closeForm.from_time),
        to_time: fromMoscowDatetimeLocal(closeForm.to_time),
      });
      alert(
        `Зона закрыта. Отменено бронирований: ${affectedBookings.length}`
      );
      setShowCloseModal(false);
      setSelectedZone(null);
      setCloseForm({ reason: '', from_time: '', to_time: '' });
      loadZones();
    } catch (err: any) {
      // Конвертируем ошибку API в строку для безопасного отображения
      const errorMessage = formatApiError(err, 'Ошибка закрытия зоны');
      alert(errorMessage);
    }
  };

  // // уведомления: Обработчик отправки массовой рассылки
  const handleSendBulkNotification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bulkNotificationForm.subject || !bulkNotificationForm.text) {
      alert('Заполните все поля');
      return;
    }

    try {
      const result = await notificationService.sendBulkEmail(
        bulkNotificationForm.subject,
        bulkNotificationForm.text
      );
      alert(
        `Массовая рассылка завершена!\nОтправлено: ${result.sent}\nНе удалось: ${result.failed}\nВсего: ${result.total}`
      );
      setShowBulkNotificationModal(false);
      setBulkNotificationForm({ subject: '', text: '' });
    } catch (err: any) {
      // Конвертируем ошибку API в строку для безопасного отображения
      const errorMessage = formatApiError(err, 'Ошибка отправки рассылки');
      alert(errorMessage);
    }
  };

  const openEditModal = (zone: Zone) => {
    setSelectedZone(zone);
    setEditForm({
      name: zone.name,
      address: zone.address || '',
      is_active: zone.is_active,
    });
    setShowEditModal(true);
  };

  const openCloseModal = (zone: Zone) => {
    setSelectedZone(zone);
    setShowCloseModal(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Админ-панель</h1>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowBulkNotificationModal(true)}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
            >
              📧 Массовая рассылка
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              + Создать зону
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
        )}

        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Управление зонами</h2>
          <div className="space-y-4">
            {zones.map((zone) => (
              <div
                key={zone.id}
                className="border rounded-lg p-4 flex justify-between items-start"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold">{zone.name}</h3>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        zone.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {zone.is_active ? 'Активен' : 'Закрыт'}
                    </span>
                  </div>
                  {zone.address && (
                    <p className="text-gray-600 mb-1">{zone.address}</p>
                  )}
                  <p className="text-sm text-gray-500 mb-2">ID: {zone.id}</p>

                  <div className="flex flex-wrap gap-4 mb-2">
                    <div className="text-sm">
                      <span className="font-medium text-green-700">
                        Активных бронирований: {zone.active_bookings}
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="font-medium text-red-700">
                        Отменённых: {zone.cancelled_bookings}
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="font-medium text-blue-700">
                        Пользователей сейчас в коворкинге: {zone.current_occupancy}
                      </span>
                    </div>
                  </div>

                  {!zone.is_active && (
                    <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded">
                      {zone.closure_reason && (
                        <p className="text-sm text-yellow-800 mb-1">
                          <span className="font-medium">Причина закрытия:</span> {zone.closure_reason}
                        </p>
                      )}
                      {zone.closed_until && (
                        <p className="text-sm text-yellow-800">
                          <span className="font-medium">Дата открытия:</span>{' '}
                          {formatMoscowTime(zone.closed_until)}
                        </p>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => openEditModal(zone)}
                    className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Редактировать
                  </button>
                  <button
                    onClick={() => openCloseModal(zone)}
                    className="px-3 py-2 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
                  >
                    Закрыть
                  </button>
                  <button
                    onClick={() => handleDeleteZone(zone.id)}
                    className="px-3 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    Удалить
                  </button>
                </div>
              </div>
            ))}
            {zones.length === 0 && (
              <p className="text-gray-500 text-center py-4">Нет зон</p>
            )}
          </div>
        </div>
      </div>

      {/* Модальное окно создания зоны */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Создать зону</h2>
            <form onSubmit={handleCreateZone} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название
                </label>
                <input
                  type="text"
                  required
                  value={createForm.name}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, name: e.target.value })
                  }
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Адрес (опционально)
                </label>
                <input
                  type="text"
                  value={createForm.address}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, address: e.target.value })
                  }
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Количество мест
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  value={createForm.places_count}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, places_count: parseInt(e.target.value) || 1 })
                  }
                  className="input-field"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="create-is-active"
                  checked={createForm.is_active}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, is_active: e.target.checked })
                  }
                  className="mr-2"
                />
                <label htmlFor="create-is-active" className="text-sm text-gray-700">
                  Активна
                </label>
              </div>

              <div className="flex space-x-2">
                <button type="submit" className="btn-primary flex-1">
                  Создать
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary flex-1"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Модальное окно редактирования зоны */}
      {showEditModal && selectedZone && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Редактировать зону</h2>
            <form onSubmit={handleEditZone} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Адрес (опционально)
                </label>
                <input
                  type="text"
                  value={editForm.address}
                  onChange={(e) =>
                    setEditForm({ ...editForm, address: e.target.value })
                  }
                  className="input-field"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="edit-is-active"
                  checked={editForm.is_active}
                  onChange={(e) =>
                    setEditForm({ ...editForm, is_active: e.target.checked })
                  }
                  className="mr-2"
                />
                <label htmlFor="edit-is-active" className="text-sm text-gray-700">
                  Активна
                </label>
              </div>

              <div className="flex space-x-2">
                <button type="submit" className="btn-primary flex-1">
                  Сохранить
                </button>
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="btn-secondary flex-1"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Модальное окно закрытия зоны */}
      {showCloseModal && selectedZone && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">
              Закрыть зону: {selectedZone.name}
            </h2>
            <form onSubmit={handleCloseZone} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Причина
                </label>
                <input
                  type="text"
                  required
                  value={closeForm.reason}
                  onChange={(e) =>
                    setCloseForm({ ...closeForm, reason: e.target.value })
                  }
                  className="input-field"
                  placeholder="Плановая уборка"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Время начала
                </label>
                <input
                  type="datetime-local"
                  required
                  value={closeForm.from_time}
                  onChange={(e) =>
                    setCloseForm({ ...closeForm, from_time: e.target.value })
                  }
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Время окончания
                </label>
                <input
                  type="datetime-local"
                  required
                  value={closeForm.to_time}
                  onChange={(e) =>
                    setCloseForm({ ...closeForm, to_time: e.target.value })
                  }
                  className="input-field"
                />
              </div>

              <div className="text-sm text-gray-600">
                <p>Время указывается по московскому часовому поясу (МСК)</p>
              </div>

              <div className="flex space-x-2">
                <button type="submit" className="btn-primary flex-1">
                  Закрыть зону
                </button>
                <button
                  type="button"
                  onClick={() => setShowCloseModal(false)}
                  className="btn-secondary flex-1"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Модальное окно массовой рассылки */}
      {showBulkNotificationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Массовая рассылка всем пользователям</h2>
            <form onSubmit={handleSendBulkNotification} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Тема письма
                </label>
                <input
                  type="text"
                  required
                  value={bulkNotificationForm.subject}
                  onChange={(e) =>
                    setBulkNotificationForm({ ...bulkNotificationForm, subject: e.target.value })
                  }
                  className="input-field"
                  placeholder="Важное объявление"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Текст сообщения
                </label>
                <textarea
                  required
                  rows={6}
                  value={bulkNotificationForm.text}
                  onChange={(e) =>
                    setBulkNotificationForm({ ...bulkNotificationForm, text: e.target.value })
                  }
                  className="input-field"
                  placeholder="Введите текст сообщения для всех пользователей..."
                />
              </div>

              <div className="text-sm text-gray-600 bg-yellow-50 p-3 rounded">
                <p className="font-medium">⚠️ Внимание:</p>
                <p>Сообщение будет отправлено на email всем подтверждённым пользователям системы.</p>
              </div>

              <div className="flex space-x-2">
                <button type="submit" className="btn-primary flex-1">
                  Отправить всем
                </button>
                <button
                  type="button"
                  onClick={() => setShowBulkNotificationModal(false)}
                  className="btn-secondary flex-1"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}