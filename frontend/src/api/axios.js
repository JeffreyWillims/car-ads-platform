import axios from 'axios';

// Используем переменную окружения Vite, если есть, иначе фоллбек на localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Перехватчик ЗАПРОСОВ (добавляем токен)
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Перехватчик ОТВЕТОВ (глобальный обработчик 401 ошибки)
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Токен протух или невалиден
            localStorage.removeItem('token');
            window.location.href = '/login'; // Жесткий редирект
        }
        return Promise.reject(error);
    }
);