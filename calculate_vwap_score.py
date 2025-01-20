import requests
import datetime
import json


def getVWAP(ticker):
	dateNow = datetime.date.today().strftime("%Y-%m-%d")
	dateStart = (datetime.date.today() - datetime.timedelta(days=120)).strftime("%Y-%m-%d")
	r1 = requests.get(url="https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/" + ticker + ".json?from=" + 
				dateStart + "&till=" + dateNow)
	historyValue = json.loads(r1.text)["history"]["data"]
	CumulativeTypicalPriceVolume = 0
	CumulativeVolume = 0
	for i in historyValue:
		CumulativeTypicalPriceVolume += (i[7] + i[8] + i[9])*i[12]/3
		CumulativeVolume += i[12]
	return round(CumulativeTypicalPriceVolume/CumulativeVolume, 3)

# Функция для получения рыночной цены акции
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

def evaluate_company(ticker):
    market_price = get_market_price(ticker)
    if market_price is None:
        print("calculate_vwap_score:: Ошибка получения рыночной цены")
        return "Ошибка получения рыночной цены"

    vwap = getVWAP(ticker)
    # 5. Сравниваем справедливую цену с рыночной ценой
    if vwap > market_price * 1.1:
        score = 2  # Справедливая цена выше рыночной на 10%+
    elif market_price * 0.9 <= vwap <= market_price * 1.1:
        score = 1  # Справедливая цена в пределах ±10% от рыночной
    else:
        score = 0  # Справедливая цена ниже рыночной на 10%+

    # Выводим результат
    return {
        "ticker": ticker,
        "vwap": vwap,
        "market_price": market_price,
        "score": score
    }

# Точка входа
if __name__ == "__main__":
    ticker = input("Введите тикер компании: ")
    result = evaluate_company(ticker)
    print(result)
