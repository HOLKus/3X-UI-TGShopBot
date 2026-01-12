import aiohttp
import uuid
import json
import logging
import random
from config import config
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class XUIAPI:
    def __init__(self):
        self.session = None
        self.cookie_jar = aiohttp.CookieJar(unsafe=True)
        self.auth_cookies = None
        # Базовая подготовка URL
        self.api_url = config.XUI_API_URL.rstrip('/')
        self.base_path = config.XUI_BASE_PATH.strip('/')
        
        if self.base_path:
            self.full_base_url = f"{self.api_url}/{self.base_path}"
        else:
            self.full_base_url = self.api_url

    async def login(self):
        """Аутентификация в 3x-UI API"""
        try:
            self.session = aiohttp.ClientSession(
                cookie_jar=self.cookie_jar,
                trust_env=True
            )
            
            auth_data = {
                "username": config.XUI_USERNAME,
                "password": config.XUI_PASSWORD
            }
            
            login_url = f"{self.full_base_url.rstrip('/')}/login"
            logger.info(f"ℹ️ Trying login to {login_url} with user: {config.XUI_USERNAME}")
            
            async with self.session.post(login_url, data=auth_data, ssl=False) as resp:
                if resp.status != 200:
                    logger.error(f"🛑 Login failed with status: {resp.status}")
                    return False
                
                try:
                    response = await resp.json()
                    if response.get("success"):
                        logger.info("✅ Login successful")
                        return True
                    else:
                        logger.error(f"🛑 Login failed: {response.get('msg')}")
                        return False
                except:
                    text = await resp.text()
                    if "success" in text.lower():
                        logger.info("✅ Login successful (text response)")
                        return True
                    return False
        except Exception as e:
            logger.exception(f"🛑 Login error: {e}")
            return False

    async def _request(self, method, path, **kwargs):
        """Универсальный метод запроса с перебором путей API"""
        # Список возможных префиксов API в разных версиях панелей
        prefixes = ["/api/inbounds", "/panel/api/inbounds", "/xui/API/inbounds"]
        
        for prefix in prefixes:
            url = f"{self.full_base_url.rstrip('/')}{prefix}{path}"
            try:
                if method == "GET":
                    async with self.session.get(url, ssl=False, **kwargs) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("success"):
                                return data.get("obj")
                elif method == "POST":
                    async with self.session.post(url, ssl=False, **kwargs) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("success"):
                                return data.get("obj") if "get" in path else True
            except Exception:
                continue
        return None

    async def get_inbound(self, inbound_id: int):
        """Получение данных инбаунда"""
        return await self._request("GET", f"/get/{inbound_id}")

    async def update_inbound(self, inbound_id: int, data: dict):
        """Обновление инбаунда"""
        return await self._request("POST", f"/update/{inbound_id}", json=data)

    async def create_vless_profile(self, telegram_id: int):
        if not await self.login():
            return None
        
        inbound = await self.get_inbound(config.INBOUND_ID)
        if not inbound: return None
        
        try:
            import time
            settings = json.loads(inbound["settings"])
            clients = settings.get("clients", [])
            
            client_id = str(uuid.uuid4())
            email = f"user_{telegram_id}_{random.randint(1000,9999)}"
            
            # Установка срока: текущее время + 3 дня в миллисекундах
            # 3 дня = 3 * 24 * 60 * 60 * 1000 = 259,200,000 мс
            expire_at = int((time.time() + (3 * 24 * 60 * 60)) * 1000)
            
            new_client = {
                "id": client_id,
                "flow": "",
                "email": email,
                "limitIp": 0,
                "totalGB": 0,
                "expiryTime": expire_at, # Теперь не 0, а +3 дня
                "enable": True,
                "tgId": str(telegram_id),
                "subId": "",
                "reset": 0,
                "fingerprint": config.REALITY_FINGERPRINT,
                "publicKey": config.REALITY_PUBLIC_KEY,
                "shortId": config.REALITY_SHORT_ID.split(',')[0],
                "spiderX": config.REALITY_SPIDER_X
            }
            
            clients.append(new_client)
            settings["clients"] = clients
            
            update_data = {
                "up": inbound["up"], "down": inbound["down"], "total": inbound["total"],
                "remark": inbound["remark"], "enable": inbound["enable"], "expiryTime": inbound["expiryTime"],
                "listen": inbound["listen"], "port": inbound["port"], "protocol": inbound["protocol"],
                "settings": json.dumps(settings, indent=2),
                "streamSettings": inbound["streamSettings"],
                "sniffing": inbound["sniffing"]
            }
            
            if await self.update_inbound(config.INBOUND_ID, update_data):
                return {
                    "client_id": client_id,
                    "email": email,
                    "port": inbound["port"],
                    "security": "reality",
                    "remark": inbound["remark"]
                }
            return None
        except Exception as e:
            logger.exception(f"🛑 Create profile error: {e}")
            return None

    async def get_user_stats(self, email: str):
        if not await self.login(): return {"upload": 0, "download": 0}
        res = await self._request("GET", f"/getClientTraffics/{email}")
        if res:
            return {"upload": res.get("up", 0), "download": res.get("down", 0)}
        return {"upload": 0, "download": 0}

    async def get_online_users(self):
        if not await self.login(): return 0
        res = await self._request("POST", "/onlines")
        if res and isinstance(res, list):
            return len([u for u in res if "user_" in str(u)])
        return 0

    async def close(self):
        if self.session:
            await self.session.close()

# Функции-обертки
# Исправленные обертки для вызова функций из handlers.py
async def create_vless_profile(telegram_id: int):
    api = XUIAPI()
    try: return await api.create_vless_profile(telegram_id)
    finally: await api.close()

async def create_static_client(profile_name: str):
    api = XUIAPI()
    try: return await api.create_static_client(profile_name)
    finally: await api.close()

async def delete_client_by_email(email: str):
    api = XUIAPI()
    try: return await api.delete_client(email)
    finally: await api.close()

async def get_global_stats():
    api = XUIAPI()
    try: return await api.get_global_stats(config.INBOUND_ID)
    finally: await api.close()

async def get_online_users():
    api = XUIAPI()
    try: return await api.get_online_users()
    finally: await api.close()

async def get_user_stats(email: str):
    api = XUIAPI()
    try: return await api.get_user_stats(email)
    finally: await api.close()

def generate_vless_url(profile_data: dict) -> str:
    from config import config
    remark = profile_data.get('remark', 'VPN')
    email = profile_data['email']
    pbk = config.REALITY_PUBLIC_KEY.strip()
    fp = config.REALITY_FINGERPRINT.strip()
    sni = config.REALITY_SNI.split(',')[0].strip()
    sid = config.REALITY_SHORT_ID.split(',')[0].strip()
    
    return (
        f"vless://{profile_data['client_id']}@{config.XUI_HOST}:{profile_data['port']}"
        f"?type=tcp&security=reality&pbk={pbk}&fp={fp}"
        f"&sni={sni}&sid={sid}&spx=%2F#{remark}-{email}"
    )