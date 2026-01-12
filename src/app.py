import json
import asyncio
import logging
import warnings
import coloredlogs
from config import config
from aiogram import Bot, Dispatcher
from aiogram.types import PreCheckoutQuery
from handlers import setup_handlers
from datetime import datetime, timedelta
from functions import delete_client_by_email
from database import Session, User, init_db, get_all_users, delete_user_profile

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Настройка логирования
coloredlogs.install(level='info')
logger = logging.getLogger(__name__)

async def check_subscriptions(bot: Bot):
    """Проверка статуса подписок"""
    while True:
        try:
            now = datetime.utcnow()
            users = await get_all_users()
            
            for user in users:
                # Проверка за 1 день до окончания
                if user.subscription_end:
                    time_diff = user.subscription_end - now
                    
                    # Уведомление за 24 часа
                    if timedelta(days=0) < time_diff < timedelta(days=1) and not user.notified:
                        try:
                            await bot.send_message(
                                user.telegram_id,
                                "⚠️ Ваша подписка истекает через 24 часа! Продлите подписку, чтобы сохранить доступ."
                            )
                            # Помечаем как уведомленного
                            with Session() as session:
                                db_user = session.query(User).filter_by(telegram_id=user.telegram_id).first()
                                if db_user:
                                    db_user.notified = True
                                    session.commit()
                        except Exception as e:
                            logger.error(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")

                    # Отключение при истечении срока
                    if time_diff <= timedelta(seconds=0):
                        try:
                            if user.vless_profile_data:
                                profile = json.loads(user.vless_profile_data)
                                email = profile.get("email")
                                if email:
                                    # Удаляем клиента из 3X-UI через API
                                    if await delete_client_by_email(email):
                                        # Очищаем данные профиля в БД бота
                                        await delete_user_profile(user.telegram_id)
                                        await bot.send_message(
                                            user.telegram_id, 
                                            "❌ Ваша подписка истекла. Доступ к VPN отключен."
                                        )
                                        logger.info(f"Подписка пользователя {user.telegram_id} истекла, профиль удален.")
                        except Exception as e:
                            logger.error(f"Ошибка при удалении профиля {user.telegram_id}: {e}")
                            
        except Exception as e:
            logger.error(f"Ошибка в цикле проверки подписок: {e}")
            
        # Проверка каждый час
        await asyncio.sleep(3600)

async def update_admins_status():
    """Обновляет статус администраторов в БД на основе конфигурации"""
    with Session() as session:
        # Сбрасываем текущих админов (кроме тех, кто в конфиге)
        session.query(User).update({User.is_admin: False})
        
        for admin_id in config.ADMINS:
            user = session.query(User).filter_by(telegram_id=admin_id).first()
            if user:
                user.is_admin = True
            else:
                # Если админа нет в БД, создаем запись
                new_admin = User(
                    telegram_id=admin_id,
                    full_name="Admin",
                    is_admin=True,
                    subscription_end=datetime.utcnow() + timedelta(days=365)
                )
                session.add(new_admin)
        
        session.commit()
    logger.info("✅ Admin status updated in database")

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    try:
        # Инициализация БД (создание таблиц)
        await init_db()
        logger.info("✅ Database initialized")

        # Обновляем статус администраторов из config.py
        await update_admins_status()
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        return
    
    try:
        # Регистрация обработчиков команд и кнопок
        setup_handlers(dp)
        logger.info("✅ Handlers registered")
    except Exception as e:
        logger.error(f"❌ Handler registration error: {e}")
        return
    
    # Обработчик для платежей (обязателен для работы с Telegram Payments)
    @dp.pre_checkout_query()
    async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    
    # Запускаем фоновую задачу проверки подписок
    try:
        asyncio.create_task(check_subscriptions(bot))
    except Exception as e:
        logger.error(f"❌ Subscription check task failed to start: {e}")
    
    logger.info("ℹ️  Starting bot...")
    try:
        # Удаляем вебхук перед запуском polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Bot start error: {e}")
        return

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")