import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        try {
            // In Docker Compose, React will run on the browser and access the API via localhost
            // Note: We use relative path if we set proxy, or absolute if direct
            // Assuming api and frontend are mapped, we fetch to the standard Docker port
            const response = await fetch('http://localhost:8000/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            if (!response.ok) {
                throw new Error('Invalid credentials');
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            navigate('/');
        } catch (err) {
            setError('Ошибка авторизации. Проверьте логин и пароль.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-container">
            <div className="header">
                <h2>Cars Service Control Panel</h2>
            </div>

            {error && <div className="error-text">{error}</div>}

            <form onSubmit={handleLogin}>
                <input
                    type="email"
                    className="input-field"
                    placeholder="Email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                <input
                    type="password"
                    className="input-field"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <button type="submit" className="btn-primary" disabled={loading}>
                    {loading ? 'Вход...' : (
                        <>
                            <LogIn size={20} />
                            Вход в систему
                        </>
                    )}
                </button>
            </form>
        </div>
    );
}
