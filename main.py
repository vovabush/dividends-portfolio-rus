import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMenuBar, QFileDialog,
    QMessageBox, QLabel, QInputDialog, QSplitter, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from backend import Portfolio, Sector, Stock  # Импорт backend кода
from PyQt5.QtWidgets import QMenu
import warnings
import pandas as pd
import calculate_efficient_frontier
import calculate_portfolio_return_and_volatility
import base64


warnings.simplefilter(action="ignore", category=FutureWarning)
encoded_icon = "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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAqnDYYf8PrXNnQV1CJ7kAAAAASUVORK5CYII="

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(encoded_icon))

        self.setWindowIcon(QIcon(pixmap))

        self.setWindowTitle("Дивидендный портфель")
        self.setGeometry(100, 100, 1200, 800)

        # Инициализация портфеля
        self.portfolio = Portfolio()

        # Словарь для хранения цветов секторов
        self.sector_colors = {}

        # Основные элементы интерфейса
        self.init_ui()

    def init_ui(self):
        # Верхнее меню
        self.menu_bar = self.menuBar()
        self.init_menu()

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основные компоненты
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(16)  # Количество столбцов
        self.portfolio_table.setHorizontalHeaderLabels([
            "Сектор", "Тикер", "Название компании", "Текущая цена", "ОД5Л",
            "В5Л", "Оценка Баффета",
            "Мультипликаторы", "VWAP", "Дивиденды", "Общая оценка акции",
            "Оценка сектора", "Вес акции в портфеле", "Стоимость лота", "Кол-во лотов",
            "Реальные веса"
        ])
        self.portfolio_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.portfolio_table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.portfolio_table.resizeColumnsToContents()
        self.portfolio_table.setSortingEnabled(True)

        # Поле ввода суммы и кнопка "Ребалансировать"
        self.sum_input = QLineEdit()
        self.sum_input.setPlaceholderText("Введите сумму для ребалансировки")
        self.rebalance_button = QPushButton("Ребалансировать")
        self.rebalance_button.clicked.connect(self.rebalance_portfolio)

        # Лейаут для ввода и кнопки
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Сумма:"))
        input_layout.addWidget(self.sum_input)
        input_layout.addWidget(self.rebalance_button)

        # Таблица с описанием эффективного портфеля
        self.efficient_portfolio_table = QTableWidget()
        self.efficient_portfolio_table.setColumnCount(3)
        self.efficient_portfolio_table.setHorizontalHeaderLabels([
            "Тикер", "Название компании", "Вес в портфеле"
        ])

        # Лейблы под таблицей
        self.min_volatility_label = QLabel("Минимальная волатильность: 1.0")
        self.expected_return_label = QLabel("Ожидаемая доходность: 1.0")

        # График эффективной границы
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Используем QSplitter для изменения размеров окон
        splitter_down = QSplitter(Qt.Horizontal)
        splitter_main = QSplitter(Qt.Vertical)

        # Верхняя часть: таблица портфеля + ввод суммы и кнопка
        portfolio_layout = QVBoxLayout()
        portfolio_layout.addWidget(self.portfolio_table)
        portfolio_layout.addLayout(input_layout)
        portfolio_widget = QWidget()
        portfolio_widget.setLayout(portfolio_layout)
        splitter_main.addWidget(portfolio_widget)

        efficient_layout = QVBoxLayout()
        efficient_widget = QWidget()
        efficient_layout.addWidget(QLabel("Эффективный портфель"))
        efficient_layout.addWidget(self.efficient_portfolio_table)
        efficient_layout.addWidget(self.min_volatility_label)
        efficient_layout.addWidget(self.expected_return_label)
        efficient_widget.setLayout(efficient_layout)

        splitter_down.addWidget(efficient_widget)

        # Нижняя часть: график
        splitter_down.addWidget(self.canvas)
        splitter_main.addWidget(splitter_down)

        # Устанавливаем основной компоновщик
        layout = QVBoxLayout()
        layout.addWidget(splitter_main)
        central_widget.setLayout(layout)

    def rebalance_portfolio(self):
            try:
                total_sum = float(self.sum_input.text())
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Введите корректную сумму для ребалансировки.")
                return

            row_count = self.portfolio_table.rowCount()
            if row_count == 0:
                QMessageBox.warning(self, "Ошибка", "Таблица портфеля пуста.")
                return

            quantities = self.portfolio.get_quantities_of_portfolio(total_sum)

            for row in range(row_count):
                self.portfolio_table.setItem(row, 14, QTableWidgetItem(str(quantities[row])))
                self.portfolio_table.item(row, 14).setBackground(self.sector_colors[self.portfolio_table.item(row, 0).text()])

            self.portfolio.calculate_real_stock_weights(total_sum)
            real_stock_wights = list(self.portfolio.real_stock_weights.values())
            for row in range(row_count):
                self.portfolio_table.setItem(row, 15, QTableWidgetItem(f"{real_stock_wights[row]:.2f}"))
                self.portfolio_table.item(row, 15).setBackground(self.sector_colors[self.portfolio_table.item(row, 0).text()])

            self.add_portfolio_return_and_volatility_point()
            QMessageBox.information(self, "Ребалансировка", "Кол-во лотов успешно обновлено.")

    def init_menu(self):
        file_menu = self.menu_bar.addMenu("Файл")
        save_action = file_menu.addAction("Сохранить в файл")
        open_action = file_menu.addAction("Открыть из файла")
        min_cost_action = file_menu.addAction("Минимальная сумма для портфеля")
        portfolio_parameters = file_menu.addAction("Доходность и волатильность портфеля")
        exit_action = file_menu.addAction("Выход")

        about_menu = self.menu_bar.addMenu("О программе")
        about_action = about_menu.addAction("Информация")

        save_action.triggered.connect(self.save_to_file)
        min_cost_action.triggered.connect(self.min_cost_view)
        open_action.triggered.connect(self.load_from_file)
        exit_action.triggered.connect(self.close)
        about_action.triggered.connect(self.show_about_dialog)
        portfolio_parameters.triggered.connect(self.show_portfolio_return_and_volatility)

    def show_portfolio_return_and_volatility(self):
        QMessageBox.information(self, "Доходность и волатильность потрфеля", 
            f"Ожидаемая доходность на 5 лет: {self.portfolio.returns:.2f}%\nОжидаемая волатильность на 5 лет: {self.portfolio.volatility:.2f}%")

    def save_to_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Excel Files (*.xlsx)")
        if filename:
            self.portfolio.save_to_xlsx(filename)
            QMessageBox.information(self, "Сохранение", "Портфель успешно сохранён!")

    def min_cost_view(self):
        total_cost = self.portfolio.calculate_min_portfolio_cost()
        if total_cost:
            self.min_sum_window = QWidget()
            self.min_sum_window.setWindowTitle("Минимальная сумма для портфеля")
            self.min_sum_window.setGeometry(150, 150, 600, 400)

            layout = QVBoxLayout()

            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["Акция", "Вес в портфеле", "Кол-во лотов"])

            for sector in self.portfolio.sectors:
                for stock in sector.stocks:
                    row = table.rowCount()
                    table.insertRow(row)
                    table.setItem(row, 0, QTableWidgetItem(stock.ticker))
                    table.setItem(row, 1, QTableWidgetItem(f"{self.portfolio.stock_weights.get(stock.ticker, 0):.2f}"))
                    table.setItem(row, 2, QTableWidgetItem(str(stock.num_lots)))

            layout.addWidget(table)

            total_cost_label = QLabel(f"Минимальная стоимость портфеля: {total_cost:.2f}")
            layout.addWidget(total_cost_label)

            save_button = QPushButton("Сохранить в Excel")
            save_button.clicked.connect(self.save_to_excel)
            layout.addWidget(save_button)

            self.min_sum_window.setLayout(layout)
            self.min_sum_window.show()

    def save_to_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Excel Files (*.xlsx)")
        total_cost = self.portfolio.calculate_min_portfolio_cost()
        if file_path:
            data = {
                "Акция": list(self.portfolio.stock_weights.keys()),
                "Вес в портфеле": list(self.portfolio.stock_weights.values()),
                "Кол-во лотов": [stock.num_lots for sector in self.portfolio.sectors for stock in sector.stocks ]
            }

            df = pd.DataFrame(data)
            df.loc[len(df.index)] = ["Итого", "", total_cost]

            df.to_excel(file_path, index=False)

    def load_from_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "Excel Files (*.xlsx)")
        if filename:
            self.portfolio.load_from_xlsx(filename)

            self.update_portfolio_table()
            QMessageBox.information(self, "Загрузка", "Портфель успешно загружен!")

    def show_about_dialog(self):
        QMessageBox.information(self, "О программе", "Разработано в рамках ВКР НИУ ВШЭ. Бушуев В.В.")

    def show_table_context_menu(self, position):
        # Создаем меню
        menu = QMenu(self)

        # Добавляем действия
        add_action = menu.addAction("Добавить акцию")
        remove_action = menu.addAction("Удалить акцию")

        # Показываем меню в позиции курсора
        action = menu.exec_(self.portfolio_table.viewport().mapToGlobal(position))

        # Обрабатываем выбор действия
        if action == add_action:
            self.add_stock()
        elif action == remove_action:
            self.remove_stock()

    def add_stock(self):
        ticker, ok = QInputDialog.getText(self, "Добавить акцию", "Введите тикер:")
        if ok and ticker:
            for sector in self.portfolio.sectors:
                for stock in sector.stocks:
                    if ticker == stock.ticker: 
                        return

            stock = Stock(ticker)
            sector = next((s for s in self.portfolio.sectors if s.name == stock.sector), None)
            if not sector:
                sector = Sector(stock.sector)
                sector.add_stock(stock)
                self.portfolio.add_sector(sector)
            else:
                sector.add_stock(stock)
            self.portfolio.calculate_sector_weights()
            self.update_portfolio_table()

    def remove_stock(self):
        ticker, ok = QInputDialog.getText(self, "Удалить акцию", "Введите тикер:")
        if ok and ticker:
            self.portfolio.remove_stock(ticker)
            self.update_portfolio_table()

    def update_portfolio_table(self):
        self.portfolio_table.setRowCount(0)
        self.efficient_portfolio_table.setRowCount(0)
        # Генерация случайных цветов для секторов
        for sector in self.portfolio.sectors:
            if sector.name not in self.sector_colors:
                self.sector_colors[sector.name] = QColor(
                    random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)
                )

        for sector in self.portfolio.sectors:
            for stock in sector.stocks:
                row = self.portfolio_table.rowCount()
                self.portfolio_table.insertRow(row)
                self.portfolio_table.setItem(row, 0, QTableWidgetItem(sector.name))
                self.portfolio_table.setItem(row, 1, QTableWidgetItem(stock.ticker))
                self.portfolio_table.setItem(row, 2, QTableWidgetItem(stock.company_name))
                self.portfolio_table.setItem(row, 3, QTableWidgetItem(f"{stock.current_price:.2f}"))
                self.portfolio_table.setItem(row, 4, QTableWidgetItem(f"{stock.return_5y}"))
                self.portfolio_table.setItem(row, 5, QTableWidgetItem(f"{stock.volatility_5y}"))
                self.portfolio_table.setItem(row, 6, QTableWidgetItem(f"{stock.buffet_score:.2f}"))
                self.portfolio_table.setItem(row, 7, QTableWidgetItem(f"{stock.multipliers_score:.2f}"))
                self.portfolio_table.setItem(row, 8, QTableWidgetItem(f"{stock.vwap_score:.2f}"))
                self.portfolio_table.setItem(row, 9, QTableWidgetItem(f"{stock.dividend_score:.2f}"))
                self.portfolio_table.setItem(row, 10, QTableWidgetItem(f"{stock.total_score:.2f}"))
                self.portfolio_table.setItem(row, 11, QTableWidgetItem(f"{sector.average_score:.2f}"))
                self.portfolio_table.setItem(row, 12, QTableWidgetItem(f"{self.portfolio.stock_weights.get(stock.ticker, 0):.2f}"))
                self.portfolio_table.setItem(row, 13, QTableWidgetItem(f"{stock.lot_price:.2f}"))
                self.portfolio_table.setItem(row, 14, QTableWidgetItem(f"{stock.num_lots}"))
                self.portfolio_table.setItem(row, 15, QTableWidgetItem(f"{self.portfolio.stock_weights.get(stock.ticker, 0):.2f}"))
                
                # Устанавливаем цвет фона для строки
                for column in range(16):
                    self.portfolio_table.item(row, column).setBackground(self.sector_colors[sector.name])

                row = self.efficient_portfolio_table.rowCount()
                self.efficient_portfolio_table.insertRow(row)
                self.efficient_portfolio_table.setItem(row, 0, QTableWidgetItem(stock.ticker))
                self.efficient_portfolio_table.setItem(row, 1, QTableWidgetItem(stock.company_name))
        
        if len(list(self.portfolio.stock_weights.keys())) == 0:
            self.min_volatility_label.setText(f"Минимальная волатильность: 0")
            self.expected_return_label.setText(f"Ожидаемая доходность: 0")
            self.sum_input.setPlaceholderText(f"Минимальная рекомендованная сумма: 0")
            self.efficient_portfolio_table.setRowCount(0)
            self.figure.clear()
            self.canvas.draw()
        else:
            final_weights, data, gmv_weights, mve_weights, combined_volatility, combined_return = calculate_efficient_frontier.main(list(self.portfolio.stock_weights.keys()))
            self.min_volatility_label.setText(f"Минимальная волатильность: {combined_volatility:.2f}")
            self.expected_return_label.setText(f"Ожидаемая доходность: {combined_return:.2f}")
            for row in range(len(final_weights)):
                self.efficient_portfolio_table.setItem(row, 2, QTableWidgetItem(f"{final_weights[row]:.2f}"))

            self.plot_efficient_frontier(data, gmv_weights, mve_weights)
            self.add_portfolio_return_and_volatility_point()
            self.portfolio_table.resizeColumnsToContents()
            self.sum_input.setPlaceholderText(f"Минимальная рекомендованная сумма: {int(self.portfolio.calculate_min_portfolio_cost())}")

    def plot_efficient_frontier(self, data, gmv_weights, mve_weights):
        # Очищаем предыдущий график
        self.figure.clear()

        # Создаем оси
        self.ax = self.figure.add_subplot(111)

        # Передаем оси и данные в функцию построения
        calculate_efficient_frontier.plot_efficient_frontier(self.ax, data, gmv_weights, mve_weights)

        # Перерисовываем график на canvas
        self.canvas.draw()

    def add_portfolio_return_and_volatility_point(self):
        try:
            self.portfolio_return_and_volatility_point.remove()
        except:
            pass

        x, y = calculate_portfolio_return_and_volatility.main(list(self.portfolio.real_stock_weights.keys()), self.portfolio.real_stock_weights.values())
        self.portfolio.returns = x
        self.portfolio.volatility = y
        self.portfolio_return_and_volatility_point = self.ax.scatter(y, x, color='red', label='Point (1, 1)')
        
        # Перерисовываем график на canvas
        self.canvas.draw()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Выход", "Сохранить изменения перед выходом?",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.save_to_file()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
