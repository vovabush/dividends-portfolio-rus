import requests
import pandas as pd
import re
import numpy as np
from bs4 import BeautifulSoup


# 1. Функция для загрузки данных отчётности по МСФО с сайта SmartLab
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

# 2. Получаем данные сектора со SmartLab
def get_sector_averages(ticker):
    url = f'https://smart-lab.ru/q/{ticker}/f/y/'
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text

        # Парсинг HTML
        soup = BeautifulSoup(html, 'html.parser')
        # Поиск всех ссылок, где data-title начинается с "Aнализ сектора"
        links = soup.find_all('a', {'title': lambda value: value and value.startswith('Aнализ сектора')})

        # Извлечение всех ссылок
        url = f"https://smart-lab.ru{links[0]['href']}"
        response = requests.get(url)
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            table = soup.find('table', {'class': 'simple-little-table'})
            data = []
            headers = []

            for th in table.find_all('th'):
                headers.append(th.text.strip())

            for row in table.find_all('tr'):
                cells = row.find_all('td')
                data.append([cell.text.strip() for cell in cells])

            df = pd.DataFrame(data, columns=headers)

            df['P/E'] = pd.to_numeric(df['P/E'], errors='coerce')  # Преобразование в число
            df['P/B'] = pd.to_numeric(df['P/B'], errors='coerce')  # Преобразование в число
            try:
                df['P/S'] = pd.to_numeric(df['P/S'], errors='coerce')  # Преобразование в число
            except:
                df['P/S'] = None
            
            # Шаг 6: Расчет средних значений
            mean_pe = df['P/E'].mean()
            mean_pb = df['P/B'].mean()
            mean_ps = df['P/S'].mean()
        else:
            return None
        return {"P/B": mean_pb, "P/S": mean_ps, "P/E": mean_pe}
    else:
        print(f"Ошибка загрузки данных для сектора {ticker}. Статус: {response.status_code}")
        return None

# 3. Функция для вычисления справедливой цены
def calculate_fair_price(data, sector_averages):
    try:
        # Достаем необходимые показатели из отчётности компании
        mult = data[data.iloc[:, 0].str.startswith('Чистая прибыль,')].iloc[-1].to_numpy()[0]
        if "млрд" in mult:
            mult = 10**9
        elif "млн" in mult:
            mult = 10**6
        else:
            mult = 1
        net_profit_row = float(data[data.iloc[:, 0].str.startswith('Чистая прибыль,')].iloc[-1]["LTM"].replace(' ', '').replace(',', '.'))
        net_profit = net_profit_row*mult

        mult = data[data.iloc[:, 0].str.startswith('Капитализация,')].iloc[-1].to_numpy()[0]
        if "млрд" in mult:
            mult = 10**9
        elif "млн" in mult:
            mult = 10**6
        else:
            mult = 1
        cap_row = float(data[data.iloc[:, 0].str.startswith('Капитализация,')].iloc[-1]["LTM"].replace(' ', '').replace(',', '.'))
        cap = cap_row*mult

        try:
            mult = data[data.iloc[:, 0].str.startswith('Баланс стоимость,')].iloc[-1]
            if "млрд" in mult:
                mult = 10**9
            elif "млн" in mult:
                mult = 10**6
            else:
                mult = 1
            bv_row = float(data[data.iloc[:, 0].str.startswith('Баланс стоимость,')].iloc[-1]["LTM"].replace(' ', '').replace(',', '.'))
            bv = bv_row*mult
        except:
            bv = None

        mult = data[data.iloc[:, 0].str.startswith('Число акций ао,')].iloc[-1].to_numpy()[0]
        if "млрд" in mult:
            mult = 10**9
        elif "млн" in mult:
            mult = 10**6
        else:
            mult = 1
        shares_row = float(data[data.iloc[:, 0].str.startswith('Число акций ао,')].iloc[-1]["LTM"].replace(' ', '').replace(',', '.'))
        shares = shares_row*mult

        try:
            mult = data[data.iloc[:, 0].str.startswith('Число акций ап,')].iloc[-1].to_numpy()[0]
            if "млрд" in mult:
                mult = 10**9
            elif "млн" in mult:
                mult = 10**6
            else:
                mult = 1
            shares_row = float(data[data.iloc[:, 0].str.startswith('Число акций ап,')].iloc[-1]["LTM"].replace(' ', '').replace(',', '.'))
            shares += shares_row*mult
        except:
            pass

        # Средние значения сектора
        sector_pe = sector_averages["P/E"]
        sector_ps = sector_averages["P/S"]
        sector_pb = sector_averages["P/B"]
        # Рассчитываем справедливую цену
        fair_price_pe = (sector_pe * net_profit) / shares
        fair_price_ps = (sector_ps * cap) / shares
        if bv:
            fair_price_pb = (sector_pb * bv) / shares
        else:
            fair_price_pb = (sector_pb * cap) / shares

        # Среднее арифметическое
        if bv:
            fair_price = np.mean([fair_price_pe, fair_price_ps, fair_price_pb])
        else:

            fair_price = np.mean([fair_price_pe, fair_price_pb])
        return fair_price
    except Exception as e:
        print(f"Ошибка при вычислении справедливой цены: {e}")
        return None

# 4. Функция для получения рыночной цены акции
def get_market_price(ticker):
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
        return float(last_price)
    except Exception as e:
        print(f"Ошибка получения данных для тикера {ticker}: {e}")
        return None

# 5. Оценка компании
def evaluate_company(ticker):
    # 1. Загружаем данные
    financial_data = download_financial_data(ticker)
    if financial_data is None:
        print("calculate_multiplier_score:: Ошибка загрузки финансовых данных")
        return "Ошибка загрузки финансовых данных"

    # 2. Получаем данные сектора
    sector_averages = get_sector_averages(ticker)
    if sector_averages is None:
        print("calculate_multiplier_score:: Ошибка загрузки данных сектора")
        return "Ошибка загрузки данных сектора"

    # 3. Вычисляем справедливую цену
    fair_price = calculate_fair_price(financial_data, sector_averages)
    if fair_price is None:
        print("calculate_multiplier_score:: Ошибка вычисления справедливой цены")
        return "Ошибка вычисления справедливой цены"

    # 4. Получаем рыночную цену
    market_price = get_market_price(ticker)
    if market_price is None:
        print("calculate_multiplier_score:: Ошибка получения рыночной цены")
        return "Ошибка получения рыночной цены"

    # 5. Сравниваем справедливую цену с рыночной ценой
    if fair_price > market_price * 1.1:
        score = 2  # Справедливая цена выше рыночной на 10%+
    elif market_price * 0.9 <= fair_price <= market_price * 1.1:
        score = 1  # Справедливая цена в пределах ±10% от рыночной
    else:
        score = 0  # Справедливая цена ниже рыночной на 10%+

    # Выводим результат
    return {
        "ticker": ticker,
        "fair_price": fair_price,
        "market_price": market_price,
        "score": score
    }

# Точка входа
if __name__ == "__main__":
    ticker = input("Введите тикер компании: ")
    result = evaluate_company(ticker)
    print(result)
