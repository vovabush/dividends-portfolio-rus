import requests
import pandas as pd
import re
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


# Формируем URL для запроса
def generate_cbr_url():
    # Получаем текущую дату
    current_date = datetime.now()
    # Дата 5 лет назад
    five_years_ago = current_date - timedelta(days=5*365)

    # Форматируем даты для URL
    current_date_str = "1.01." + current_date.strftime('%Y')
    five_years_ago_str = "1.12." + five_years_ago.strftime('%Y')

    # Формируем URL
    url = f'https://www.cbr.ru/statistics/avgprocstav/?UniDbQuery.Posted=True&UniDbQuery.From={five_years_ago_str}&UniDbQuery.To={current_date_str}'
    return url

def get_cbr_data():
    # Получаем URL
    cbr_url = generate_cbr_url()

    # Загружаем данные с Банка России (пример запроса)
    response = requests.get(cbr_url)
    if response.status_code != 200:
        print("Не удалось загрузить данные с Банка России.")
        return None

    # HTML данные
    return response.text

# Функция для извлечения данных из таблицы
def parse_table(html):
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select('table.data tr')[1:]  # Пропускаем заголовок
    data = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 2:
            date = cells[0].text.strip()
            rate = cells[1].text.strip().replace(',', '.')
            data.append((date, float(rate)))
    return data

# Функция для загрузки данных отчётности по МСФО с сайта SmartLab
def download_financial_data(ticker):
    url = f'https://smart-lab.ru/q/{ticker}/f/y/MSFO/download/'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.text
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

        # Возвращаем DataFrame для анализа
        return df
    else:
        print(f"Ошибка загрузки данных для {ticker}. Статус: {response.status_code}")
        return None

# Функция для вычисления справедливой цены
def get_divi_data(data):
    try:
        # Достаем необходимые показатели из отчётности компании
        return data[data.iloc[:, 0].str.startswith('Див доход, ао, %')].iloc[-1].tail(6)[0:5].replace("", "0%").to_numpy()
    except Exception as e:
        return None

# Функция для вычисления средней доходности вкладов по годам
def calculate_yearly_average(data):
    yearly_data = {}
    for date, rate in data:
        # Извлекаем год из даты
        match = re.search(r'\d{4}', date)
        if match:
            year = int(match.group(0))
            if year not in yearly_data:
                yearly_data[year] = []
            yearly_data[year].append(rate)

    # Считаем среднее значение для каждого года
    yearly_average = {}
    for year, rates in yearly_data.items():
        yearly_average[year] = np.mean(rates)
    return yearly_average

# Оценка компании
def evaluate_company(ticker):
    # Загружаем данные
    financial_data = download_financial_data(ticker)
    if financial_data is None:
        print("calculate_multiplier_score:: Ошибка загрузки финансовых данных")
        return "Ошибка загрузки финансовых данных"

    # Получаем данные о дивидендах
    divi_data = get_divi_data(financial_data)
    if divi_data is None:
        print("calculate_dividends_score:: Ошибка получения дивидендов")
        return "Ошибка получения дивидендов"
    # Получаем данные с сайта Банка России по вкладам
    cbr_data = get_cbr_data()
    if cbr_data == None:
        return None
    
    cbr_table = parse_table(cbr_data)
    bank_income = calculate_yearly_average(cbr_table)

    # Преобразуем дивидендную доходность из строк в числа
    dividend_yields_numeric = np.array([float(yield_.strip('%')) for yield_ in divi_data])

    # Получаем соответствующие года для сравнения (последние 5 лет)
    comparison_years = sorted(bank_income.keys())[-len(dividend_yields_numeric):]

    # Выполняем сравнение
    results = []
    for year, dividend_yield in zip(comparison_years, dividend_yields_numeric):
        deposit_rate = bank_income[year]
        if dividend_yield > deposit_rate:
            results.append(2)  # Дивидендная доходность выше
        elif dividend_yield < deposit_rate:
            results.append(0)  # Дивидендная доходность ниже
        else:
            results.append(1)  # При равенстве (если такое возможно)

    # Выставляем итоговую оценку
    if all(result == 2 for result in results):
        final_score = 2
    elif all(result == 0 for result in results):
        final_score = 0
    else:
        final_score = 1

    # Выводим результат
    return {
        "ticker": ticker,
        "score": final_score
    }

# Точка входа
if __name__ == "__main__":
    ticker = input("Введите тикер компании: ")
    result = evaluate_company(ticker)
    print(result)
