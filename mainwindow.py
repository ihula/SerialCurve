import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtGui import QIntValidator  # 新增整数验证
import serial.tools.list_ports
from serial_thread import SerialThread
from excel_exporter import ExcelExporter  # 导入导出Excel模块


# 重写 QComboBox，实现点击刷新
class PortComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.refresh_ports()
        super().mouseReleaseEvent(event)

    def refresh_ports(self):
        current_text = self.currentText()
        self.clear()
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            self.addItem(p.device)
        if not ports:
            self.addItem("未找到串口")
        # 尝试恢复之前选中的项
        index = self.findText(current_text)
        if index >= 0:
            self.setCurrentIndex(index)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 串口实时绘图")
        self.resize(1000, 650)

        self.serial_thread = None
        self.x_data = []
        self.y_data = []

        # 主布局
        top_widget = QWidget()
        self.setCentralWidget(top_widget)
        main_layout = QVBoxLayout(top_widget)

        # 顶部控件行
        row_layout = QHBoxLayout()
        self.label_port = QLabel("串口号：")
        self.combo_port = PortComboBox()

        self.label_baud = QLabel("波特率：")
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.combo_baud.setCurrentText("9600")
        self.combo_baud.setMinimumWidth(100)
        self.combo_baud.adjustSize()

        self.btn_open = QPushButton("打开串口")
        self.btn_open.setMinimumWidth(80)
        self.btn_open.adjustSize()

        # ====================== 显示点数（限制大于0的整数）
        self.label_show_count = QLabel("显示点数：")
        self.edit_show_count = QLineEdit()
        self.edit_show_count.setText("50")
        self.edit_show_count.setFixedWidth(60)

        # ✅ 限制：只能输入 1~9999 的整数
        validator = QIntValidator(1, 99999999, self)
        self.edit_show_count.setValidator(validator)
        self.edit_show_count.editingFinished.connect(self.update_plot)

        self.btn_export = QPushButton("导出Excel")  # <--- 导出按钮
        self.btn_export.setMinimumWidth(80)

        # 布局添加按钮
        row_layout.addWidget(self.label_port)
        row_layout.addWidget(self.combo_port, stretch=1)
        row_layout.addWidget(self.label_baud)
        row_layout.addWidget(self.combo_baud)
        row_layout.addWidget(self.btn_open)
        row_layout.addSpacing(10)
        row_layout.addWidget(self.label_show_count)
        row_layout.addWidget(self.edit_show_count)
        row_layout.addSpacing(10)
        row_layout.addWidget(self.btn_export)
        main_layout.addLayout(row_layout)

        # 信号绑定
        self.btn_open.clicked.connect(self.toggle_serial)
        self.btn_export.clicked.connect(self.export_data)

        # 绘图
        self.plot_widget = pg.GraphicsLayoutWidget()
        main_layout.addWidget(self.plot_widget)
        self.plot = self.plot_widget.addPlot(title="实时波形曲线")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        # 开启鼠标拖动、滚轮缩放
        self.plot.setMouseEnabled(x=True, y=False)  # 只允许X轴拖动缩放，Y轴固定
        self.plot.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        self.curve = self.plot.plot(pen=pg.mkPen("#00ff88", width=2))

    # ========== 导出数据到 Excel ==========
    def export_data(self):
        if len(self.x_data) == 0 or len(self.y_data) == 0:
            QMessageBox.warning(self, "提示", "暂无数据可导出！")
            return

        success, result = ExcelExporter.export_to_excel(self.x_data, self.y_data)
        if success:
            QMessageBox.information(self, "成功", f"数据已导出：\n{result}")
        else:
            QMessageBox.critical(self, "失败", f"导出失败：\n{result}")

    def on_serial_error(self, msg):
        QMessageBox.critical(self, "串口错误", msg)
        self.btn_open.setText("打开串口")
        print(f"❌ UI层收到错误：{msg}")
        self.serial_thread = None

    def toggle_serial(self):
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop_serial()
            self.btn_open.setText("打开串口")
            print("🔌 串口已关闭")
        else:
            port = self.combo_port.currentText()
            baud = int(self.combo_baud.currentText())

            if not port or port == "未找到串口":
                QMessageBox.critical(self, "串口错误", "请选择串口")
                return

            self.serial_thread = SerialThread(port, baud)
            self.serial_thread.data_received.connect(self.on_data)
            self.serial_thread.error_occurred.connect(self.on_serial_error)
            self.serial_thread.start()
            self.btn_open.setText("关闭串口")

    def on_data(self, val):
        self.x_data.append(len(self.x_data))
        self.y_data.append(val)
        self.update_plot()

    def update_plot(self):
        self.curve.setData(self.x_data, self.y_data)

        # 读取显示点数（确保 >=1）
        try:
            show_count = int(self.edit_show_count.text())
            if show_count < 1:
                show_count = 50
        except ValueError:
            show_count = 50

        total = len(self.x_data)
        if total > show_count:
            x_min = self.x_data[-show_count]
            x_max = self.x_data[-1]
            self.plot.setXRange(x_min, x_max, padding=0)

    def closeEvent(self, event):
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop_serial()
            self.serial_thread.wait(1000)
            self.serial_thread = None
        event.accept()