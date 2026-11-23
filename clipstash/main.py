import sqlite3
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ClipStashApp(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).resolve().parent / "clipstash.db"
        self.init_db()
        self.init_ui()
        self.load_snippets()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    tag TEXT NOT NULL DEFAULT 'general',
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                )
                """
            )

    def init_ui(self):
        self.setWindowTitle("ClipStash — Local Snippet & Command Stash")
        self.resize(900, 650)

        root = QVBoxLayout()
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        top_bar = QHBoxLayout()
        title = QLabel("ClipStash")
        title.setObjectName("title_label")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, tag, or snippet...")
        self.search_input.textChanged.connect(self.load_snippets)

        self.clear_search_btn = QPushButton("Reset")
        self.clear_search_btn.setObjectName("neutral_btn")
        self.clear_search_btn.clicked.connect(self.reset_search)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.search_input, stretch=1)
        top_bar.addWidget(self.clear_search_btn)

        editor_box = QGroupBox("Save Snippet")
        editor_layout = QVBoxLayout()
        editor_layout.setSpacing(8)

        meta_row = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Title (e.g., git undo last commit)")

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Tag (e.g., git, sql, shell)")
        self.tag_input.setMaximumWidth(220)

        self.save_btn = QPushButton("Save Snippet")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self.save_snippet)

        meta_row.addWidget(self.title_input, stretch=2)
        meta_row.addWidget(self.tag_input, stretch=1)
        meta_row.addWidget(self.save_btn)

        self.content_input = QPlainTextEdit()
        self.content_input.setPlaceholderText("Paste command, snippet, or note here...")
        self.content_input.setMaximumHeight(95)

        editor_layout.addLayout(meta_row)
        editor_layout.addWidget(self.content_input)
        editor_box.setLayout(editor_layout)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Tag", "Snippet", "Saved"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.preview_selected)

        action_row = QHBoxLayout()
        self.copy_btn = QPushButton("Copy Selected")
        self.copy_btn.setObjectName("secondary_btn")
        self.copy_btn.clicked.connect(self.copy_selected)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.clicked.connect(self.delete_selected)

        action_row.addStretch()
        action_row.addWidget(self.copy_btn)
        action_row.addWidget(self.delete_btn)

        root.addLayout(top_bar)
        root.addWidget(editor_box)
        root.addWidget(self.status_label)
        root.addWidget(self.table)
        root.addLayout(action_row)

        self.setLayout(root)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet(
            """
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
            QGroupBox {
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 14px;
                font-weight: bold;
                color: #cbd5e1;
            }
            QLineEdit, QPlainTextEdit {
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
            QPushButton#neutral_btn {
                background-color: #334155;
            }
            QPushButton#neutral_btn:hover {
                background-color: #475569;
            }
            QLabel#status_label {
                color: #38bdf8;
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
            """
        )

    def set_status(self, text: str):
        self.status_label.setText(text)

    def reset_search(self):
        self.search_input.clear()
        self.load_snippets()

    def save_snippet(self):
        title = self.title_input.text().strip()
        tag = self.tag_input.text().strip().lower() or "general"
        content = self.content_input.toPlainText().strip()

        if not title or not content:
            self.set_status("Add both a title and snippet content before saving.")
            return

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO snippets (title, tag, content) VALUES (?, ?, ?)",
                (title, tag, content),
            )

        self.title_input.clear()
        self.tag_input.clear()
        self.content_input.clear()
        self.load_snippets()
        self.set_status(f"Saved '{title}' under [{tag}].")

    def load_snippets(self):
        query = f"%{self.search_input.text().strip().lower()}%"

        with self._connect() as conn:
            if self.search_input.text().strip():
                rows = conn.execute(
                    """
                    SELECT id, title, tag, content, created_at
                    FROM snippets
                    WHERE lower(title) LIKE ? OR lower(tag) LIKE ? OR lower(content) LIKE ?
                    ORDER BY id DESC
                    """,
                    (query, query, query),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, title, tag, content, created_at FROM snippets ORDER BY id DESC"
                ).fetchall()

        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            id_item = QTableWidgetItem(str(row["id"]))
            id_item.setData(Qt.UserRole, row["content"])
            id_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            title_item = QTableWidgetItem(row["title"])
            tag_item = QTableWidgetItem(row["tag"])

            single_line_preview = " ".join(row["content"].splitlines())
            snippet_item = QTableWidgetItem(single_line_preview)
            snippet_item.setToolTip(row["content"])

            date_item = QTableWidgetItem(row["created_at"])

            self.table.setItem(row_idx, 0, id_item)
            self.table.setItem(row_idx, 1, title_item)
            self.table.setItem(row_idx, 2, tag_item)
            self.table.setItem(row_idx, 3, snippet_item)
            self.table.setItem(row_idx, 4, date_item)

    def _selected_row_content(self) -> tuple[int | None, str | None, str | None]:
        row = self.table.currentRow()
        if row < 0:
            return None, None, None
        id_item = self.table.item(row, 0)
        title_item = self.table.item(row, 1)
        if not id_item or not title_item:
            return None, None, None
        return int(id_item.text()), title_item.text(), id_item.data(Qt.UserRole)

    def preview_selected(self):
        _, title, content = self._selected_row_content()
        if title and content is not None:
            self.set_status(f"Selected '{title}' — click 'Copy Selected' to copy full text.")

    def copy_selected(self):
        _, title, content = self._selected_row_content()
        if content is None:
            self.set_status("Select a snippet row first to copy it.")
            return
        QApplication.clipboard().setText(content)
        self.set_status(f"Copied '{title}' to clipboard.")

    def delete_selected(self):
        snippet_id, title, _ = self._selected_row_content()
        if snippet_id is None:
            self.set_status("Select a snippet row first to delete it.")
            return

        with self._connect() as conn:
            conn.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))

        self.load_snippets()
        self.set_status(f"Deleted '{title}'.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClipStashApp()
    window.show()
    sys.exit(app.exec_())
