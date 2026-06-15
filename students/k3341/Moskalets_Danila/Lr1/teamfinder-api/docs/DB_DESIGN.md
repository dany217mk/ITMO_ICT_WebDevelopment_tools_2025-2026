# База данных платформы TeamFinder

## 1. Роли пользователей (ENUM)
- `ADMIN` - системный администратор
- `USER` - обычный пользователь

## 2. Уровни владения навыком (ENUM)
- `BEGINNER` - Начинающий
- `INTERMEDIATE` - Средний
- `ADVANCED` - Продвинутый
- `EXPERT` - Эксперт

## 3. Статусы проекта (ENUM)
- `DRAFT` - Черновик
- `OPEN` - Открыт для участников
- `IN_PROGRESS` - В работе
- `COMPLETED` - Завершен
- `ARCHIVED` - В архиве

## 4. Роли в команде (ENUM)
- `LEAD` - Лидер команды
- `MEMBER` - Участник
- `OBSERVER` - Наблюдатель

## 5. Статусы участников команды (ENUM)
- `INVITED` - Приглашен
- `ACTIVE` - Активен
- `LEFT` - Покинул
- `REMOVED` - Исключен

## 6. Статусы задач (ENUM)
- `TODO` - К выполнению
- `IN_PROGRESS` - В процессе
- `REVIEW` - На проверке
- `DONE` - Выполнена

## 7. Приоритеты задач (ENUM)
- `LOW` - Низкий
- `MEDIUM` - Средний
- `HIGH` - Высокий
- `CRITICAL` - Критический

## 8. Важность навыка для проекта (ENUM)
- `NICE_TO_HAVE` - Желательно
- `IMPORTANT` - Важно
- `REQUIRED` - Обязателен

---

## 9. Таблица `users`
Хранит всех пользователей системы.

**Поля:**
- `id` (PK, BIGINT) - уникальный идентификатор
- `role` (ENUM) - роль: ADMIN, USER
- `first_name` (VARCHAR(64)) - имя
- `last_name` (VARCHAR(64)) - фамилия
- `email` (VARCHAR(255), UNIQUE) - электронная почта
- `password_hash` (VARCHAR(255)) - хеш пароля
- `avatar_url` (TEXT, NULLABLE) - URL аватара
- `bio` (TEXT, NULLABLE) - информация о пользователе
- `is_verified` (BOOLEAN, DEFAULT false) - подтверждён ли email
- `created_at` (TIMESTAMP, DEFAULT NOW())
- `updated_at` (TIMESTAMP, DEFAULT NOW())

---

## 10. Таблица `skills`
Справочник навыков (программирование, дизайн,管理等).

**Поля:**
- `id` (PK, BIGINT)
- `name` (VARCHAR(128), UNIQUE) - название навыка
- `category` (VARCHAR(64)) - категория (Backend, Frontend,管理等)

---

## 11. Таблица `user_skills`
Ассоциативная сущность (Many-to-Many между `User` и `Skill`). **Имеет дополнительное поле**, характеризующее связь.

**Поля:**
- `user_id` (FK → users.id, PK)
- `skill_id` (FK → skills.id, PK)
- `proficiency_level` (ENUM) - уровень владения навыком (доп. поле)

---

## 12. Таблица `projects`
Проекты, созданные пользователями.

**Поля:**
- `id` (PK, BIGINT)
- `owner_id` (FK → users.id) - владелец проекта
- `title` (VARCHAR(256)) - название
- `description` (TEXT) - описание целей
- `status` (ENUM) - статус проекта
- `deadline` (DATE, NULLABLE) - дедлайн
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

---

## 13. Таблица `project_skills`
Ассоциативная сущность (Many-to-Many между `Project` и `Skill`). **Имеет дополнительное поле**, характеризующее связь.

**Поля:**
- `project_id` (FK → projects.id, PK)
- `skill_id` (FK → skills.id, PK)
- `importance` (ENUM) - требуемый уровень владения (доп. поле)

---

## 14. Таблица `teams`
Команды внутри проекта. Один проект может содержать несколько команд (например, Frontend-команда, Backend-команда).

**Поля:**
- `id` (PK, BIGINT)
- `project_id` (FK → projects.id) - родительский проект
- `created_by` (FK → users.id) - создатель команды
- `name` (VARCHAR(256)) - название команды
- `description` (TEXT, NULLABLE) - описание
- `created_at` (TIMESTAMP)

---

## 15. Таблица `team_members`
Ассоциативная сущность (Many-to-Many между `Team` и `User`). **Имеет дополнительные поля**, характеризующие связь.

**Поля:**
- `team_id` (FK → teams.id, PK)
- `user_id` (FK → users.id, PK)
- `role_in_team` (ENUM) - роль в команде (доп. поле)
- `status` (ENUM) - статус участия (доп. поле)
- `joined_at` (TIMESTAMP) - дата вступления

---

## 16. Таблица `tasks`
Задачи, привязанные к проекту. Назначены конкретному пользователю.

**Поля:**
- `id` (PK, BIGINT)
- `project_id` (FK → projects.id)
- `assignee_id` (FK → users.id, NULLABLE) - исполнитель
- `title` (VARCHAR(256))
- `description` (TEXT, NULLABLE)
- `status` (ENUM)
- `priority` (ENUM)
- `due_date` (DATE, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

---

## 17. Таблица `refresh_tokens`
Хранит refresh-токены для ротации сессий.

**Поля:**
- `id` (PK, BIGINT)
- `user_id` (FK → users.id)
- `token` (VARCHAR(512), UNIQUE)
- `expires_at` (TIMESTAMP)
- `revoked` (BOOLEAN, DEFAULT false)
- `created_at` (TIMESTAMP)