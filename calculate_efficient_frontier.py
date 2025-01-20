import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import itertools
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import requests
import re


n_years = 5
# Список тикеров компаний
tickers = [
    "UPRO",   # Юнипро
    "PHOR",   # Фосагро
    "MRKU",   # Россети Урал
    "OGKB",   # ОГК-2
    "NVTK",   # Новатэк
    "LKOH",   # Лукойл
    "ROSN",   # Роснефть
    "TATN",   # Татнефть
    "SIBN",   # Газпромнефть
    "MGNT",   # Магнит
    "BELU",   # Белуга
    "SBER",   # Сбербанк
    "MTSS",   # МТС
    "LSRG",   # ЛСР Групп
    "GMKN",   # Норникель
    "CHMF",   # Северсталь
    "ALRS",   # Алроса
    "PLZL"    # Полюсзолото
]


def calculate_portfolio_daily_returns(weights, returns_df):
    """
    Рассчитывает ежедневную доходность портфеля на основе весов активов.
    weights: np.array, веса активов в портфеле
    returns_df: DataFrame, содержит ежедневные доходности активов (колонки - тикеры)
    """
    portfolio_returns = np.dot(returns_df.values, weights)
    return portfolio_returns

def calculate_combined_portfolio_variance(weights, gmv_variance, mve_variance, correlation):
    """
    Вычисляет дисперсию итогового портфеля как функцию весов GMV и MVE.
    weights: [w_gmv, w_mve] — веса портфелей GMV и MVE
    """
    w_gmv, w_mve = weights
    combined_variance = (
        w_gmv**2 * gmv_variance**2 +
        w_mve**2 * mve_variance**2 +
        2 * w_gmv * w_mve * gmv_variance * mve_variance * correlation
    )
    return np.sqrt(combined_variance)

def plot_efficient_frontier(ax, data, gmv_weights, mve_weights):
    # Получаем матрицу ежедневных доходностей акций
    returns_df = data.pivot(index="begin", columns="ticker", values="return").fillna(0)

    # Рассчитываем временные ряды доходностей портфелей
    gmv_returns = calculate_portfolio_daily_returns(gmv_weights, returns_df)
    mve_returns = calculate_portfolio_daily_returns(mve_weights, returns_df)

    # 2. Корреляция между GMV и MVE
    correlation_between_gmv_and_mve = np.corrcoef(gmv_returns, mve_returns)[0, 1]

    # Ожидаемая волатильность GMV и MVE на 5 лет
    gmv_variance = np.std(gmv_returns) * np.sqrt(n_years)
    mve_variance = np.std(mve_returns) * np.sqrt(n_years)

    # Рассчитываем эффективную границу
    frontier_volatilities, frontier_returns = calculate_efficient_frontier(
        gmv_returns, mve_returns, gmv_variance, mve_variance, correlation_between_gmv_and_mve
    )

    # Рисуем эффективную границу на переданном объекте Axes
    ax.plot(frontier_volatilities, frontier_returns, label="Эффективная граница")
    ax.set_xlabel("Волатильность портфеля (σ)")
    ax.set_ylabel("Ожидаемая доходность портфеля (R)")
    ax.set_title("Эффективная граница портфеля")
    ax.legend()
    ax.grid(True)

def calculate_efficient_frontier(gmv_returns, mve_returns, gmv_variance, mve_variance, correlation, num_points=1000):
    """
    Строит эффективную границу.
    """
    weights = np.linspace(-1, 2, num_points)
    frontier_returns = []
    frontier_volatilities = []
    for w in weights:
        # Итоговые веса GMV и MVE
        w_gmv = w
        w_mve = 1 - w

        # Доходность итогового портфеля
        combined_return = w_gmv * np.mean(gmv_returns)*n_years + w_mve * np.mean(mve_returns)*n_years

        # Дисперсия итогового портфеля
        combined_variance = calculate_combined_portfolio_variance(
            [w_gmv, w_mve], gmv_variance, mve_variance, correlation
        )
        frontier_returns.append(combined_return)
        frontier_volatilities.append(combined_variance)

    return frontier_volatilities, frontier_returns

def calculate_portfolio_variance(weights, volatilities, correlations):
    """
    Функция для вычисления дисперсии портфеля.
    weights - вектор весов активов
    volatilities - вектор волатильностей активов
    correlations - матрица коэффициентов корреляции между активами
    """
    num_assets = len(weights)

    # Матрица ковариации
    cov_matrix = np.outer(volatilities, volatilities) * correlations
    
    # Дисперсия портфеля
    portfolio_variance = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    return portfolio_variance

