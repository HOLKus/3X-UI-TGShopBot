#!/bin/bash
# 1. Убиваем всё, что висит на порту 8501
fuser -k 8501/tcp
# 2. Запускаем панель строго на этом порту
streamlit run admin_panel.py --server.port 8501 --server.headless true
