import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
            <span className="block text-primary-600">ПУНККроссинг</span>
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Распределённая система бронирования мест в коворкингах кампуса
          </p>
          <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
            <div className="rounded-md shadow">
              <Link
                href="/zones"
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 md:py-4 md:text-lg md:px-10"
              >
                Посмотреть зоны
              </Link>
            </div>
            <div className="mt-3 rounded-md shadow sm:mt-0 sm:ml-3">
              <Link
                href="/register"
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-primary-600 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10"
              >
                Регистрация
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-12">
          <div className="card max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Преимущества системы</h2>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span>Интуитивно понятный интерфейс</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span>Полноценный функционал для быстрого бронирования: создание, отмена, продление и история</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span>Отказоустойчивая и масштабируемая архитектура</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary-600 mr-2">✓</span>
                <span>Высокая производительность и доступность 24/7</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Возможности системы */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">Возможности системы</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            <div className="card text-center">
              <div className="text-primary-600 text-4xl mb-4">⚡</div>
              <h3 className="text-lg font-semibold mb-2">Быстрое бронирование</h3>
              <p className="text-gray-600">
                Забронируйте место в несколько кликов
              </p>
            </div>
            <div className="card text-center">
              <div className="text-primary-600 text-4xl mb-4">💼</div>
              <h3 className="text-lg font-semibold mb-2">Новые вместительные помещения</h3>
              <p className="text-gray-600">
                Есть все необходимое для продуктивной работы
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
