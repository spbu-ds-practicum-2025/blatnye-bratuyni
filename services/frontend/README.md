# Frontend - Система бронирования коворкинга "ПУНККроссинг"

## Обзор

Современный веб-интерфейс для системы бронирования коворкинга, построенный на Next.js 14 с TypeScript. Приложение предоставляет полнофункциональный интерфейс для пользователей и администраторов с чистым, современным дизайном.

## Технологический стек

- **Framework**: Next.js 14 (App Router)
- **Язык**: TypeScript
- **Стилизация**: Tailwind CSS
- **HTTP клиент**: Axios
- **Формы**: React Hook Form + Zod
- **Дата/время**: date-fns

## Структура проекта

```
services/frontend/
├── src/
│   ├── app/                    # Next.js App Router страницы
│   │   ├── admin/             # Админ-панель
│   │   ├── bookings/          # История бронирований
│   │   ├── confirm/           # Подтверждение email
│   │   ├── login/             # Вход
│   │   ├── recover/           # Восстановление пароля
│   │   ├── register/          # Регистрация
│   │   ├── reset/             # Сброс пароля
│   │   ├── zones/             # Просмотр зон и бронирование
│   │   ├── layout.tsx         # Корневой layout
│   │   ├── page.tsx           # Главная страница
│   │   └── globals.css        # Глобальные стили
│   ├── components/            # React компоненты
│   │   └── layout/
│   │       ├── Header.tsx     # Шапка сайта
│   │       └── Footer.tsx     # Подвал сайта
│   ├── lib/                   # Утилиты и сервисы
│   │   ├── api.ts            # Axios инстанс
│   │   ├── auth.ts           # Сервис аутентификации
│   │   └── booking.ts        # Сервис бронирования
│   └── types/                 # TypeScript типы
│       └── index.ts
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
└── README.md
```

## Основные функции

### Аутентификация и авторизация

- **Регистрация** (`/register`): Создание нового аккаунта с валидацией
- **Подтверждение email** (`/confirm`): Ввод 6-значного кода подтверждения
- **Вход** (`/login`): Аутентификация пользователя с JWT токеном
- **Восстановление пароля** (`/recover`): Запрос кода восстановления
- **Сброс пароля** (`/reset`): Установка нового пароля по коду

### Основной функционал

- **Просмотр зон** (`/zones`): 
  - Список всех активных коворкинг-зон
  - Просмотр доступных мест в каждой зоне
  - Выбор даты и просмотр свободных слотов
  - Мгновенное бронирование доступных слотов

- **История бронирований** (`/bookings`):
  - Просмотр всех бронирований пользователя
  - Фильтрация по статусу, датам
  - Отмена активных бронирований
  - Продление бронирований

### Админ-панель

- **Управление зонами** (`/admin`):
  - Создание новых зон коворкинга
  - Редактирование существующих зон
  - Активация/деактивация зон
  - Удаление зон
  - Временное закрытие зон на обслуживание с автоматической отменой бронирований

## API интеграция

Приложение взаимодействует с backend через API Gateway на `http://localhost:8000`.

### Эндпоинты пользователя

- `POST /users/register` - Регистрация
- `POST /users/confirm` - Подтверждение email
- `POST /users/login` - Вход
- `POST /users/recover` - Запрос восстановления пароля
- `POST /users/reset` - Сброс пароля

### Эндпоинты бронирования

- `GET /bookings/zones` - Список зон
- `GET /bookings/zones/{zone_id}/places` - Места в зоне
- `GET /bookings/places/{place_id}/slots?date={date}` - Доступные слоты
- `POST /bookings/` - Создать бронирование
- `POST /bookings/cancel` - Отменить бронирование
- `GET /bookings/bookings/history` - История бронирований
- `POST /bookings/bookings/{booking_id}/extend` - Продлить бронирование

### Эндпоинты администратора

- `POST /bookings/admin/zones` - Создать зону
- `PATCH /bookings/admin/zones/{zone_id}` - Обновить зону
- `DELETE /bookings/admin/zones/{zone_id}` - Удалить зону
- `POST /bookings/admin/zones/{zone_id}/close` - Закрыть зону

