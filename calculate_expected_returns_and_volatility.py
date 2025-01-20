import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import re


# Базовый URL для получения свечей и дивидендов
base_url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{}/candles.json"
dividends_url = "https://iss.moex.com/iss/securities/{}/dividends.json"

def get_dividends(ticker):
    """Получение данных о дивидендах за указанный период."""
    url = f'https://smart-lab.ru/q/{ticker}/f/y/MSFO/download/'
    response = requests.get(url)
    
    # Проверяем, что запрос успешен
    
    data = response.text
    # Разбиваем строки и убираем BOM символы
    lines = data.strip().split("\n")
    lines = [re.sub(r'^', '', line) for line in lines]  # Убираем BOM символ

    # Заголовок таблицы
    header = lines[0].split(";")

    # Разделяем данные по строкам
    rows = [line.split(";") for line in lines[1:]]

    # Создаем DataFrame
    df = pd.DataFrame(rows, columns=header)

    # Убираем кавычки из заголовков и данных
    df.columns = [col.strip('"') for col in df.columns]
    df = df.applymap(lambda x: x.strip('"') if isinstance(x, str) else x)

    dividends_row = df[df.iloc[:, 0].str.startswith('Дивиденд,')]
    if dividends_row.empty:
        print("Не удалось найти данные о чистой прибыли.")
        return False, False

    # Оставляем только столбцы с годами и преобразуем в числовой формат
    year_columns = [col for col in df.columns if col.isdigit()]  # Ищем колонки с годами
    try:
        # Преобразуем строки с данными в числовой формат
        dividends_data = dividends_row[year_columns].iloc[0].apply(lambda x: float(str(x).replace(' ', '').replace(',', '.')) if len(str(x)) != 0 else 0)
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")
        return False, False

    return dividends_data


def get_expected_returns_and_volatility(ticker, years=10, investment_horizon_years=5):
    """Получение годовых цен акции за последние N лет с учетом дивидендов."""
    # Текущая дата
    end_date = datetime.now()
    # Дата N лет назад
    start_date = end_date - timedelta(days=365 * years)
    
    # Параметры запроса
    params = {
        "from": start_date.strftime('%Y-%m-%d'),
        "till": end_date.strftime('%Y-%m-%d'),
        "interval": 31  # Интервал в 1 месяц
    }
    
    # Формирование URL для получения цен
    url = base_url.format(ticker)
    
    # Запрос данных о ценах
    response = requests.get(url, params=params, timeout=30)
    if response.status_code != 200:
        print(f"Ошибка запроса: {response.status_code}")
        return None
    
    # Извлечение данных из ответа
    data = response.json()
    candles = data.get("candles", {}).get("data", [])
    columns = data.get("candles", {}).get("columns", [])
    
    if not candles:
        print("Нет данных для указанного периода.")
        return None
    
    # Преобразование данных о ценах в DataFrame
    df = pd.DataFrame(candles, columns=columns)
    df["begin"] = pd.to_datetime(df["begin"])
    
    # Получение годовых цен (например, последних значений за каждый год)
    annual_prices = df.groupby(df["begin"].dt.year).last()

    prices_array = annual_prices[["close"]]["close"].values
    
    # Получение данных о дивидендах
    dividends_df = pd.DataFrame(get_dividends(ticker))

    # Добавление дивидендов к доходностям
    adjusted_returns = []
    for i in range(1, len(prices_array)):
        year = annual_prices.index[i]
        try: 
            dividends = dividends_df.loc[str(year)].values[0]
        except:
            dividends = 0
        if dividends > prices_array[i]:
            dividends = dividends / 100.0
        # Учитываем дивиденды при расчете доходности
        adjusted_return = (prices_array[i] + dividends) / prices_array[i - 1] - 1
        adjusted_returns.append(adjusted_return)
    
    # Вычисление среднегодовой доходности
    avg_return = np.mean(adjusted_returns) * investment_horizon_years
    
    # Волатильность (стандартное отклонение доходностей)
    volatility = np.std(adjusted_returns) * np.sqrt(investment_horizon_years)
    
    return round(float(avg_return) * 100, 2), round(float(volatility) * 100, 2)


if __name__ == "__main__":
    # Пример использования
    ticker = "TRNFP"  # Например, Сбербанк
    prices = get_expected_returns_and_volatility(ticker)

    if prices is not None:
        print(prices)
