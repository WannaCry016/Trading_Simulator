import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QLineEdit, QGroupBox, QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QDoubleValidator
from core.websocket_client import WebSocketWorker
from core.trade_analyzer import FeeTier


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trade Execution Simulator")
        self.setMinimumSize(900, 600)
        self.thread = None
        self.worker = None

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Trade Execution Simulator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 700; padding-bottom: 20px;")
        main_layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # ========== INPUT GROUP ==========
        input_group = QGroupBox("Input Parameters")
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 1.5px solid #4A90E2;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
        """)
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(14)
        input_layout.setHorizontalSpacing(20)

        label_style = "font-size: 14px;"

        self.exchange_input = QComboBox()
        self.exchange_input.addItems(["OKX"])

        self.asset_input = QComboBox()
        self.asset_input.addItems(["BTC/USDT"])

        self.order_type_input = QComboBox()
        self.order_type_input.addItems(["Market"])

        self.usd_amount_input = QLineEdit("100")
        self.usd_amount_input.setValidator(QDoubleValidator(0.0, 1e6, 2))

        self.volatility_input = QLineEdit("0.75")
        self.volatility_input.setValidator(QDoubleValidator(0.0, 100.0, 2))

        self.fee_tier_input = QComboBox()
        self.fee_tier_input.addItems(["Tier 1", "Tier 2", "Tier 3"])

        # Add widgets to input layout
        input_layout.addWidget(QLabel("Exchange:"), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        input_layout.addWidget(self.exchange_input, 0, 1)
        input_layout.addWidget(QLabel("Spot Asset:"), 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
        input_layout.addWidget(self.asset_input, 1, 1)
        input_layout.addWidget(QLabel("Order Type:"), 2, 0, alignment=Qt.AlignmentFlag.AlignRight)
        input_layout.addWidget(self.order_type_input, 2, 1)
        input_layout.addWidget(QLabel("Quantity (USD):"), 3, 0, alignment=Qt.AlignmentFlag.AlignRight)
        input_layout.addWidget(self.usd_amount_input, 3, 1)
        input_layout.addWidget(QLabel("Volatility:"), 4, 0, alignment=Qt.AlignmentFlag.AlignRight)
        input_layout.addWidget(self.volatility_input, 4, 1)
        input_layout.addWidget(QLabel("Fee Tier:"), 5, 0, alignment=Qt.AlignmentFlag.AlignRight)
        input_layout.addWidget(self.fee_tier_input, 5, 1)

        self.set_button = QPushButton("Set")
        self.set_button.setStyleSheet(
            "padding: 6px 18px; font-size: 14px; background-color: #4A90E2; color: white; border-radius: 4px;"
        )
        self.set_button.clicked.connect(self.start_worker)
        input_layout.addWidget(self.set_button, 6, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        input_group.setLayout(input_layout)
        input_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # ========== OUTPUT GROUP ==========
        output_group = QGroupBox("Live Output")
        output_group.setStyleSheet(input_group.styleSheet())
        output_layout = QGridLayout()
        output_layout.setVerticalSpacing(14)
        output_layout.setHorizontalSpacing(20)

        label_bold_style = "font-weight: 600; font-size: 14px;"
        value_style = "font-size: 14px; color: #333;"

        self.top_ask = QLabel("$0.00")
        self.top_bid = QLabel("$0.00")
        self.slippage_label = QLabel("0.00000 %")
        self.fee_label = QLabel("$0.00")
        self.impact_label = QLabel("$0.00")
        self.net_cost_label = QLabel("$0.00")
        self.maker_taker_label = QLabel("Maker: 0.0000 | Taker: 0.0000")

        output_layout.addWidget(QLabel("Top Ask:"), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        output_layout.addWidget(self.top_ask, 0, 1)
        output_layout.addWidget(QLabel("Top Bid:"), 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
        output_layout.addWidget(self.top_bid, 1, 1)
        output_layout.addWidget(QLabel("Expected Slippage:"), 2, 0, alignment=Qt.AlignmentFlag.AlignRight)
        output_layout.addWidget(self.slippage_label, 2, 1)
        output_layout.addWidget(QLabel("Expected Fees:"), 3, 0, alignment=Qt.AlignmentFlag.AlignRight)
        output_layout.addWidget(self.fee_label, 3, 1)
        output_layout.addWidget(QLabel("Market Impact:"), 4, 0, alignment=Qt.AlignmentFlag.AlignRight)
        output_layout.addWidget(self.impact_label, 4, 1)
        output_layout.addWidget(QLabel("Net Cost:"), 5, 0, alignment=Qt.AlignmentFlag.AlignRight)
        output_layout.addWidget(self.net_cost_label, 5, 1)
        output_layout.addWidget(QLabel("Maker/Taker Ratio:"), 6, 0, alignment=Qt.AlignmentFlag.AlignRight)
        output_layout.addWidget(self.maker_taker_label, 6, 1)

        for row in range(7):
            for col in [0, 1]:
                item = output_layout.itemAtPosition(row, col)
                if item and item.widget():
                    item.widget().setStyleSheet(label_bold_style if col == 0 else value_style)

        output_group.setLayout(output_layout)
        output_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # Add input and output panels
        content_layout.addWidget(input_group, stretch=1)
        content_layout.addWidget(output_group, stretch=1)
        main_layout.addLayout(content_layout)

        # ========== LATENCY GROUP ==========
        latency_group = QGroupBox("Latency Metrics")
        latency_group.setStyleSheet(input_group.styleSheet())

        latency_layout = QGridLayout()
        latency_layout.setVerticalSpacing(10)
        latency_layout.setHorizontalSpacing(20)

        self.stream_latency_label = QLabel("0 ms")
        self.processing_latency_label = QLabel("0 ms")
        self.ui_latency_label = QLabel("0 ms")
        self.total_latency_label = QLabel("0 ms")

        latency_layout.addWidget(QLabel("Stream Latency:"), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        latency_layout.addWidget(self.stream_latency_label, 0, 1)
        latency_layout.addWidget(QLabel("Processing Latency:"), 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
        latency_layout.addWidget(self.processing_latency_label, 1, 1)
        latency_layout.addWidget(QLabel("UI Latency:"), 2, 0, alignment=Qt.AlignmentFlag.AlignRight)
        latency_layout.addWidget(self.ui_latency_label, 2, 1)
        latency_layout.addWidget(QLabel("Total Latency:"), 3, 0, alignment=Qt.AlignmentFlag.AlignRight)
        latency_layout.addWidget(self.total_latency_label, 3, 1)

        for row in range(4):
            for col in [0, 1]:
                item = latency_layout.itemAtPosition(row, col)
                if item and item.widget():
                    item.widget().setStyleSheet(label_bold_style if col == 0 else value_style)

        latency_group.setLayout(latency_layout)
        main_layout.addWidget(latency_group)

        self.setLayout(main_layout)
        self.start_worker()

    def get_fee_tier(self):
        selected = self.fee_tier_input.currentText().strip().lower()
        if "2" in selected:
            return FeeTier.TIER2
        elif "3" in selected:
            return FeeTier.TIER3
        return FeeTier.TIER1

    def start_worker(self):
        if self.worker:
            self.worker.stop()
        if self.thread:
            self.thread.quit()
            self.thread.wait()

        try:
            usd_amount = float(self.usd_amount_input.text())
        except ValueError:
            usd_amount = 100.0

        fee_tier = self.get_fee_tier()

        self.thread = QThread()
        self.worker = WebSocketWorker(
            host="ws.gomarket-cpp.goquant.io",
            port="443",
            target="/ws/l2-orderbook/okx/BTC-USDT-SWAP",
            usd_amount=usd_amount,
            fee_tier=fee_tier
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.result_signal.connect(self.display_result)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def display_result(self, result):
        start_ui_time = time.perf_counter()

        self.top_ask.setText(f"${result['top_ask'].price:.2f}")
        self.top_bid.setText(f"${result['top_bid'].price:.2f}")

        self.slippage_label.setText(f"{result['slippage']:.5f} %")
        self.fee_label.setText(f"${result['fee']:.2f}")
        self.impact_label.setText(f"${result['impact']:.2f}")
        self.net_cost_label.setText(f"${result['net_cost']:.2f}")
        self.maker_taker_label.setText(
            f"Maker: {result['maker_prob']:.4f} | Taker: {result['taker_prob']:.4f}"
        )

        stream_latency = result.get('stream_latency_ms', 0)
        processing_latency = result.get('processing_latency_ms', 0)
        ui_latency = (time.perf_counter() - start_ui_time) * 1000

        self.stream_latency_label.setText(f"{stream_latency:.2f} ms")
        self.processing_latency_label.setText(f"{processing_latency:.2f} ms")
        self.ui_latency_label.setText(f"{ui_latency:.2f} ms")
        self.total_latency_label.setText(f"{(stream_latency + processing_latency + ui_latency):.2f} ms")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
