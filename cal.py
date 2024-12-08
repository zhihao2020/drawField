from PyQt5.QtWidgets import QApplication, QMessageBox, QMainWindow, QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QObject, QRectF
from ui.cal_area import CalWindow
from PyQt5.QtCore import QPoint
import sys
import pytesseract
import cv2
import numpy as np
from PyQt5.QtGui import QPen, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from ui.cal_area import CalWindow



class CalMain(QMainWindow, QObject):
    def __init__(self):
        super(CalMain, self).__init__()
        self.cal_ui = CalWindow()
        self.setWindowTitle('计算波及区域')
        self.setCentralWidget(self.cal_ui)
        
        self.cal_ui.pickColorButton.clicked.connect(self.select_colorbar)
        self.cal_ui.pickThemeButton.clicked.connect(self.select_body)
        # 导入图片
        self.cal_ui.pickSpecialButton.clicked.connect(self.load_file_png)
        self.mouse_press_event_flag = -1
        self.png_path = r".\ui\welcome.png"


    def load_file_png(self):
        name, _ = QFileDialog.getOpenFileName(self, "加载PNG文件", "", "CSV Files (*.png)")
        self.png_path = name
        self.scene_show_png()

    def load_png(self):
        with open("data.io") as f:
            for line in f:
                if line.startswith("cal_area_name:"):
                    self.png_path = line.split(": ", 1)[1].strip()
                    print(self.png_path)
                    img = cv2.imread(self.png_path)
                    if img is None:
                        QMessageBox.critical(self, "Error", f"Failed to load image: {self.png_path}")
                    self.scene_show_png()
                        
    def scene_show_png(self):
        self.cal_ui.scene.clear()
        pixmap = QPixmap(self.png_path)
        self.cal_ui.scene.addPixmap(pixmap)
        self.cal_ui.graphicsView.setScene(self.cal_ui.scene)
        self.cal_ui.graphicsView.setFixedSize(pixmap.size())
        self.cal_ui.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cal_ui.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def select_colorbar(self):
        self.mouse_press_event_flag = 0
        self.start_point = None
        self.end_point = None
        self.cal_ui.graphicsView.mousePressEvent = self.mouse_press_event
    
    def select_body(self):
        self.mouse_press_event_flag = 1
        self.cal_ui.graphicsView.mousePressEvent = self.mouse_press_event

    def select_polygon(self):
        self.mouse_press_event_flag = 2
        self.start_point = None
        self.end_point = None
        self.polygon_points = []
        self.cal_ui.graphicsView.mousePressEvent = self.mouse_press_event
        
    def mouse_press_event(self, event):
        if self.mouse_press_event_flag == 0 or self.mouse_press_event_flag == 1:
            if event.button() == Qt.LeftButton:
                self.start_point = self.cal_ui.graphicsView.mapToScene(event.pos())
            elif event.button() == Qt.RightButton:
                self.end_point = self.cal_ui.graphicsView.mapToScene(event.pos())
                rect = QRectF(self.start_point, self.end_point)
                rect_item = self.cal_ui.graphicsView.scene().addRect(rect, QPen(Qt.red, 3))
                self.cal_ui.graphicsView.scene().addItem(rect_item)
                if self.mouse_press_event_flag == 0:
                    self.rectangle_selection(0)
                else:
                    self.rectangle_selection(1)
                    # self.process_body_selection(roi)

        elif self.mouse_press_event_flag == 2:
            if event.button() == Qt.LeftButton:
                self.polygon_points.append(self.cal_ui.graphicsView.mapToScene(event.pos()))
                print(self.polygon_points)
                if len(self.polygon_points) > 1:
                    line_item = self.cal_ui.graphicsView.scene().addLine(self.polygon_points[-2].x(), self.polygon_points[-2].y(), self.polygon_points[-1].x(), self.polygon_points[-1].y(), QPen(Qt.red, 3))
                    self.cal_ui.graphicsView.scene().addItem(line_item)
                    ellipse_item = self.cal_ui.graphicsView.scene().addEllipse(self.polygon_points[-1].x(), self.polygon_points[-1].y(), 3, 3, QPen(Qt.red, 3))
                    self.cal_ui.graphicsView.scene().addItem(ellipse_item)

            elif event.button() == Qt.RightButton:
                self.polygon_points.append(self.cal_ui.graphicsView.mapToScene(event.pos()))

                line_item = self.cal_ui.graphicsView.scene().addLine(self.polygon_points[-1].x(), self.polygon_points[-1].y(), self.polygon_points[0].x(), self.polygon_points[0].y(), QPen(Qt.red, 3))
                self.cal_ui.graphicsView.scene().addItem(line_item)
                ellipse_item = self.cal_ui.graphicsView.scene().addEllipse(self.polygon_points[-1].x(), self.polygon_points[-1].y(), 3, 3, QPen(Qt.red, 3))
                self.cal_ui.graphicsView.scene().addItem(ellipse_item)

                polygon = QPolygonF(self.polygon_points)
                painter_path = QPainterPath()
                painter_path.addPolygon(polygon)
                region = painter_path.boundingRect().toRect()
                img = cv2.imread(self.png_path)
                if img is None:
                    QMessageBox.critical(self, "Error", f"Failed to load image: {self.png_path}")
                    return
                x, y, w, h = region.x(), region.y(), region.width(), region.height()
                roi = img[y:y+h, x:x+w]
                mask = np.zeros((h, w), dtype=np.uint8)
                points = [(self.cal_ui.graphicsView.mapFromScene(p).x() - x, self.cal_ui.graphicsView.mapFromScene(p).y() - y) for p in self.polygon_points]
                cv2.fillPoly(mask, [np.array(points, dtype=np.int32)], 255)
                roi = cv2.bitwise_and(roi, roi, mask=mask)
                self.process_polygon_selection(roi)

    def rectangle_selection(self, flag):
        self.cal_ui.graphicsView.scene().mousePressEvent = None
        x1, y1 = self.start_point.x(), self.start_point.y()
        x2, y2 = self.end_point.x(), self.end_point.y()
        
        rect = (int(min(x1, x2)), int(min(y1, y2)), int(abs(x1 - x2)), int(abs(y1 - y2)))
        img = cv2.imread(self.png_path)
        if img is None:
            QMessageBox.critical(self, "错误", f"重新加载图片: {self.png_path}")
            return
        roi = img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]
        
        if roi.size == 0:
            QMessageBox.critical(self, "错误", "重新选择")
            return
        else:
            if flag == 0:
                output_path = "selected_roi.png"
                cv2.imwrite(output_path, roi)
                print(f"ROI saved at: {output_path}")
                self.analyze_colorbar(roi)
            else:
                self.process_body_selection(roi)

    def analyze_colorbar(self, roi):
        self.select_num(roi)
        self.select_colorbar_rectangle(roi)
    
    def select_num(self, roi):
        pytesseract.pytesseract.tesseract_cmd = r'.\OCR\tesseract.exe'
        # 读取图像
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(roi, 150, 255, cv2.THRESH_BINARY)
        
        # 配置 tesseract 参数，仅识别数字和小数点
        custom_config = r'--psm 6 digits'  # psm 6 表示按块识别

        # 使用 tesseract 按行提取文字
        data = pytesseract.image_to_data(thresh, config=custom_config, output_type=pytesseract.Output.DICT)

        extracted_numbers = []
        current_line = -1
        line_text = ""

        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text:
                if data['line_num'][i] != current_line:
                    if line_text:
                        extracted_numbers.append(line_text)  
                    current_line = data['line_num'][i]
                    line_text = text
                else:
                    line_text += f" {text}"

        if line_text:
            extracted_numbers.append(line_text)

        self.processed_numbers = []
        for line in extracted_numbers:
            numbers = [float(num) if '.' in num else int(num) for num in line.split() if num.replace('.', '', 1).isdigit()]
            self.processed_numbers.extend(numbers)
        print(f"提取到的数字: {self.processed_numbers}")
        QMessageBox.information(self, "提示", f"提取到的数字: {self.processed_numbers}")

    def select_colorbar_rectangle(self, roi):

        gray = cv2.cvtColor(roi.copy(), cv2.COLOR_BGR2GRAY)

        # Step 2: 图像预处理（边缘检测）
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)  # 高斯模糊，去噪
        edges = cv2.Canny(blurred, 50, 150)  # 边缘检测

        # Step 3: 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Step 4: 找到最大矩形轮廓
        max_contour = None
        max_area = 0
        for contour in contours:
            # 获取轮廓的外接矩形
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            # 排除过小的轮廓，保留最大区域
            if area > max_area:
                max_area = area
                max_contour = (x, y, w, h)

        if max_contour is None:
            QMessageBox.warning(self, "警告", "未找到矩形轮廓，请重新选取")
            return None

        # Step 5: 截取感兴趣区域（ROI）
        x, y, w, h = max_contour
        new_roi = roi[y:y+h, x:x+w]
        self.select_color(new_roi)
        # 保存结果
        output_path = "colorbar_extracted.png"
        cv2.imwrite(output_path, roi)
        print(f"ROI 保存至: {output_path}")

      
    def select_color(self, new_roi):
        self.color_mapping = {}
        height, width, _ = new_roi.shape
        interval = (max(self.processed_numbers) - min(self.processed_numbers)) / (height)
        for i in range(height):
            color = new_roi[i, new_roi.shape[1] // 2]  # 获取中间位置的颜色
            self.color_mapping[max(self.processed_numbers) - i*interval] = color.tolist()  # 将颜色转换为列表并存储
        #print(self.color_mapping)
        
    def show_min_max_dialog(self, roi, flag):
        dialog = QMainWindow(self)
        dialog.setWindowTitle("输入数值范围")
        dialog.setGeometry(100, 100, 300, 150)

        min_label = QLabel("最小数值", dialog)
        min_label.move(20, 20)
        min_label.setStyleSheet("font-size: 12px;")
        min_line_edit = QLineEdit(dialog)
        min_line_edit.move(100, 20)
        min_line_edit.setStyleSheet("font-size: 12px;")

        max_label = QLabel("最大数值", dialog)
        max_label.move(20, 60)
        max_label.setStyleSheet("font-size: 12px;")
        max_line_edit = QLineEdit(dialog)
        max_line_edit.move(100, 60)
        max_line_edit.setStyleSheet("font-size: 12px;")

        def on_ok_clicked():
            self.cal_area_min_value = min_line_edit.text()
            self.cal_area_max_value = max_line_edit.text()
            dialog.close()
            self.multi_cal(roi, flag)

        ok_button = QPushButton("确定", dialog)
        ok_button.move(100, 100)
        ok_button.setStyleSheet("font-size: 12px;")
        ok_button.clicked.connect(on_ok_clicked)

        dialog.show()
    
        dialog.show()
      
    
    def process_body_selection(self, roi):  
        temp_box = QMessageBox.information(self, "提示", "是否需要绘制多边形区域", QMessageBox.Yes | QMessageBox.No)
        if temp_box == QMessageBox.No:
            self.show_min_max_dialog(roi, 0)
        else:
            self.select_polygon()
      
    def process_polygon_selection(self, roi):
        self.cal_ui.scene.mousePressEvent = None
        self.show_min_max_dialog()
        # self.color_mapping中的颜色与数值的映射
        # self.cal_area_min_value, self.cal_area_max_value为用户输入的最小最大值
        # 要提取self.cal_area_min_value到self.cal_area_max_value之间的区域
        # 用于计算波及区域
        self.multi_cal(roi)   

    def multi_cal(self, roi, flag):
        min_value = float(self.cal_area_min_value)
        max_value = float(self.cal_area_max_value)
  
        mask = np.zeros(roi.shape[:2], dtype=np.uint8)
        for value, color in self.color_mapping.items():
            if min_value <= value <= max_value:
                print(f"Extracting area for value: {value}")
                color = np.array(color)
                lower_bound = np.array(color) - 20
                upper_bound = np.array(color) + 20
                mask[np.all((roi >= lower_bound) & (roi <= upper_bound), axis=-1)] = 255

        # Calculate the ratio of the mask area to the ROI area
        mask_area = cv2.countNonZero(mask)
        # Save the mask area as an image
        mask_image_path = "mask_area.png"
        cv2.imwrite(mask_image_path, mask)
        print(f"Mask area image saved at: {mask_image_path}")
        roi_area = roi.shape[0] * roi.shape[1]

        if flag == 0:
            area_ratio = mask_area / roi_area
        elif flag == 1:
            area_ratio = mask_area / self.square_rectangle
        
        QMessageBox.information(self, "提示", f"波及区域面积比例: {area_ratio:.2f}")
        print(f"Mask area: {mask_area}, ROI area: {roi_area}, Area ratio: {area_ratio:.2f}")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = CalMain()
    mainWindow.show()
    sys.exit(app.exec_())