## Установка и запуск

### Требования

- Node.js 18+ 
- npm или yarn

### Установка зависимостей

```bash
cd services/frontend
npm install
```

### Настройка окружения

Создайте файл `.env.local`:

```bash
cp .env.local.example .env.local
```

Отредактируйте `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Режим разработки

```bash
npm run dev
```

Приложение будет доступно на `http://localhost:3000`.

### Продакшн сборка

```bash
npm run build
npm start
```

### Линтинг

```bash
npm run lint
```

## Особенности UI/UX

### Дизайн

- Чистый, минималистичный интерфейс
- Адаптивный дизайн для мобильных устройств
- Использование Tailwind CSS для консистентной стилизации
- Цветовая схема в голубых тонах (primary-600)
- Понятная навигация и иерархия страниц

### Пользовательский опыт

- Мгновенная обратная связь при действиях
- Валидация форм в реальном времени
- Информативные сообщения об ошибках
- Loading состояния для асинхронных операций
- Автоматическое перенаправление после успешных операций

### Безопасность

- JWT токены хранятся в localStorage
- Автоматическое добавление токена ко всем API запросам
- Перенаправление на /login при истечении токена (401)
- Защита роутов с проверкой авторизации

## Архитектура

### Организация кода

- **Pages**: Используется App Router Next.js 14 для роутинга
- **Components**: Переиспользуемые React компоненты
- **Services**: Бизнес-логика для взаимодействия с API
- **Types**: TypeScript интерфейсы и типы
- **Styles**: Tailwind CSS классы и глобальные стили

### State Management

- Использование React Hooks (useState, useEffect)
- Локальное состояние компонентов
- JWT токен в localStorage

### Routing

Next.js App Router предоставляет:
- File-based routing
- Server и Client Components
- Layout система
- Loading и Error states

## Разработка

### Добавление новой страницы

1. Создайте директорию в `src/app/`
2. Добавьте `page.tsx` файл
3. Используйте `'use client'` для клиентских компонентов
4. Добавьте навигацию в Header при необходимости

### Добавление нового API эндпоинта

1. Определите TypeScript типы в `src/types/index.ts`
2. Добавьте функцию в соответствующий сервис (`lib/auth.ts` или `lib/booking.ts`)
3. Используйте функцию в компоненте

### Стилизация

Используйте Tailwind CSS классы:

```tsx
<div className="card">              {/* Карточка */}
<button className="btn-primary">   {/* Основная кнопка */}
<button className="btn-secondary"> {/* Вторичная кнопка */}
<input className="input-field">    {/* Поле ввода */}
```

## Интеграция с Docker

Для запуска вместе с остальными сервисами добавьте в `docker-compose.yaml`:

```yaml
frontend:
  build: ./services/frontend
  container_name: coworking-frontend
  ports:
    - "3000:3000"
  environment:
    - NEXT_PUBLIC_API_URL=http://api-gateway:8000
  depends_on:
    - api-gateway
```

## Troubleshooting

### Проблема: CORS ошибки

**Решение**: Убедитесь, что API Gateway правильно настроен для CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Проблема: Токен не сохраняется

**Решение**: Проверьте, что localStorage доступен (не SSR):

```typescript
if (typeof window !== 'undefined') {
  localStorage.setItem('token', token);
}
```

### Проблема: 401 ошибки после входа

**Решение**: Проверьте формат токена в заголовке:

```typescript
Authorization: `Bearer ${token}`
```

## Планы развития

- [ ] Добавить уведомления (toast notifications)
- [ ] Реализовать WebSocket для real-time обновлений
- [ ] Добавить профиль пользователя
- [ ] Реализовать темную тему
- [ ] Добавить i18n поддержку (русский/английский)
- [ ] Интегрировать систему платежей
- [ ] Добавить календарный вид для бронирований
- [ ] Реализовать поиск и фильтрацию зон

## Контакты и поддержка

Для вопросов и предложений создавайте issues в репозитории проекта.

---

**Версия**: 0.1.0  
**Дата последнего обновления**: 2025-12-04
