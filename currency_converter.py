import sys
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
                             QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import Qt


class CurrencyConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.title_label = QLabel("Currency Converter", self)
        self.amount_input = QLineEdit(self)
        self.from_input = QLineEdit(self)
        self.to_input = QLineEdit(self)
        self.convert_button = QPushButton("Convert", self)
        self.result_label = QLabel(self)
        self.rate_label = QLabel(self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Currency Converter")

        vbox = QVBoxLayout()

        self.amount_input.setPlaceholderText("Amount (e.g. 100)")
        self.from_input.setPlaceholderText("From (e.g. USD)")
        self.to_input.setPlaceholderText("To (e.g. INR)")

        hbox = QHBoxLayout()
        hbox.addWidget(self.from_input)
        hbox.addWidget(self.to_input)

        vbox.addWidget(self.title_label)
        vbox.addWidget(self.amount_input)
        vbox.addLayout(hbox)
        vbox.addWidget(self.convert_button)
        vbox.addWidget(self.result_label)
        vbox.addWidget(self.rate_label)

        self.setLayout(vbox)

        self.title_label.setAlignment(Qt.AlignCenter)
        self.amount_input.setAlignment(Qt.AlignCenter)
        self.from_input.setAlignment(Qt.AlignCenter)
        self.to_input.setAlignment(Qt.AlignCenter)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.rate_label.setAlignment(Qt.AlignCenter)

        self.title_label.setObjectName("title_label")
        self.amount_input.setObjectName("amount_input")
        self.from_input.setObjectName("from_input")
        self.to_input.setObjectName("to_input")
        self.convert_button.setObjectName("convert_button")
        self.result_label.setObjectName("result_label")
        self.rate_label.setObjectName("rate_label")

        self.setStyleSheet("""
            QLabel, QPushButton {
                font-family: calibri;
            }
            QLabel#title_label {
                font-size: 40px;
                font-style: italic;
            }
            QLineEdit#amount_input {
                font-size: 36px;
            }
            QLineEdit#from_input, QLineEdit#to_input {
                font-size: 32px;
            }
            QPushButton#convert_button {
                font-size: 30px;
                font-weight: bold;
            }
            QLabel#result_label {
                font-size: 56px;
                font-weight: bold;
            }
            QLabel#rate_label {
                font-size: 28px;
            }
        """)

        self.convert_button.clicked.connect(self.convert_currency)

    def convert_currency(self):
        raw_amount = self.amount_input.text().strip()
        base = self.from_input.text().strip().upper()
        target = self.to_input.text().strip().upper()

        try:
            amount = float(raw_amount)
            if amount <= 0:
                self.display_error("Invalid Amount:\nEnter a number greater than 0")
                return
        except ValueError:
            self.display_error("Invalid Amount:\nPlease enter a valid number")
            return

        if not base or not target:
            self.display_error("Missing Currency:\nEnter both currency codes (e.g. USD, INR)")
            return

        if base == target:
            self.result_label.setStyleSheet("font-size: 56px; font-weight: bold;")
            self.result_label.setText(f"{amount:,.2f} {target}")
            self.rate_label.setText(f"1 {base} = 1.0000 {target}")
            return

        url = "https://api.frankfurter.dev/v1/latest"
        params = {
            "amount": amount,
            "base": base,
            "symbols": target,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            rates = data.get("rates", {})
            if target not in rates:
                self.display_error(f"Unsupported Currency:\nCheck codes '{base}' and '{target}'")
                return

            converted = rates[target]
            unit_rate = converted / amount
            self.display_result(amount, base, converted, target, unit_rate)

        except requests.exceptions.HTTPError as http_error:
            status = http_error.response.status_code if http_error.response is not None else None
            match status:
                case 400 | 404:
                    self.display_error("Invalid Currency Code:\nCheck 3-letter codes like USD or INR")
                case 429:
                    self.display_error("Too Many Requests:\nPlease wait a moment and try again")
                case 500:
                    self.display_error("Internal Server Error:\nPlease try again later")
                case 502:
                    self.display_error("Bad Gateway:\nInvalid response from the server")
                case 503:
                    self.display_error("Service Unavailable:\nServer is down")
                case 504:
                    self.display_error("Gateway Timeout:\nNo response from the server")
                case _:
                    self.display_error(f"HTTP error occurred:\n{http_error}")

        except requests.exceptions.ConnectionError:
            self.display_error("Connection Error:\nCheck your internet connection")
        except requests.exceptions.Timeout:
            self.display_error("Timeout Error:\nThe request timed out")
        except requests.exceptions.TooManyRedirects:
            self.display_error("Too many Redirects:\nCheck the URL")
        except requests.exceptions.RequestException as req_error:
            self.display_error(f"Request Error:\n{req_error}")

    def display_error(self, message):
        self.result_label.setStyleSheet("font-size: 28px; font-weight: normal;")
        self.result_label.setText(message)
        self.rate_label.clear()

    def display_result(self, amount, base, converted, target, unit_rate):
        self.result_label.setStyleSheet("font-size: 56px; font-weight: bold;")
        self.result_label.setText(f"{converted:,.2f} {target}")
        self.rate_label.setText(f"{amount:,.2f} {base}  |  1 {base} = {unit_rate:.4f} {target}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter_app = CurrencyConverterApp()
    converter_app.show()
    sys.exit(app.exec_())