from pydantic import BaseModel, Field, field_validator


class CarSearchQuery(BaseModel):
    """
    Структура поискового запроса для LLM.
    """
    brand: str | None = Field(None, description="Марка авто (например, BMW, Audi)")
    model: str | None = Field(None, description="Модель авто (например, X5, A4)")

    min_year: int | None = Field(None, description="Минимальный год выпуска")
    max_price: int | None = Field(None, description="Максимальная цена")

    color: str | None = Field(None, description="Цвет автомобиля (на английском)")

    # --- MAGIC FIX ---
    @field_validator('min_year', 'max_price', mode='before')
    @classmethod
    def parse_nullable_int(cls, v):
        # Если LLM прислала строку "null" или "None", превращаем её в Python None
        if isinstance(v, str) and v.lower() in ('null', 'none', ''):
            return None
        return v

    @field_validator('brand', 'model', 'color', mode='before')
    @classmethod
    def parse_nullable_str(cls, v):
        if isinstance(v, str) and v.lower() in ('null', 'none'):
            return None
        return v