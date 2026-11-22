import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
import requests


class CoinPulseApp(QWidget):
    def __init__(self):
        super().__init__()
        # coin_id -> {"holdings": float, "price": float, "change_24h": float}
        self.portfolio = {
            "bitcoin": {"holdings": 0.05, "price": None, "change_24h": None},
            "ethereum": {"holdings": 1.2, "price": None, "change_24h": None},
            "solana": {"holdings": 10.0, "price": None, "change_24h": None},
        }
        self.init_ui()
        self.refresh_prices()

    def init_ui(self):
        self.setWindowTitle("CoinPulse — Crypto Watchlist & Portfolio Tracker")
        self.resize(820, 580)

        root = QVBoxLayout()
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Header + Currency selector + Refresh
        top_bar = QHBoxLayout()
        title = QLabel("CoinPulse")
        title.setObjectName("title_label")

        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["usd", "inr"])
        self.currency_combo.currentTextChanged.connect(self.refresh_prices)

        self.refresh_btn = QPushButton("Refresh Prices")
        self.refresh_btn.setObjectName("primary_btn")
        self.refresh_btn.clicked.connect(self.refresh_prices)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Currency:"))
        top_bar.addWidget(self.currency_combo)
        top_bar.addWidget(self.refresh_btn)

        # Add / Update coin row
        add_row = QHBoxLayout()
        self.coin_input = QLineEdit()
        self.coin_input.setPlaceholderText("CoinGecko ID (e.g., bitcoin, dogecoin, cardano)")
        self.coin_input.returnPressed.connect(self.add_or_update_coin)

        self.holdings_spin = QDoubleSpinBox()
        self.holdings_spin.setRange(0.0, 1_000_000_000.0)
        self.holdings_spin.setDecimals(4)
        self.holdings_spin.setValue(1.0)
        self.holdings_spin.setPrefix("Qty: ")

        self.add_btn = QPushButton("Add / Update")
        self.add_btn.setObjectName("secondary_btn")
        self.add_btn.clicked.connect(self.add_or_update_coin)

        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setObjectName("danger_btn")
        self.remove_btn.clicked.connect(self.remove_selected_coin)

        add_row.addWidget(self.coin_input, stretch=2)
        add_row.addWidget(self.holdings_spin)
        add_row.addWidget(self.add_btn)
        add_row.addWidget(self.remove_btn)

        # Summary banner
        self.summary_label = QLabel("Total Portfolio Value: --")
        self.summary_label.setObjectName("summary_label")

        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)

        # Watchlist table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Coin ID", "Holdings", "Price", "24h Change", "Value"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        root.addLayout(top_bar)
        root.addLayout(add_row)
        root.addWidget(self.summary_label)
        root.addWidget(self.status_label)
        root.addWidget(self.table)

        self.setLayout(root)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0b1120;
                color: #e2e8f0;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 14px;
            }
            QLabel#title_label {
                font-size: 26px;
                font-weight: bold;
                color: #38bdf8;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                color: #f8fafc;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton#primary_btn {
                background-color: #0284c7;
            }
            QPushButton#primary_btn:hover {
                background-color: #0369a1;
            }
            QPushButton#secondary_btn {
                background-color: #0d9488;
            }
            QPushButton#secondary_btn:hover {
                background-color: #0f766e;
            }
            QPushButton#danger_btn {
                background-color: #b91c1c;
            }
            QPushButton#danger_btn:hover {
                background-color: #991b1b;
            }
            QLabel#summary_label {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
                font-weight: bold;
                color: #f8fafc;
            }
            QLabel#status_label {
                color: #f87171;
                font-weight: bold;
            }
            QTableWidget {
                background-color: #1e293b;
                alternate-background-color: #162032;
                border: 1px solid #334155;
                border-radius: 8px;
                gridline-color: #334155;
            }
            QHeaderView::section {
                background-color: #334155;
                color: #f8fafc;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

    def set_error(self, msg):
        self.status_label.setText(msg)

    def clear_error(self):
        self.status_label.setText("")

    def add_or_update_coin(self):
        coin_id = self.coin_input.text().strip().lower()
        holdings = self.holdings_spin.value()

        if not coin_id:
            self.set_error("Enter a valid CoinGecko coin ID (e.g., bitcoin).")
            return

        existing = self.portfolio.get(coin_id, {"price": None, "change_24h": None})
        self.portfolio[coin_id] = {
            "holdings": holdings,
            "price": existing["price"],
            "change_24h": existing["change_24h"],
        }
        self.coin_input.clear()
        self.refresh_prices()

    def remove_selected_coin(self):
        row = self.table.currentRow()
        if row < 0:
            self.set_error("Select a row first to remove a coin.")
            return
        coin_item = self.table.item(row, 0)
        if coin_item:
            coin_id = coin_item.text()
            self.portfolio.pop(coin_id, None)
            self.clear_error()
            self.render_table()

    def refresh_prices(self):
        if not self.portfolio:
            self.render_table()
            return

        vs_currency = self.currency_combo.currentText()
        ids_param = ",".join(self.portfolio.keys())
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": ids_param,
            "vs_currencies": vs_currency,
            "include_24hr_change": "true",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            missing = []
            for coin_id, entry in self.portfolio.items():
                coin_data = data.get(coin_id)
                if not coin_data or vs_currency not in coin_data:
                    missing.append(coin_id)
                    continue
                entry["price"] = coin_data[vs_currency]
                entry["change_24h"] = coin_data.get(f"{vs_currency}_24h_change", 0.0)

            if missing:
                self.set_error(f"No market data found for: {', '.join(missing)}")
            else:
                self.clear_error()

            self.render_table()

        except requests.exceptions.HTTPError as err:
            code = err.response.status_code if err.response is not None else 0
            match code:
                case 400:
                    self.set_error("Bad Request (400): Check coin IDs or currency.")
                case 429:
                    self.set_error("Rate Limit (429): Too many requests to CoinGecko. Wait a bit.")
                case code if 500 <= code < 600:
                    self.set_error(f"Server Error ({code}): CoinGecko API is temporarily down.")
                case _:
                    self.set_error(f"HTTP Error ({code}): {err}")

        except requests.exceptions.ConnectionError:
            self.set_error("Connection Error: Check your internet connection.")
        except requests.exceptions.Timeout:
            self.set_error("Timeout Error: Request timed out.")
        except requests.exceptions.RequestException as err:
            self.set_error(f"Network Error: {err}")

    def format_money(self, amount, currency):
        symbol = "₹" if currency == "inr" else "$"
        if amount is None:
            return "--"
        if amount >= 1:
            return f"{symbol}{amount:,.2f}"
        return f"{symbol}{amount:.6f}"

    def render_table(self):
        currency = self.currency_combo.currentText()
        items = list(self.portfolio.items())
        self.table.setRowCount(len(items))

        total_value = 0.0
        has_any_price = False

        for row, (coin_id, info) in enumerate(items):
            holdings = info["holdings"]
            price = info["price"]
            change = info["change_24h"]

            value = (holdings * price) if price is not None else None
            if value is not None:
                total_value += value
                has_any_price = True

            id_item = QTableWidgetItem(coin_id)
            qty_item = QTableWidgetItem(f"{holdings:g}")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            price_item = QTableWidgetItem(self.format_money(price, currency))
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            if change is None:
                change_text = "--"
                change_color = QColor("#94a3b8")
            else:
                sign = "+" if change >= 0 else ""
                change_text = f"{sign}{change:.2f}%"
                change_color = QColor("#4ade80") if change >= 0 else QColor("#f87171")

            change_item = QTableWidgetItem(change_text)
            change_item.setForeground(change_color)
            change_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            val_item = QTableWidgetItem(self.format_money(value, currency))
            val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, qty_item)
            self.table.setItem(row, 2, price_item)
            self.table.setItem(row, 3, change_item)
            self.table.setItem(row, 4, val_item)

        if has_any_price:
            self.summary_label.setText(
                f"Total Portfolio Value: {self.format_money(total_value, currency)}"
            )
        else:
            self.summary_label.setText("Total Portfolio Value: --")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoinPulseApp()
    window.show()
    sys.exit(app.exec_())