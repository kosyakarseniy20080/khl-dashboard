FROM apache/airflow:2.7.3-python3.9

# Копируем requirements до установки, чтобы использовать кэш Docker
COPY requirements.txt /requirements.txt

# Устанавливаем Python-зависимости
# --no-cache-dir уменьшает размер образа
RUN pip install --no-cache-dir -r /requirements.txt

# Если git все же понадобится для dbt deps из github, можно попробовать установить так,
# но пока оставим чистую установку python пакетов.
# USER root
# RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
# USER airflow