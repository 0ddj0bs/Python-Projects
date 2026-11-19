import sys
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
                             QLineEdit, QPushButton, QVBoxLayout)
from PyQt5.QtCore import Qt


class GitHubLookupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.username_label = QLabel("Enter GitHub username:", self)
        self.username_input = QLineEdit(self)
        self.lookup_button = QPushButton("Lookup Profile", self)
        self.name_label = QLabel(self)
        self.bio_label = QLabel(self)
        self.stats_label = QLabel(self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("GitHub Profile Lookup")

        vbox = QVBoxLayout()

        self.username_input.setPlaceholderText("e.g. torvalds")
        self.bio_label.setWordWrap(True)

        vbox.addWidget(self.username_label)
        vbox.addWidget(self.username_input)
        vbox.addWidget(self.lookup_button)
        vbox.addWidget(self.name_label)
        vbox.addWidget(self.bio_label)
        vbox.addWidget(self.stats_label)

        self.setLayout(vbox)

        self.username_label.setAlignment(Qt.AlignCenter)
        self.username_input.setAlignment(Qt.AlignCenter)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.bio_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setAlignment(Qt.AlignCenter)

        self.username_label.setObjectName("username_label")
        self.username_input.setObjectName("username_input")
        self.lookup_button.setObjectName("lookup_button")
        self.name_label.setObjectName("name_label")
        self.bio_label.setObjectName("bio_label")
        self.stats_label.setObjectName("stats_label")

        self.setStyleSheet("""
            QLabel, QPushButton {
                font-family: calibri;
            }
            QLabel#username_label {
                font-size: 38px;
                font-style: italic;
            }
            QLineEdit#username_input {
                font-size: 36px;
            }
            QPushButton#lookup_button {
                font-size: 30px;
                font-weight: bold;
            }
            QLabel#name_label {
                font-size: 52px;
                font-weight: bold;
            }
            QLabel#bio_label {
                font-size: 30px;
            }
            QLabel#stats_label {
                font-size: 32px;
            }
        """)

        self.lookup_button.clicked.connect(self.get_profile)

    def get_profile(self):
        username = self.username_input.text().strip()
        if not username:
            self.display_error("Missing Username:\nPlease enter a GitHub username")
            return

        url = f"https://api.github.com/users/{username}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Python-PyQt5-GitHub-Lookup",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.display_profile(data)

        except requests.exceptions.HTTPError as http_error:
            status = http_error.response.status_code if http_error.response is not None else None
            match status:
                case 400:
                    self.display_error("Bad Request:\nCheck the username format")
                case 403:
                    self.display_error("Rate Limit / Forbidden:\nGitHub API limit reached or access denied")
                case 404:
                    self.display_error("Not Found:\nGitHub user does not exist")
                case 500:
                    self.display_error("Internal Server Error:\nGitHub server error")
                case 502:
                    self.display_error("Bad Gateway:\nInvalid response from GitHub")
                case 503:
                    self.display_error("Service Unavailable:\nGitHub service is down")
                case 504:
                    self.display_error("Gateway Timeout:\nGitHub took too long to respond")
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
        self.name_label.setStyleSheet("font-size: 30px; font-weight: normal;")
        self.name_label.setText(message)
        self.bio_label.clear()
        self.stats_label.clear()

    def display_profile(self, data):
        self.name_label.setStyleSheet("font-size: 52px; font-weight: bold;")
        display_name = data.get("name") or data.get("login", "Unknown User")
        login = data.get("login", "")
        bio = data.get("bio") or "No bio available."
        repos = data.get("public_repos", 0)
        followers = data.get("followers", 0)
        following = data.get("following", 0)

        self.name_label.setText(f"{display_name} (@{login})")
        self.bio_label.setText(bio)
        self.stats_label.setText(
            f"Repos: {repos}  |  Followers: {followers}  |  Following: {following}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    lookup_app = GitHubLookupApp()
    lookup_app.show()
    sys.exit(app.exec_())