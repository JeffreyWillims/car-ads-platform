import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Car as CarIcon, RefreshCw } from 'lucide-react';

export default function Cars() {
    const [cars, setCars] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const fetchCars = async () => {
        setLoading(true);
        setError('');
        const token = localStorage.getItem('token');

        if (!token) {
            navigate('/login');
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/api/cars', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                localStorage.removeItem('token');
                navigate('/login');
                return;
            }

            if (!response.ok) {
                throw new Error('Failed to fetch data');
            }

            const data = await response.json();
            setCars(data);
        } catch (err) {
            setError('Ошибка загрузки данных');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCars();
    }, [navigate]);

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
                    <button className="btn-secondary" onClick={fetchCars} title="Обновить">
                        <RefreshCw size={18} className={loading ? "loading-spinner" : ""} />
                    </button>
                    <button className="btn-secondary" onClick={handleLogout} title="Выход">
                        <LogOut size={18} />
                    </button>
                </div>
            </div>

            {error && <div className="error-text">{error}</div>}

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Марка</th>
                            <th>Модель</th>
                            <th>Год</th>
                            <th>Цена (₽)</th>
                            <th>Цвет</th>
                            <th>Ссылка</th>
                            <th>Обновлено</th>
                        </tr>
                    </thead>
                    <tbody>
                        {cars.map((car) => (
                            <tr key={car.id}>
                                <td>{car.id}</td>
                                <td>{car.brand}</td>
                                <td>{car.model}</td>
                                <td>{car.year}</td>
                                <td>
                                    {new Intl.NumberFormat('ru-RU').format(car.price)}
                                </td>
                                <td>{car.color}</td>
                                <td>
                                    <a href={car.link} target="_blank" rel="noopener noreferrer">
                                        Открыть
                                    </a>
                                </td>
                                <td>{new Date(car.updated_at).toLocaleString('ru-RU')}</td>
                            </tr>
                        ))}
                        {cars.length === 0 && !loading && (
                            <tr>
                                <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                                    Объявлений пока нет. Настройте парсер или подождите.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
