import streamlit as st
import sqlite3
import os
import signal
import psutil
import pandas as pd
import subprocess
import time

# ==========================================
# КОНФИГУРАЦИЯ И ПУТИ
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
DB_PATH = os.path.join(BASE_DIR, "users.db")
LOG_PATH = os.path.join(BASE_DIR, "bot_error.log")

st.set_page_config(page_title="RedWeb Admin Panel", layout="wide")

# Проверка статуса бота
def get_bot_status():
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmd = proc.info.get('cmdline')
            if cmd and any('src/app.py' in s for s in cmd):
                return proc.info['pid']
        except: continue
    return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ RedWeb Control")
    menu = st.radio("Навигация:", ["📊 Мониторинг", "👥 Пользователи", "📝 Редактор кода", "📋 Логи бота"])
    
    st.divider()
    bot_pid = get_bot_status()
    if bot_pid:
        st.success(f"Бот Онлайн (PID: {bot_pid})")
        if st.button("⏹ Остановить бота", use_container_width=True):
            os.kill(bot_pid, signal.SIGTERM)
            st.rerun()
    else:
        st.error("Бот Оффлайн")
        if st.button("▶️ Запустить бота", use_container_width=True):
            subprocess.Popen(["python3", os.path.join(SRC_DIR, "app.py")], 
                             stdout=open(LOG_PATH, "a"), stderr=open(LOG_PATH, "a"), start_new_session=True)
            time.sleep(2)
            st.rerun()

# --- МЕНЮ: ПОЛЬЗОВАТЕЛИ ---
if menu == "👥 Пользователи":
    st.header("👥 База данных пользователей")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        users = conn.execute("SELECT * FROM users").fetchall()
        for row in users:
            with st.expander(f"👤 {row['full_name']} (ID: {row['telegram_id']})"):
                with st.form(key=f"edit_form_{row['id']}"):
                    f_name = st.text_input("Имя", value=row['full_name'])
                    u_name = st.text_input("Username", value=row['username'] or "")
                    s_end = st.text_input("Подписка до", value=str(row['subscription_end'] or ""))
                    is_adm = st.checkbox("Права администратора", value=bool(row['is_admin']))
                    
                    if st.form_submit_button("💾 Сохранить"):
                        conn.execute("UPDATE users SET full_name=?, username=?, is_admin=?, subscription_end=? WHERE id=?", 
                                     (f_name, u_name, 1 if is_adm else 0, s_end, row['id']))
                        conn.commit()
                        st.success("Данные обновлены")
                        st.rerun()
                
                # Кнопка удаления пользователя
                if st.button(f"🗑 Удалить {row['telegram_id']}", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM users WHERE id=?", (row['id'],))
                    conn.commit()
                    st.warning("Пользователь удален")
                    time.sleep(1)
                    st.rerun()
    finally:
        conn.close()

# --- МЕНЮ: РЕДАКТОР ---
elif menu == "📝 Редактор кода":
    st.header("📝 Редактор файлов")
    files = [f for f in os.listdir(SRC_DIR) if f.endswith('.py')]
    target = st.selectbox("Файл:", files)
    path = os.path.join(SRC_DIR, target)
    with open(path, "r", encoding="utf-8") as f: content = f.read()
    new_content = st.text_area("Код:", content, height=500)
    if st.button("💾 Сохранить"):
        with open(path, "w", encoding="utf-8") as f: f.write(new_content)
        st.success("Файл обновлен!")

# --- МЕНЮ: ЛОГИ ---
elif menu == "📋 Логи бота":
    st.header("📋 Журнал событий")
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            st.code(f.read()[-5000:], language="text")