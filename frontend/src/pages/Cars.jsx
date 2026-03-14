import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Car as CarIcon, RefreshCw, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { apiClient } from '../api/axios';
const JPY_TO_RUB = 0.62;

export default function Cars() {
    const navigate = useNavigate();

    // Стейт для текущей страницы (начинается с 0, так как математика offset = page * limit)
    const[page, setPage] = useState(0);
    const limit = 20; // Сколько авто показываем на одной странице

    // Fetcher теперь принимает queryKey, внутри которого "зашита" текущая страница
    const fetchCars = async ({ queryKey }) => {
        const [_key, pageIndex] = queryKey;
        const offset = pageIndex * limit;

        // Передаем Query-параметры в FastAPI
        const response = await apiClient.get('/cars', {
            params: { limit, offset }
        });
        return response.data;
    };

    // React Query автоматически делает рефетч, когда 'page' меняется
    const { data: cars =[], isLoading, isError, refetch, isFetching } = useQuery({
        queryKey: ['cars', page], // Массив зависимостей: при смене page, запрос улетит заново
        queryFn: fetchCars,
        placeholderData: keepPreviousData, // UX фишка: оставляем старые данные на экране, пока грузятся новые
    });

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <div className="glass-container large">
            <div className="header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <CarIcon size={28} color="var(--accent)" />
                    <h2>База Автообъявлений</h2>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="btn-secondary" onClick={() => refetch()} title="Обновить">
                        <RefreshCw size={18} className={isFetching ? "loading-spinner" : ""} />
                    </button>
                    <button className="btn-secondary" onClick={handleLogout} title="Выход">
                        <LogOut size={18} />
                    </button>
                </div>
            </div>

            {isError && <div className="error-text">Ошибка загрузки данных с сервера</div>}

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Фото</th>
                            <th>ID</th>
                            <th>AI Анализ</th> {/* 🔥 НОВАЯ КОЛОНКА */}
                            <th>Марка</th>
                            <th>Модель</th>
                            <th>Год</th>
                            <th>Пробег</th>
                            <th>Цена (₽)</th>
                            <th>Цвет</th>
                            <th>Ссылка</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading ? (
                            <tr>
                                <td colSpan="10" style={{ textAlign: 'center', padding: '2rem' }}>
                                    Загрузка данных...
                                </td>
                            </tr>
                        ) : cars.length > 0 ? (
                            cars.map((car) => (
                                <tr key={car.id}>
                                    {/* Фото */}
                                    <td>
                                        {car.image_url ? (
                                            <img
                                                src={car.image_url}
                                                alt={car.model}
                                                style={{ width: '80px', height: '60px', objectFit: 'cover', borderRadius: '4px' }}
                                                onError={(e) => { e.target.src = 'https://placehold.co/80x60?text=No+Photo' }}
                                            />
                                        ) : (
                                            <div style={{ width: '80px', height: '60px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem' }}>
                                                No Photo
                                            </div>
                                        )}
                                    </td>

                                    <td>{car.id}</td>

                                    {/* 🔥 AI ОПИСАНИЕ */}
                                    <td style={{ maxWidth: '200px' }}>
                                        {car.ai_description ? (
                                            <div title={car.ai_description} style={{ cursor: 'help' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#fbbf24', marginBottom: '4px' }}>
                                                    <Sparkles size={14} />
                                                    <span style={{ fontSize: '0.7rem', fontWeight: 'bold' }}>AI READY</span>
                                                </div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                    {car.ai_description}
                                                </div>
                                            </div>
                                        ) : (
                                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Ожидает...</span>
                                        )}
                                    </td>

                                    <td>{car.brand}</td>
                                    <td>{car.model}</td>
                                    <td>{car.year}</td>

                                    <td>
                                        {car.mileage ? new Intl.NumberFormat('ru-RU').format(car.mileage) + ' км' : '-'}
                                    </td>

                                    <td>
                                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                                            <span style={{ fontWeight: 'bold' }}>
                                                {new Intl.NumberFormat('ru-RU').format(Math.round(car.price * JPY_TO_RUB))} ₽
                                            </span>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                ¥ {new Intl.NumberFormat('ja-JP').format(car.price)}
                                            </span>
                                        </div>
                                    </td>
                                    <td>{car.color}</td>
                                    <td>
                                        <a href={car.link} target="_blank" rel="noopener noreferrer">
                                            Открыть
                                        </a>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan="10" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                                    Объявлений больше нет.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* ПАГИНАЦИЯ (остается без изменений) */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '1.5rem',
                paddingTop: '1rem',
                borderTop: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
                <button
                    className="btn-secondary"
                    style={{ display: 'flex', gap: '5px', opacity: page === 0 ? 0.5 : 1 }}
                    onClick={() => setPage((old) => Math.max(old - 1, 0))}
                    disabled={page === 0 || isFetching}
                >
                    <ChevronLeft size={18} /> Назад
                </button>

                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    Страница {page + 1}
                </span>

                <button
                    className="btn-secondary"
                    style={{ display: 'flex', gap: '5px', opacity: cars.length < limit ? 0.5 : 1 }}
                    onClick={() => setPage((old) => old + 1)}
                    disabled={cars.length < limit || isFetching}
                >
                    Вперед <ChevronRight size={18} />
                </button>
            </div>
        </div>
    );
}