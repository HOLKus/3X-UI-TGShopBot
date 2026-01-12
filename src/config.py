import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict

load_dotenv()

class Config(BaseModel):
    # Основные настройки (берутся из .env или заглушек)
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    ADMINS: List[int] = [] # Будет заполнено через валидатор из .env
    
    # Настройки 3x-ui панели
    XUI_API_URL: str = os.getenv("XUI_API_URL", "http://your-panel-ip:port")
    XUI_BASE_PATH: str = os.getenv("XUI_BASE_PATH", "/panel")
    XUI_USERNAME: str = os.getenv("XUI_USERNAME", "admin")
    XUI_PASSWORD: str = os.getenv("XUI_PASSWORD", "password")
    XUI_HOST: str = os.getenv("XUI_HOST", "your-domain.com")
    XUI_SERVER_NAME: str = os.getenv("XUI_SERVER_NAME", "your-server-name")
    
    # Платежи и ID входящего подключения
    PAYMENT_TOKEN: str = os.getenv("PAYMENT_TOKEN", "")
    INBOUND_ID: int = Field(default=os.getenv("INBOUND_ID", "1"))

    # Настройки REALITY
    REALITY_PUBLIC_KEY: str = os.getenv("REALITY_PUBLIC_KEY", "YOUR_PUBLIC_KEY")
    REALITY_FINGERPRINT: str = os.getenv("REALITY_FINGERPRINT", "chrome")
    REALITY_SNI: str = os.getenv("REALITY_SNI", "google.com")
    REALITY_SHORT_ID: str = os.getenv("REALITY_SHORT_ID", "your_short_id")
    REALITY_SPIDER_X: str = os.getenv("REALITY_SPIDER_X", "/")

    # Настройки цен и скидок
    PRICES: Dict[int, Dict[str, int]] = {
        1: {"base_price": 200, "discount_percent": 0},
        3: {"base_price": 600, "discount_percent": 18},
        6: {"base_price": 1200, "discount_percent": 28},
        12: {"base_price": 2400, "discount_percent": 34}
    }

    @field_validator('ADMINS', mode='before')
    def parse_admins(cls, value):
        if isinstance(value, str):
            return [int(admin) for admin in value.split(",") if admin.strip()]
        if isinstance(value, int):
            return [value]
        return value or []
    
    @field_validator('INBOUND_ID', mode='before')
    def parse_inbound_id(cls, value):
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value if isinstance(value, int) else 1
    
    def calculate_price(self, months: int) -> int:
        """Вычисляет итоговую стоимость с учетом скидки"""
        if months not in self.PRICES:
            return 0
        
        price_info = self.PRICES[months]
        base_price = price_info["base_price"]
        discount_percent = price_info["discount_percent"]
        
        discount_amount = (base_price * discount_percent) // 100
        return base_price - discount_amount

# Инициализация конфига с приоритетом данных из окружения (.env)
config = Config(
    ADMINS=os.getenv("ADMINS", ""),
    INBOUND_ID=os.getenv("INBOUND_ID", "1")
)