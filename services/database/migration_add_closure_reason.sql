-- Миграция: добавление поля closure_reason и починка временных полей в таблице zones
-- Дата: 2025-12-07

-- Добавить колонку is_active (оставляем как есть)
ALTER TABLE bookings.zones 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL;

-- Починить тип временных колонок (если вдруг остался TIMESTAMP БЕЗ TIME ZONE)
ALTER TABLE bookings.zones
ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';

ALTER TABLE bookings.zones
ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC';

-- Сделать DEFAULT NOW() явным для created_at и updated_at
ALTER TABLE bookings.zones ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE bookings.zones ALTER COLUMN updated_at SET DEFAULT NOW();

-- Добавить closure_reason
ALTER TABLE bookings.zones 
ADD COLUMN IF NOT EXISTS closure_reason TEXT DEFAULT NULL;