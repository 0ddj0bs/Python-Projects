import sys
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
                             QLineEdit, QPushButton, QVBoxLayout)
from PyQt5.QtCore import Qt


class DictionaryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.word_label = QLabel("Enter an English word:", self)
        self.word_input = QLineEdit(self)
        self.lookup_button = QPushButton("Define Word", self)
        self.heading_label = QLabel(self)
        self.pos_label = QLabel(self)
        self.definition_label = QLabel(self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Dictionary Lookup")

        vbox = QVBoxLayout()

        self.word_input.setPlaceholderText("e.g. serendipity")
        self.definition_label.setWordWrap(True)

        vbox.addWidget(self.word_label)
        vbox.addWidget(self.word_input)
        vbox.addWidget(self.lookup_button)
        vbox.addWidget(self.heading_label)
        vbox.addWidget(self.pos_label)
        vbox.addWidget(self.definition_label)

        self.setLayout(vbox)

        self.word_label.setAlignment(Qt.AlignCenter)
        self.word_input.setAlignment(Qt.AlignCenter)
        self.heading_label.setAlignment(Qt.AlignCenter)
        self.pos_label.setAlignment(Qt.AlignCenter)
        self.definition_label.setAlignment(Qt.AlignCenter)

        self.word_label.setObjectName("word_label")
        self.word_input.setObjectName("word_input")
        self.lookup_button.setObjectName("lookup_button")
        self.heading_label.setObjectName("heading_label")
        self.pos_label.setObjectName("pos_label")
        self.definition_label.setObjectName("definition_label")

        self.setStyleSheet("""
            QLabel, QPushButton {
                font-family: calibri;
            }
            QLabel#word_label {
                font-size: 38px;
                font-style: italic;
            }
            QLineEdit#word_input {
                font-size: 36px;
            }
            QPushButton#lookup_button {
                font-size: 30px;
                font-weight: bold;
            }
            QLabel#heading_label {
                font-size: 52px;
                font-weight: bold;
            }
            QLabel#pos_label {
                font-size: 28px;
                font-style: italic;
            }
            QLabel#definition_label {
                font-size: 30px;
            }
        """)

        self.lookup_button.clicked.connect(self.get_definition)

    def get_definition(self):
        word = self.word_input.text().strip().lower()
        if not word:
            self.display_error("Missing Word:\nPlease enter a word to look up")
            return

        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.display_definition(data)

        except requests.exceptions.HTTPError as http_error:
            status = http_error.response.status_code if http_error.response is not None else None
            match status:
                case 400:
                    self.display_error("Bad Request:\nCheck the word you entered")
                case 404:
                    self.display_error("Word Not Found:\nNo definition found for that word")
                case 429:
                    self.display_error("Too Many Requests:\nPlease wait a moment and try again")
                case 500:
                    self.display_error("Internal Server Error:\nDictionary service error")
                case 502:
                    self.display_error("Bad Gateway:\nInvalid response from the server")
                case 503:
                    self.display_error("Service Unavailable:\nDictionary service is down")
                case 504:
                    self.display_error("Gateway Timeout:\nThe request timed out")
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
        self.heading_label.setStyleSheet("font-size: 30px; font-weight: normal;")
        self.heading_label.setText(message)
        self.pos_label.clear()
        self.definition_label.clear()

    def display_definition(self, data):
        if not isinstance(data, list) or not data:
            self.display_error("Unexpected Response:\nCould not parse dictionary data")
            return

        entry = data[0]
        word_text = entry.get("word", "")
        phonetic = entry.get("phonetic", "")
        if not phonetic:
            for item in entry.get("phonetics", []):
                if item.get("text"):
                    phonetic = item["text"]
                    break

        meanings = entry.get("meanings", [])
        part_of_speech = ""
        definition = "No definition available."
        example = ""

        if meanings:
            part_of_speech = meanings[0].get("partOfSpeech", "")
            definitions = meanings[0].get("definitions", [])
            if definitions:
                definition = definitions[0].get("definition", definition)
                example = definitions[0].get("example", "")

        self.heading_label.setStyleSheet("font-size: 52px; font-weight: bold;")
        self.heading_label.setText(f"{word_text}  {phonetic}".strip())
        self.pos_label.setText(part_of_speech)

        body_text = definition
        if example:
            body_text += f"\n\nExample: \"{example}\""
        self.definition_label.setText(body_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dict_app = DictionaryApp()
    dict_app.show()
    sys.exit(app.exec_())
    