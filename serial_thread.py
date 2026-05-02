import serial
from PyQt6.QtCore import QThread, pyqtSignal

class SerialThread(QThread):
    data_received = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, port, baud):
        super().__init__()
        self.port = port
        self.baud = baud
        self.ser = None
        self.running = False

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
            self.running = True
            print(f"✅ 串口 {self.port} 打开成功  波特率:{self.baud}")

            while self.running:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(1)
                    if data:
                        hex_value = int.from_bytes(data, byteorder='big')
                        self.data_received.emit(hex_value)
                        # print(f'serial received：{hex_value} (0x{hex_value:02X})')

        except Exception as e:
            error_msg = f"串口错误：{e}"
            print(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)

        finally:
            self.running = False
            # 只有串口对象存在 且 已打开 才关闭
            if self.ser is not None and self.ser.is_open:
                try:
                    self.ser.close()
                except OSError:
                    pass

    def stop_serial(self):
        self.running = False