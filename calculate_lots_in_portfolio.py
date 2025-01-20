import numpy as np

# Данные
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
total_sum = 50000  # Общая сумма для портфеля

# 1. Расчет целевых капиталовложений для каждой акции
target_investment = weights * total_sum

# 2. Первоначальный расчет количества акций
initial_quantities = target_investment / prices

# 3. Округление количества акций до целых чисел (с учетом минимального отклонения)
rounded_quantities = np.floor(initial_quantities).astype(int)  # Округление вниз для начала

# Итеративный процесс, чтобы минимизировать отклонение от целевой суммы
def adjust_quantities(rounded_quantities, target_investment, prices, total_sum):
    current_sum = np.sum(rounded_quantities * prices)
    while current_sum < total_sum:
        # Рассчитываем отклонения от целевых весов
        remaining_investment = target_investment - (rounded_quantities * prices)
        # Выбираем акцию с наибольшим отклонением
        idx = np.argmax(remaining_investment)
        rounded_quantities[idx] += 1
        current_sum = np.sum(rounded_quantities * prices)
    return rounded_quantities

final_quantities = adjust_quantities(rounded_quantities, target_investment, prices, total_sum)

# Проверка итоговой стоимости
final_investment = final_quantities * prices
final_sum = np.sum(final_investment)

# Вывод результатов
print("Итоговое количество акций для каждой позиции:", final_quantities)
print("Итоговая сумма портфеля:", final_sum)
print("Отклонение от целевой суммы:", total_sum - final_sum)
