import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import re


# Функция для загрузки данных отчётности по МСФО с сайта Smart-lab
def download_financial_data(ticker):
    url = f'https://smart-lab.ru/q/{ticker}/f/y/MSFO/download/'
    response = requests.get(url)
    
    # Проверяем, что запрос успешен
    if response.status_code == 200:
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

        # Сохраняем в Excel
        df.to_excel("financial_data.xlsx", index=False)

        return 'financial_data.xlsx'
    else:
        print(f"Ошибка загрузки данных для {ticker}. Статус: {response.status_code}")
        return None

# Функция для извлечения данных по выручке и чистой прибыли из Excel
def extract_revenue_and_profit(file_path):
    df = pd.read_excel(file_path, sheet_name='Sheet1')  # Загружаем все листы
    
    # Извлекаем строки с выручкой и чистой прибылью
    revenue_row = df[df['Unnamed: 0'] == 'Выручка, млрд руб']
    profit_row = df[df['Unnamed: 0'] == 'Чистая прибыль, млрд руб']

    if revenue_row.empty or profit_row.empty:
        print("calculate_buffer_score:: Не удалось найти данные о выручке или чистой прибыли.")
        return None, None

    # Оставляем только столбцы с годами и преобразуем в числовой формат
    year_columns = [col for col in df.columns if col.isdigit()]  # Ищем колонки с годами
    try:
        # Преобразуем строки с данными в числовой формат
        revenue_data = revenue_row[year_columns].iloc[0].apply(lambda x: float(str(x).replace(' ', '').replace(',', '.')))
        profit_data = profit_row[year_columns].iloc[0].apply(lambda x: float(str(x).replace(' ', '').replace(',', '.')))
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")
        return None, None

    # Проверяем рост за последние 5 лет
    if len(year_columns) < 5:
        print("Недостаточно данных для анализа (менее 5 лет).")
        return None, None

    revenue_growth = (revenue_data.pct_change().tail(5) > 0).all()  # Рост выручки
    profit_growth = (profit_data.pct_change().tail(5) > 0).all()  # Рост чистой прибыли

    return revenue_growth, profit_growth

def extract_ebitda(file_path):
    df = pd.read_excel(file_path, sheet_name='Sheet1')  # Загружаем все листы
    
    # Извлекаем строки с выручкой и чистой прибылью
    ebitda_row = df[df['Unnamed: 0'] == 'Рентаб EBITDA, %']

    if ebitda_row.empty:
        print("calculate_buffer_score:: Не удалось найти данные о EBITDA.")
        return None

    # Оставляем только столбцы с годами и преобразуем в числовой формат
    year_columns = [col for col in df.columns if col.isdigit()]  # Ищем колонки с годами
    try:
        # Преобразуем строки с данными в числовой формат
        ebitda_data = ebitda_row[year_columns].iloc[0].apply(lambda x: float(str(x).replace(' ', '').replace(',', '.').replace('%', '')))
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")
        return None

    ebitda_growth = (ebitda_data.pct_change().tail(3) > 0).all()  # Рост ebitda
    return ebitda_growth

# Функция для получения текущей цены акции и цены 5 лет назад через API MOEX
def get_stock_prices(ticker):
    # Получение текущей цены акции
    base_url = "https://iss.moex.com/iss"
    market_data_url = f"{base_url}/engines/stock/markets/shares/securities/{ticker}.json"
    market_data_response = requests.get(market_data_url)
    market_data = market_data_response.json()
    # Поиск элемента с рынком TQBR в данных
    data = market_data['securities']['data']
    tqbr_entry = next((entry for entry in data if entry[1] == "TQBR"), None)

    if tqbr_entry is None:
        raise ValueError("Не найден элемент с рынком TQBR")

    # Доступ к текущей цене (поле LAST на индексе 3)
    current_price = tqbr_entry[3]
    # Получаем цену акции 5 лет назад
    five_years_ago = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    url_historical = f'https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json?from={five_years_ago}'
    response_historical = requests.get(url_historical)

    if response_historical.status_code == 200:
        historical_data = response_historical.json()
        five_years_ago_price = historical_data['history']['data'][0][9]  # Цена 5 лет назад
        return current_price, five_years_ago_price
    else:
        print(f"Ошибка получения исторических данных для {ticker}. Статус: {response_historical.status_code}")
        return None, None

# Функция для расчёта субъективной оценки
def calculate_subjective_score(ticker):
    # Шаг 1: Скачиваем и извлекаем данные о выручке и прибыли
    file_path = download_financial_data(ticker)
    if not file_path:
        return None
    
    revenue_growth, profit_growth = extract_revenue_and_profit(file_path)

    
    # Шаг 2: Получаем текущие и исторические цены акций
    current_price, five_years_ago_price = get_stock_prices(ticker)
    if current_price is None or five_years_ago_price is None:
        print(f"Не удалось получить цены для {ticker}.")
        return None
    
    # Шаг 3: Оценка на основе роста выручки, прибыли и цен
    score = 0
    if revenue_growth == None:
        if current_price > five_years_ago_price:
            score += 5
    else:
        if revenue_growth:
            score += 1.67
        if profit_growth:
            score += 1.67
        if current_price > five_years_ago_price:
            score += 1.67
    
    # Шаг 4: Оценка роста рентабильности по EBITDA за последние три года
    ebitda_growth = extract_ebitda(file_path)
    if ebitda_growth != None:
        if ebitda_growth:
            score += 5
            score = score/5

    return score

if __name__ == "__main__":
    # Пример использования
    ticker = "TQBR"  # Укажите тикер компании
    score = calculate_subjective_score(ticker)
    if score is not None:
        print(f"Субъективная оценка для {ticker}: {score}")
    else:
        print(f"Не удалось рассчитать оценку для {ticker}.")
