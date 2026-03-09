#### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ainj
```

#### 2. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните `.env` своими данными:

```env
BOT_TOKEN=your_telegram_bot_token_here
GIGACHAT_KEY=your_gigachat_credentials_here
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat-Pro
DATABASE_PATH=users.db
LOG_LEVEL=INFO

# Search Configuration
ENABLE_SEARCH=true
SEARCH_MAX_RESULTS=5
SEARCH_CACHE_TTL=86400
```

#### Получение токенов:

**Telegram Bot Token:**
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

**GigaChat API Key:**
1. Зарегистрируйтесь на [developers.sber.ru](https://developers.sber.ru/)
2. Создайте проект
3. Получите credentials для GigaChat API

#### 3. Запуск с Docker Compose

```bash
# Создать и запустить контейнер
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановить контейнер
docker-compose down

# Перезапустить контейнер
docker-compose restart
```

#### 4. Управление контейнером

```bash
# Просмотр статуса
docker-compose ps

# Остановить и удалить контейнер с данными
docker-compose down -v

# Пересобрать образ
docker-compose build --no-cache

# Обновить и перезапустить
docker-compose up -d --build
```