def get_minimum_variance_portfolio(volatility_df, correlation_df):
    """
    Оптимизация для минимизации дисперсии портфеля.
    """
    # Волатильности активов
    volatilities = volatility_df["volatility"].values
    
    # Коэффициенты корреляции между активами
    tickers = volatility_df["ticker"].values
    corr_matrix = np.zeros((len(tickers), len(tickers)))
    
    # Заполнение матрицы корреляций
    for i, ticker1 in enumerate(tickers):
        for j, ticker2 in enumerate(tickers):
            if i != j:
                corr_matrix[i, j] = correlation_df[
                    (correlation_df["ticker1"] == ticker1) & (correlation_df["ticker2"] == ticker2)
                ]["correlation"].values[0]
            else:
                corr_matrix[i, j] = 1  # Диагональ — корреляция 1

    # Начальные веса (равномерное распределение)
    initial_weights = np.ones(len(tickers)) / len(tickers)
    
    # Ограничение: сумма весов должна быть равна 1
    constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
    
    # Ограничения на веса: от 0 до 1 для каждого актива
    bounds = tuple((0, 1) for _ in range(len(tickers)))

    # Оптимизация
    result = minimize(calculate_portfolio_variance, initial_weights, args=(volatilities, corr_matrix), 
                      bounds=bounds, constraints=constraints)
    
    return result

def get_maximum_sharp_portfolio(summary, correlation_df):
    # Извлекаем ожидаемую доходность и волатильность
    expected_returns = summary["expected_return"].values
    volatilities = summary["volatility"].values

    # Коэффициенты корреляции между активами
    tickers = summary["ticker"].values
    corr_matrix = np.zeros((len(tickers), len(tickers)))
    
    # Заполнение матрицы корреляций
    for i, ticker1 in enumerate(tickers):
        for j, ticker2 in enumerate(tickers):
            if i != j:
                corr_matrix[i, j] = correlation_df[
                    (correlation_df["ticker1"] == ticker1) & (correlation_df["ticker2"] == ticker2)
                ]["correlation"].values[0]
            else:
                corr_matrix[i, j] = 1  # Диагональ — корреляция 1

    # Безрисковая ставка (15% годовых)
    risk_free_rate = 0.15 #todo

    # Ограничение: сумма весов должна быть равна 1
    constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
    
    # Ограничения на веса: от 0 до 1 для каждого актива
    bounds = tuple((0, 1) for _ in range(len(tickers)))

    # Начальные значения для весов (равномерное распределение)
    initial_weights = np.ones(len(tickers)) / len(tickers)
    # Оптимизация
    result = minimize(sharpe_ratio, initial_weights, args=(expected_returns, volatilities, corr_matrix, risk_free_rate),
                      bounds=bounds, constraints=constraints)

    return result

def perm(n, seq):
    returns = []
    for p in itertools.product(seq, repeat=n):
        returns.append(p)
    return returns

def calculate_correlation(df):
    # Получаем уникальные тикеры из данных
    tickers = df["ticker"].unique()
    correlation_results = []

    # Проходим по всем парам тикеров
    for ticker1, ticker2 in perm(2, tickers):
        # Фильтруем данные по тикерам
        data1 = df[df["ticker"] == ticker1][["begin", "return"]].rename(columns={"return": "return1"})
        data2 = df[df["ticker"] == ticker2][["begin", "return"]].rename(columns={"return": "return2"})

        # Объединяем данные по датам
        merged = pd.merge(data1, data2, on="begin", how="inner").dropna()

        if merged.empty:
            print(f"Нет общих данных для {ticker1} и {ticker2}")
            continue

        # Вычисляем коэффициент корреляции
        correlation_matrix = np.corrcoef(merged["return1"], merged["return2"])
        correlation = correlation_matrix[0, 1]

        correlation_results.append({
            "ticker1": ticker1,
            "ticker2": ticker2,
            "correlation": round(correlation, 2)
        })

    return pd.DataFrame(correlation_results)

def calculate_expected_returns_and_volatility(df):
    # Группировка данных по тикерам
    summary = df.groupby("ticker")["return"].agg(
        expected_return=lambda x: (x.mean() * n_years).round(2),  # Ожидаемая доходность
        volatility=lambda x: (x.std() * np.sqrt(n_years)).round(2)  # Стандартное отклонение
    ).reset_index()
    return summary

