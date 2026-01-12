import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict

load_dotenv()

class Config(BaseModel):
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8558912303:AAEe8njZFjI-HBvtXdENzeeVpQkLLVQAlX8")
    ADMINS: List[int] = 710335355
    XUI_API_URL: str = os.getenv("XUI_API_URL", "https://rednl.bot.nu:20753")
    XUI_BASE_PATH: str = os.getenv("XUI_BASE_PATH", "/cW093fmsdv993-ha")
    XUI_USERNAME: str = os.getenv("XUI_USERNAME", "holkus")
    XUI_PASSWORD: str = os.getenv("XUI_PASSWORD", "298317Aa")
    XUI_HOST: str = os.getenv("XUI_HOST", "rednl.bot.nu")
    XUI_SERVER_NAME: str = os.getenv("XUI_SERVER_NAME", "rednl.bot.nu")
    PAYMENT_TOKEN: str = os.getenv("PAYMENT_TOKEN", "390540012:LIVE:86546")
    INBOUND_ID: int = Field(default=os.getenv("INBOUND_ID", "3"))
    REALITY_PUBLIC_KEY: str = os.getenv("REALITY_PUBLIC_KEY", "msHwWuKEcKsHonWdSYSHPFJXYwSkziUloh2673TeAHU")
    REALITY_FINGERPRINT: str = os.getenv("REALITY_FINGERPRINT", "chrome")
    REALITY_SNI: str = os.getenv("REALITY_SNI", "google.com")
    REALITY_SHORT_ID: str = os.getenv("REALITY_SHORT_ID", "70e79f93c1,57,2c4f2e344c1e,4a7a,5f1014,290b238c7ad8c220,8fd5848a,10c798ace7b534")
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
        return value or []
    
    @field_validator('INBOUND_ID', mode='before')
    def parse_inbound_id(cls, value):
        if isinstance(value, str):
            return int(value)
        return value or 15
    
    def calculate_price(self, months: int) -> int:
        """Вычисляет итоговую стоимость с учетом скидки"""
        if months not in self.PRICES:
            return 0
        
        price_info = self.PRICES[months]
        base_price = price_info["base_price"]
        discount_percent = price_info["discount_percent"]
        
        discount_amount = (base_price * discount_percent) // 100
        return base_price - discount_amount

config = Config(
    ADMINS=os.getenv("ADMINS", ""),
    INBOUND_ID=os.getenv("INBOUND_ID", "3")
)
