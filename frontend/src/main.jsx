import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.jsx'
import './index.css'

// Инициализируем клиент с умными настройками
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false, // Не перекачивать данные при переключении вкладок браузера
            retry: 1, // Если запрос упал (например 500), попробовать еще 1 раз
            staleTime: 5 * 60 * 1000, // Кэшировать данные на 5 минут
        },
    },
})

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <App />
        </QueryClientProvider>
    </React.StrictMode>,
)