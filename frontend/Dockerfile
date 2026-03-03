# ==========================================
# STAGE 1: Build (Сборка React/Vite)
# ==========================================
FROM node:20-alpine AS build

WORKDIR /app

# Копируем манифесты зависимостей
COPY package*.json ./

# 🛠 ИСПРАВЛЕНИЕ: Используем 'npm install' вместо 'npm ci'.
# Это менее строго, но гарантирует, что сборка пройдет,
# даже если package-lock.json отсутствует или рассинхронизирован.
RUN npm install

# Копируем исходный код
COPY . .

# Собираем билд
# ВАЖНО: Убедись, что в package.json в "scripts" есть команда "build"
RUN npm run build

# ==========================================
# STAGE 2: Serve (Запуск Nginx)
# ==========================================
FROM nginx:alpine

# Удаляем дефолтный конфиг
RUN rm /etc/nginx/conf.d/default.conf

# 1. Копируем статику из стадии "build"
# ВАЖНО: Проверь, создает ли твой билд папку 'dist' или 'build'.
# Для Vite это 'dist', для CRA это 'build'.
# Если ошибка повторится на этом шаге - поменяй /app/dist на /app/build
COPY --from=build /app/dist /usr/share/nginx/html

# 2. Копируем наш кастомный конфиг
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]