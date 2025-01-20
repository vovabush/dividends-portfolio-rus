import requests
import json
import math
import okama as ok
import pandas as pd
import re


def get_inflation_rate():
    """
    Получаем среднегодовую инфляцию. Можно заменить на запрос к источнику Росстата.
    """
    # Задаем параметры: тикер рублевого инфляционного индекса (CPI.RUB) и временной период
    ticker = "RUB.INFL"
    years = 15

    # Получаем текущий год
    current_year = pd.Timestamp.today().year
    start_date = f"{current_year - years}-01"  # Начало периода (15 лет назад)
    end_date = f"{current_year}-12"  # Конец периода (текущий год)

    # Загружаем данные по инфляции
    try:
        inflation_data = ok.Inflation(symbol=ticker, first_date=start_date, last_date=end_date)
        annual_inflation_rates = inflation_data.annual_inflation_ts  # Ежегодный уровень инфляции
        average_inflation = annual_inflation_rates.mean() * 100  # Среднегодовая инфляция в процентах
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
    return average_inflation

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

def get_avg_net_income_and_outstanding_shares(ticker):
    """
    Возвращает среднюю чистую прибыль компании за последние 5 лет и количество акций в обращении
    Можно парсить с сайта SmartLab или вручную.
    """
    file_path = download_financial_data(ticker)
    if not file_path:
        return None

    df = pd.read_excel(file_path, sheet_name='Sheet1')  # Загружаем все листы

    # Извлекаем строки с количеством акций и чистой прибылью
    profit_row = df[df.iloc[:, 0].str.startswith('Чистая прибыль,')]
    if profit_row.empty:
        print("Не удалось найти данные о чистой прибыли.")
        return False, False

    # Оставляем только столбцы с годами и преобразуем в числовой формат
    year_columns = [col for col in df.columns if col.isdigit()]  # Ищем колонки с годами
    try:
        # Преобразуем строки с данными в числовой формат
        profit_data = profit_row[year_columns].iloc[0].apply(lambda x: float(str(x).replace(' ', '').replace(',', '.')))
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")
        return False, False

    # Проверяем рост за последние 5 лет
    if len(year_columns) < 5:
        print("Недостаточно данных для анализа (менее 5 лет).")
        return False, False

    mult = df[df.iloc[:, 0].str.startswith('Чистая прибыль,')].iloc[-1].to_numpy()[0]
    if "млрд" in mult:
        mult = 10**9
    elif "млн" in mult:
        mult = 10**6
    else:
        mult = 1

    profit_growth = profit_data.tail(5).mean()*mult

    mult = df[df.iloc[:, 0].str.startswith('Число акций ао,')].iloc[-1].to_numpy()[0]
    if "млрд" in mult:
        mult = 10**9
    elif "млн" in mult:
        mult = 10**6
    else:
        mult = 1
    shares_row = float(df[df.iloc[:, 0].str.startswith('Число акций ао,')].iloc[-1]["LTM"].replace(' ', '').replace(',', '.'))
    shares = shares_row*mult

    try:
        mult = df[df.iloc[:, 0].str.startswith('Число акций ап,')].iloc[-1].to_numpy()[0]
        if "млрд" in mult:
            mult = 10**9
        elif "млн" in mult:
            mult = 10**6
        else:
            mult = 1
        shares_row = float(df[df.iloc[:, 0].str.startswith('Число акций ап,')].iloc[-1]["LTM"].replace(' ', '').replace(',', '.'))
        shares += shares_row*mult
    except:
        pass
    stocks_count = shares

    return profit_growth, stocks_count
   
def calculate_fair_value(net_income, inflation_rate, outstanding_shares):
    """
    Рассчитывает справедливую стоимость акции по формуле.
    """
    fair_value_total = (net_income / inflation_rate) * 100
    fair_price_per_share = fair_value_total / outstanding_shares
    return fair_price_per_share

def get_market_price(ticker):
    """
    Получаем текущую рыночную цену акции через API MOEX.
    :param ticker: Тикер компании
    """
    base_url = "https://iss.moex.com/iss"

    try:
        # Доступ к текущей цене
        market_data_url = f"{base_url}/engines/stock/markets/shares/securities/{ticker}.json"
        market_data_response = requests.get(market_data_url)
        market_data = market_data_response.json()

        # Поиск элемента с рынком TQBR в данных
        data = market_data['securities']['data']
        tqbr_entry = next((entry for entry in data if entry[1] == "TQBR"), None)

        if tqbr_entry is None:
            raise ValueError("Не найден элемент с рынком TQBR")

        # Доступ к текущей цене (поле LAST на индексе 3)
        last_price = tqbr_entry[3]
        return last_price
    except Exception as e:
        return f"Ошибка получения данных для тикера {ticker}: {e}"

def compare_prices(fair_price, market_price):
    """
    Сравнивает справедливую стоимость с рыночной ценой и возвращает оценку.
    Новая логика:
    - Если справедливая стоимость > рыночной цены +10% -> 2 балла
    - Если справедливая стоимость в диапазоне ±10% от рыночной цены -> 1 балл
    - Если справедливая стоимость < рыночной цены +10% -> 0 баллов
    """
    if market_price is None:
        return "Невозможно получить рыночную цену."

    # Вычисляем пределы ±10% от рыночной цены
    upper_bound = market_price * 1.10  # Рыночная цена +10%
    lower_bound = market_price * 0.90  # Рыночная цена -10%

    if fair_price > upper_bound:
        return 2  # Справедливая стоимость больше рыночной цены +10%
    elif lower_bound <= fair_price <= upper_bound:
        return 1  # Справедливая стоимость в диапазоне ±10%
    else:
        return 0  # Справедливая стоимость меньше рыночной цены +10%


def main(ticker):
    """
    Главная функция: собирает данные, считает и сравнивает.
    :param ticker: Тикер компании (например, 'GAZP')
    """
    # Шаг 1: Получаем данные
    inflation_rate = get_inflation_rate()
    net_income, outstanding_shares = get_avg_net_income_and_outstanding_shares(ticker)
    market_price = get_market_price(ticker)
    
    # Шаг 2: Расчет справедливой стоимости
    fair_price = calculate_fair_value(net_income, inflation_rate, outstanding_shares)
    
    # Шаг 3: Сравнение
    #print(f"Справедливая стоимость: {fair_price:.2f} руб.")
    #print(f"Текущая рыночная цена: {market_price:.2f} руб.")
    score = compare_prices(fair_price, market_price)
    #print(f"Оценка: {score} балла(ов)")
    return score

if __name__ == "__main__":
    # Пример запуска программы
    ticker = "BELU" 
    main(ticker)  