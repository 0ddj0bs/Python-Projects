import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
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
import psutil


class SysPulseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []
        self.init_ui()
        self.refresh_stats()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(2000)

    def init_ui(self):
        self.setWindowTitle("SysPulse — System & Process Monitor")
        self.resize(860, 600)

        root = QVBoxLayout()
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Top bar
        top_bar = QHBoxLayout()
        title = QLabel("SysPulse")
        title.setObjectName("title_label")

        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["2s", "5s", "Paused"])
        self.interval_combo.currentTextChanged.connect(self.change_interval)

        self.refresh_btn = QPushButton("Refresh Now")
        self.refresh_btn.setObjectName("primary_btn")
        self.refresh_btn.clicked.connect(self.refresh_stats)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Interval:"))
        top_bar.addWidget(self.interval_combo)
        top_bar.addWidget(self.refresh_btn)

        # Filter row
        filter_row = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter processes by name or PID...")
        self.filter_input.textChanged.connect(self.render_table)

        self.clear_btn = QPushButton("Clear Filter")
        self.clear_btn.setObjectName("secondary_btn")
        self.clear_btn.clicked.connect(self.clear_filter)

        filter_row.addWidget(self.filter_input, stretch=1)
        filter_row.addWidget(self.clear_btn)

        # Summary banner
        self.summary_label = QLabel("CPU: --%  |  RAM: --%  |  Disk (/): --%")
        self.summary_label.setObjectName("summary_label")

        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)

        # Process table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Process Name", "PID", "CPU %", "Memory (MB)", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        root.addLayout(top_bar)
        root.addLayout(filter_row)
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
            QLineEdit, QComboBox {
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
            QLabel#summary_label {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-size: 17px;
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

    def change_interval(self, mode):
        if mode == "Paused":
            self.timer.stop()
            self.status_label.setText("Auto-refresh paused.")
        else:
            self.status_label.setText("")
            ms = 2000 if mode == "2s" else 5000
            self.timer.start(ms)

    def clear_filter(self):
        self.filter_input.clear()
        self.render_table()

    def refresh_stats(self):
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            ram_used_gb = mem.used / (1024 ** 3)
            ram_total_gb = mem.total / (1024 ** 3)

            disk_path = "C:\\" if sys.platform.startswith("win") else "/"
            disk = psutil.disk_usage(disk_path)

            self.summary_label.setText(
                f"CPU: {cpu_pct:.1f}%  |  "
                f"RAM: {mem.percent:.1f}% ({ram_used_gb:.1f}/{ram_total_gb:.1f} GB)  |  "
                f"Disk ({disk_path}): {disk.percent:.1f}%"
            )

            rows = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
                try:
                    info = proc.info
                    mem_info = info.get("memory_info")
                    mem_mb = (mem_info.rss / (1024 ** 2)) if mem_info else 0.0
                    rows.append(
                        {
                            "name": info.get("name") or "unknown",
                            "pid": info.get("pid", 0),
                            "cpu": float(info.get("cpu_percent") or 0.0),
                            "mem_mb": mem_mb,
                            "status": info.get("status") or "unknown",
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            rows.sort(key=lambda r: r["mem_mb"], reverse=True)
            self.processes = rows[:100]
            if self.interval_combo.currentText() != "Paused":
                self.status_label.setText("")
            self.render_table()

        except Exception as err:
            self.status_label.setText(f"Telemetry Error: {err}")

    def render_table(self):
        query = self.filter_input.text().strip().lower()
        if query:
            filtered = [
                p for p in self.processes
                if query in p["name"].lower() or query in str(p["pid"])
            ]
        else:
            filtered = self.processes

        self.table.setRowCount(len(filtered))

        for row, proc in enumerate(filtered):
            name_item = QTableWidgetItem(proc["name"])
            pid_item = QTableWidgetItem(str(proc["pid"]))
            pid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            cpu_val = proc["cpu"]
            cpu_item = QTableWidgetItem(f"{cpu_val:.1f}%")
            cpu_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if cpu_val >= 25.0:
                cpu_item.setForeground(QColor("#f87171"))
            elif cpu_val >= 5.0:
                cpu_item.setForeground(QColor("#fbbf24"))
            else:
                cpu_item.setForeground(QColor("#4ade80"))

            mem_item = QTableWidgetItem(f"{proc['mem_mb']:.1f}")
            mem_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            status_item = QTableWidgetItem(proc["status"])

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, pid_item)
            self.table.setItem(row, 2, cpu_item)
            self.table.setItem(row, 3, mem_item)
            self.table.setItem(row, 4, status_item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SysPulseApp()
    window.show()
    sys.exit(app.exec_())