def get_moex_data(ticker, years=10):
    """Получение годовых цен акции за последние N лет."""
    # Текущая дата
    end_date = datetime.now()
    # Дата 10 лет назад
    years = 10
    start_date = end_date - timedelta(days=365 * years)
    
    # Параметры запроса
    params = {
        "from": start_date.strftime('%Y-%m-%d'),
        "till": end_date.strftime('%Y-%m-%d'),
        "interval": 31  # Интервал в 1 месяц
    }
    
    # Формирование URL
    base_url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{}/candles.json"
    url = base_url.format(ticker)
    
    # Запрос данных
    response = requests.get(url, params=params)
    
    # Проверка статуса ответа
    if response.status_code != 200:
        print(f"Ошибка запроса: {response.status_code}")
        return None
    
    # Извлечение данных из ответа
    data = response.json()
    candles = data.get("candles", {}).get("data", [])
    columns = data.get("candles", {}).get("columns", [])

    # Если данных нет
    if not candles:
        print("Нет данных для указанного периода.")
        return None
    
    # Преобразование данных в DataFrame для удобной работы
    df = pd.DataFrame(candles, columns=columns)
    # Преобразование даты
    df["begin"] = pd.to_datetime(df["begin"])
    
    # Получение годовых цен (например, последних значений за каждый год)
    annual_prices = df.groupby(df["begin"].dt.year).last()
    # Преобразуем данные в DataFrame

    annual_prices["ticker"] = ticker  # Добавляем столбец с тикером
    return annual_prices

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

def get_data_for_tickers(tickers, years=n_years):
    all_data = []
    for ticker in tickers:
        print(f"Получение данных для {ticker}...")
        df = get_moex_data(ticker, years=years)
        dividends_df = pd.DataFrame(get_dividends(ticker))
        dividends_df = dividends_df.reset_index()
        dividends_df.columns = ['year', 'dividends']
        dividends_df['year'] = dividends_df['year'].astype(int)
        df['year'] = df.index
        df['year'] = df['year'].astype(int)
        merged_df = pd.merge(df, dividends_df, on='year', how='left')
        merged_df = merged_df.fillna(0)
        if df is not None:
            all_data.append(merged_df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        print("Нет данных для указанных тикеров.")
        return pd.DataFrame()

def calculate_returns(df):
    # Создаем новый столбец для годовой доходности, заполняем его значениями
    annual_returns = []
    ticker_prev = ""
    for i in range(len(df)):
        ticker = df.loc[i, 'ticker']
        if ticker_prev != ticker:
            annual_returns.append(0)
            ticker_prev = ticker
            continue
        ticker_prev = ticker
        if i == 0:
            # Для первого года доходность не вычисляется, так как нет данных за предыдущий год
            annual_returns.append(0)
        else:
            prev_close = df.loc[i - 1, 'close']
            curr_close = df.loc[i, 'close']
            dividends = df.loc[i, 'dividends']
            if dividends > curr_close:
                dividends = dividends / 100
            annual_return = round(100 * (dividends + (curr_close - prev_close)) / prev_close, 2)
            annual_returns.append(annual_return)
    
    # Добавляем новый столбец в DataFrame
    df['return'] = annual_returns
    return df

def sharpe_ratio(weights, expected_returns, volatilities, correlation_matrix, risk_free_rate):
    # Расчет ожидаемой доходности портфеля
    portfolio_return = np.sum(weights * expected_returns)

    # Расчет волатильности портфеля
    portfolio_volatility = calculate_portfolio_variance(weights, volatilities, correlation_matrix)

    # Коэффициент Шарпа
    res = -(portfolio_return - risk_free_rate) / portfolio_volatility
    return res

def get_optimal_portfolio(data, gmv_weights, mve_weights):
    # Получаем матрицу ежедневных доходностей акций
    returns_df = data.pivot(index="begin", columns="ticker", values="return").fillna(0)

    # Рассчитываем временные ряды доходностей портфелей
    gmv_returns = calculate_portfolio_daily_returns(gmv_weights, returns_df)
    mve_returns = calculate_portfolio_daily_returns(mve_weights, returns_df)

    # 2. Корреляция между GMV и MVE
    correlation_between_gmv_and_mve = np.corrcoef(gmv_returns, mve_returns)[0, 1]

    # Ожидаемая волатильность GMV и MVE на 5 лет
    gmv_variance = np.std(gmv_returns) * np.sqrt(n_years)
    mve_variance = np.std(mve_returns) * np.sqrt(n_years)

    # Ограничения: сумма весов должна быть равна 1
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})

    # Ограничения на веса: от 0 до 1
    bounds = [(-1, 2)]

    # Начальные веса
    initial_weights = [-1, 2]

    # Оптимизация
    result_combined = minimize(calculate_combined_portfolio_variance, initial_weights,
        args=(gmv_variance, mve_variance, correlation_between_gmv_and_mve),
        bounds=bounds, constraints=constraints
    )

    return result_combined

