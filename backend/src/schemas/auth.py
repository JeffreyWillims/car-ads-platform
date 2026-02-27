from pydantic import BaseModel, EmailStr, Field

class Token(BaseModel):
    """
    Возвращается клиенту при успешном логине.
    Строго соответствует спецификации OAuth2.
    """
    access_token: str
    token_type: str = "bearer" # По стандарту всегда 'bearer'


class TokenPayload(BaseModel):
    """
    Данные, которые мы достаем из JWT токена.
    Используется в зависимостях (Dependencies) для проверки прав.
    """
    # Даже если в БД у нас ID - это Integer, здесь мы ждем строку.
    sub: str | None = None


class UserCreate(BaseModel):
    """
    Используется для регистрации нового пользователя.
    Здесь используется EmailStr для надежной валидации формата почты.
    """
    email: EmailStr 
    password: str = Field(min_length=8, description="Пароль минимум 8 символов")