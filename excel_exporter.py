import pandas as pd
from datetime import datetime

class ExcelExporter:
    @staticmethod
    def export_to_excel(x_data, y_data):
        """
        将 X 轴(点数) 和 Y 轴(串口数据) 导出为 Excel 文件
        文件名自动带时间戳
        """
        try:
            # 构造数据
            data = {
                "点数": x_data,
                "串口数据(十进制)": y_data
            }

            # 自动生成文件名（带时间）
            filename = f"串口数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            # 导出
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)

            return True, filename

        except Exception as e:
            return False, str(e)