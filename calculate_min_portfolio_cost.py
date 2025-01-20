import numpy as np
import pandas as pd

weights = np.array([
    0.029187706, 0.043781559, 0.126528706, 0.017512624, 0.025305741, 
    0.0194682, 0.017512624, 0.022386971, 0.060856367, 0.055967427,
    0.111934853, 0.102156971, 0.097341, 0.043781559, 0.055967427, 
    0.087563118, 0.082747147
])
prices = np.array([
    1738, 318.9, 3220, 915.4, 6833, 
    572.7, 625.3, 617.55, 4945.5, 500,
    2643.4, 1948, 6391, 1049.6, 1135.8, 
    529.8, 13719
])


quantities = weights * np.sum(prices/weights) / prices
quantities = np.ceil(quantities).astype(int)
quantities = quantities / np.gcd.reduce(quantities)

# Шаг 3: Вычислить минимальную стоимость портфеля
min_cost = np.sum(quantities * prices)

data = {
        "цена": list(prices),
        "Вес в портфеле начальный": list(weights),
        "Кол-во лотов": list(quantities)
    }
df = pd.DataFrame(data)
df.to_excel("test.xlsx", index=False)

# Шаг 3: Вычислить минимальную стоимость портфеля
min_cost = np.sum(quantities * prices)

print("Минимальная стоимость портфеля:", min_cost)
