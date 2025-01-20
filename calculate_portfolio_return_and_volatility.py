import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import itertools
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import requests
import re
from calculate_efficient_frontier import *


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

weights = [
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555,
    0.0555
]


def main(tickers, weights):
    # Получение данных и вычисление доходности
    weights = np.array(list(weights))
    data = get_data_for_tickers(tickers)
    data = calculate_returns(data)

    # Рассчитываем ожидаемую доходность и волатильность
    summary = calculate_expected_returns_and_volatility(data)

    # Рассчитываем корреляцию между акциями
    correlation_df = calculate_correlation(data)
    corr_matrix = np.zeros((len(tickers), len(tickers)))
    volatilities = summary["volatility"].values
    # Заполнение матрицы корреляций
    for i, ticker1 in enumerate(tickers):
        for j, ticker2 in enumerate(tickers):
            if i != j:
                corr_matrix[i, j] = correlation_df[
                    (correlation_df["ticker1"] == ticker1) & (correlation_df["ticker2"] == ticker2)
                ]["correlation"].values[0]
            else:
                corr_matrix[i, j] = 1  # Диагональ — корреляция 1
    volatility = calculate_portfolio_variance(weights, volatilities, corr_matrix)

    combined_return = np.sum(weights * summary["expected_return"].values)
    

    # Построение эффективной границы
    return combined_return, volatility

if __name__ == "__main__":
    returns, volatility = main(tickers, weights)
    print(returns, volatility)
