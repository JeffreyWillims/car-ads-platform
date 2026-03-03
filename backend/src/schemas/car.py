from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CarRead(BaseModel):
    id: int
    brand: str
    model: str
    year: int
    price: int
    color: str
    link: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)