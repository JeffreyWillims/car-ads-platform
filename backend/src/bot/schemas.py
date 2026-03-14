from pydantic import BaseModel, Field, field_validator

class CarSearchQuery(BaseModel):
    """
    Структура поискового запроса (Инструмент для LLM).
    """
    brand: str | None = Field(None, description="Марка авто (например, Toyota, Honda, Mazda)")
    model: str | None = Field(None, description="Модель авто (например, Camry, CX-5)")
    min_year: int | None = Field(None, description="Минимальный год выпуска")
    max_price: int | None = Field(None, description="Максимальная цена в йенах (конвертируй рубли в йены, если нужно)")
    color: str | None = Field(None, description="Цвет автомобиля (СТРОГО на английском: White, Black, Red и т.д.)")

    @field_validator('min_year', 'max_price', mode='before')
    @classmethod
    def parse_nullable_int(cls, v):
        if isinstance(v, str) and v.lower() in ('null', 'none', ''):
            return None
        return v

    @field_validator('brand', 'model', 'color', mode='before')
    @classmethod
    def parse_nullable_str(cls, v):
        if isinstance(v, str) and v.lower() in ('null', 'none', ''):
            return None
        return v