import requests
from datetime import datetime

def get_stock_price_on_date(ticker, date):
    """
    Получает цену акции на указанную дату из API MOEX.
    """
    date_str = date.strftime('%Y-%m-%d')
    url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json?from={date_str}&till={date_str}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Не удалось получить данные для тикера {ticker} на дату {date_str}. Код ответа: {response.status_code}")
    
    data = response.json()
    try:
        # Берём данные о закрытии (CLOSE) на указанную дату
        closing_price = float(data['history']['data'][0][11])  # Индекс 11 - цена закрытия (CLOSE)
        return closing_price
    except (IndexError, TypeError):
        raise Exception(f"Не удалось получить цену акции на дату {date_str}.")

def get_dividend_yield(ticker):
    """
    Вычисляет ожидаемую дивидендную доходность как среднюю доходность на основе последних 5 дивидендных выплат.
    """
    # Получить данные о дивидендах
    url = f"https://iss.moex.com/iss/securities/{ticker}/dividends.json"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Не удалось получить дивидендные данные для тикера {ticker}. Код ответа: {response.status_code}")
    
    data = response.json()
    try:
        # Извлекаем список дивидендов
        dividends = data['dividends']['data']
        if len(dividends) == 0:
            raise Exception("Нет данных о дивидендах для данного тикера.")
        
        # Берём последние 5 дивидендных выплат (или меньше, если их меньше 5)
        last_dividends = sorted(dividends, key=lambda x: x[2], reverse=True)[:5]  # Сортируем по дате (индекс 3)

        yields = []
        for dividend in last_dividends:
            try:
                payment_date = datetime.strptime(dividend[2], '%Y-%m-%d')  # Индекс 3 - дата выплаты
                annual_dividend = float(dividend[3])  # Индекс 4 - размер выплаты

                # Получаем цену акции на дату выплаты дивиденда
                stock_price_on_payment_date = get_stock_price_on_date(ticker, payment_date)

                # Рассчитываем дивидендную доходность для этой выплаты
                dividend_yield = (annual_dividend / stock_price_on_payment_date) * 100
                yields.append(dividend_yield)
                print(payment_date, dividend_yield)
            except Exception as e:
                print(f"Предупреждение: не удалось обработать выплату дивидендов: {e}")

        # Рассчитываем среднюю дивидендную доходность
        if not yields:
            raise Exception("Не удалось рассчитать дивидендную доходность, данные отсутствуют.")

        average_yield = sum(yields) / len(yields)
        return average_yield
    except (IndexError, TypeError, ValueError):
        raise Exception("Не удалось получить данные о дивидендах или цене акции.")

# Пример использования
if __name__ == "__main__":
    ticker = "OGKB"  # Например, Газпром
    try:
        yield_percentage = get_dividend_yield(ticker)
        print(f"Ожидаемая дивидендная доходность для {ticker}: {yield_percentage:.2f}%")
    except Exception as e:
        print(f"Ошибка: {e}")
