import sys
# 解决 Ubuntu Wayland 无标题栏、QT 报错问题
import os
# 自动判断系统：只有 Linux(Ubuntu) 才启用 XCB 修复
if sys.platform.startswith("linux"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    os.environ["EGL_PLATFORM"] = "x11"

from PyQt6.QtWidgets import QApplication
from mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())