def main(tickers):
    # Получение данных и вычисление доходности
    try:
        data = get_data_for_tickers(tickers)
        data = calculate_returns(data)
        
        # Рассчитываем ожидаемую доходность и волатильность
        summary = calculate_expected_returns_and_volatility(data)

        # Рассчитываем корреляцию между акциями
        correlation_df = calculate_correlation(data)

        min_variance_result = get_minimum_variance_portfolio(summary, correlation_df)
        if min_variance_result.success:
            optimal_weights = min_variance_result.x
            gmv_weights = min_variance_result.x
            tickers = summary["ticker"].values
            print("\nОптимальные веса для минимальной дисперсии:")
            for ticker, weight in zip(tickers, optimal_weights):
                print(f"{ticker}: {weight * 100:.2f}%")
            combined_return = np.sum(optimal_weights * summary["expected_return"].values)
            print(f"Минимальная дисперсия портфеля: {min_variance_result.fun}")
            print(f"Ожидаемая доходность GVM портфеля: {combined_return:.2f}%")
        else:
            print("Оптимизация не удалась!")


        # Оптимизация MVE портфеля
        max_sharp_portfolio = get_maximum_sharp_portfolio(summary, correlation_df)

        # Выводим результаты
        if max_sharp_portfolio.success:
            print(f"Максимальный коэффициент Шарпа портфеля: {-max_sharp_portfolio.fun}")
            optimal_weights = max_sharp_portfolio.x
            mve_weights = max_sharp_portfolio.x
            print("Оптимальные веса активов для максимального коэффициента Шарпа:")
            for ticker, weight in zip(tickers, optimal_weights):
                print(f"{ticker}: {weight:.2%}")
            mve_return = np.sum(optimal_weights * summary["expected_return"].values)
            print(f"Ожидаемая доходность MVE портфеля: {mve_return:.2f}%")
            volatilities = summary["volatility"].values
            # Коэффициенты корреляции между активами
            tickers = summary["ticker"].values
            corr_matrix = np.zeros((len(tickers), len(tickers)))
            
            # Заполнение матрицы корреляций
            for i, ticker1 in enumerate(tickers):
                for j, ticker2 in enumerate(tickers):
                    if i != j:
                        corr_matrix[i, j] = correlation_df[
                            (correlation_df["ticker1"] == ticker1) & (correlation_df["ticker2"] == ticker2)
                        ]["correlation"].values[0]
                    else:
                        corr_matrix[i, j] = 1  # Диагональ — корреляция 1
            mve_volatility = calculate_portfolio_variance(optimal_weights, volatilities, corr_matrix)
            print(f"Волатильность портфеля Шарпа: {mve_volatility}")
        else:
            print("Оптимизация не удалась.")


        # Вычисление оптимального портфеля
        optimal_portfolio = get_optimal_portfolio(data, gmv_weights, mve_weights)

        # Выводим результаты
        if optimal_portfolio.success:
            # Оптимальные веса GMV и MVE
            optimal_gmv_weight, optimal_mve_weight = optimal_portfolio.x
            print(f"Оптимальные веса для итогового портфеля: GMV = {optimal_gmv_weight:.2f}, MVE = {optimal_mve_weight:.2f}")
            print("Минимальная волатильность портфеля: ", optimal_portfolio.fun)
        else:
            print("Оптимизация не удалась.")

         # Расчет итоговых весов активов в комбинированном портфеле
        final_weights = optimal_gmv_weight * gmv_weights + optimal_mve_weight * mve_weights

        # Выводим итоговые веса
        print("\nИтоговые веса активов для комбинированного портфеля:")
        for ticker, weight in zip(tickers, final_weights):
            print(f"{ticker}: {weight * 100:.2f}%")

        combined_return = np.sum(final_weights * summary["expected_return"].values)
        print(f"Ожидаемая доходность комбинированного портфеля: {combined_return:.2f}%")

        # Построение эффективной границы
        return mve_weights, data, gmv_weights, mve_weights, mve_volatility, mve_return

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    mve_weights, data, gmv_weights, mve_weights, mve_volatility, mve_return = main(tickers)
    plt = plot_efficient_frontier(data, gmv_weights, mve_weights)
    plt.show()
