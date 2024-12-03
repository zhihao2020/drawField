import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QMainWindow, QVBoxLayout, QFileDialog, QLineEdit, QWidget, QPushButton, QComboBox
from PyQt5.QtCore import Qt, QObject
import pyqtgraph as pg
import webbrowser
import sys
from svgpathtools import svg2paths
from ui.modify import Ui_MainWindow

import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.colors import LinearSegmentedColormap

class LoadMain(QMainWindow, Ui_MainWindow, QObject):
    def __init__(self):
        super(LoadMain, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Ensure graphWidget is defined in Ui_MainWindow
        
        # Create a PlotWidget for displaying graphs
        self.graphWidget = pg.PlotWidget(self)
        self.ui.verticalLayout.replaceWidget(self.ui.graphWidget, self.graphWidget)
    

        self.ui.action.triggered.connect(self.about_soft)
        self.ui.action_svg.triggered.connect(self.load_file)
        # 展示场图
        self.graphWidget.scene().sigMouseClicked.connect(self.change)
        # 绘制场图
        self.ui.pushButton_2.clicked.connect(self.darw_field_pre)
        # 导出场图数据
        self.ui.pushButton.clicked.connect(self.save_csv)
        # 计算波及区域
        # self.ui.pushButton_3.clicked.connect(self.analyse_involve)
        # 加载svg文件
        # self.ui.pushButton_4.clicked.connect(self.load_svg_line)

         # 定义颜色映射
        rgb_colors = [
            (255/255, 255/255, 204/255),
            (102/255, 51/255, 51/255),
            (67/255, 16/255, 122/255),
            (18/255, 0/255, 219/255),
            (0/255, 59/255, 255/255),
            (0/255, 157/255, 255/255),
            (0/255, 209/255, 228/255),
            (26/255, 255/255, 0/255),
            (255/255, 253/255, 4/255),
            (255/255, 210/255,90/255),
            (255/255, 136/255, 133/255),
            (255/255, 57/255, 0/255),      
            (255/255, 48/255, 0/255)
        ]
        # 创建自定义颜色映射
        self.custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', rgb_colors)

    def load_svg_line(self):
        self.graphWidget.scene().sigMouseClicked.connect(self.change)
        if self.filename:  
            self.svg2image(filename)
            self.draw_image()

    def get_pos(self, event):
        mouse_point = self.graphWidget.plotItem.vb.mapSceneToView(event.pos())
        x = mouse_point.x()
        y = mouse_point.y()

        self.relative_x = x
        self.relative_y = y
        print(f"Relative position on GraphWidget: ({self.relative_x}, {self.relative_y})")

    def get_path(self, event):
        self.get_pos(event)
        # 读取CSV文件
        df = pd.read_csv(r'1.csv')
        x=  self.relative_x
        y=self.relative_y 
        print("po:", x, y)
        # 找到距离点击位置最近的点
        df['distance'] = np.sqrt((df['X'] - x) ** 2 + (df['Y'] - y) ** 2)
        nearest_point = df.loc[df['distance'].idxmin()]

        # 获取最近点的Path
        self.nearest_path = nearest_point['Path']
        print(f"Clicked on Path: {self.nearest_path}")

        # 显示输入框
        self.num_label()

    def darw_field_pre(self):
        # 创建输入框窗口
        self.input_window = QMainWindow()
        self.input_window.setWindowTitle("输入色标值")

        # 创建一个中央小部件和布局
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.input_window.setCentralWidget(central_widget)

        # 创建两个QLineEdit控件
        self.input_x = QLineEdit(self.input_window)
        self.input_x.setPlaceholderText("色标的最低值")

        layout.addWidget(self.input_x)

        self.input_y = QLineEdit(self.input_window)
        self.input_y.setPlaceholderText("色标的最高值")
 
        layout.addWidget(self.input_y)
        self.input_z_label = QLabel("保留小数位数", self.input_window)
        layout.addWidget(self.input_z_label)
        self.input_z = QComboBox(self.input_window)
        self.input_z.addItems(["0", "1", "2", "3"])
        layout.addWidget(self.input_z)

        # 创建确认按钮
        self.confirm_button = QPushButton("确认", self.input_window)
        layout.addWidget(self.confirm_button)
        self.confirm_button.clicked.connect(self.on_confirm)

        # 显示输入框窗口
        self.input_window.setWindowModality(Qt.ApplicationModal)
        self.input_window.resize(300, 200)  # 调整窗口大小
        self.input_window.show()

    def on_confirm(self):
        if self.input_x.text():
            self.low_colorbar = float(self.input_x.text())
        else:
            self.low_colorbar = 10

        if self.input_y.text():
            self.high_colorbar = float(self.input_y.text())
        else:
            self.high_colorbar = 60
        self.z = int(self.input_z.currentText())
        self.input_window.close()
        self.darw_field()

    def analyse_involve(self):
        # 增加按钮 可以计算波及面积
        self.graphWidget.scene().sigMouseClicked.connect(self.change)

        df = pd.read_csv(r'temp.csv')
        # 提取X, Y, Z数据
        X = df['X'].values
        Y = df['Y'].values
        Z = df['Z'].values

        # 将X, Y, Z数据转换为网格数据
        xi = np.linspace(min(X), max(X), 400)
        yi = np.linspace(min(Y), max(Y), 400)
        X_grid, Y_grid = np.meshgrid(xi, yi)
        Z_grid = griddata((X, Y), Z, (X_grid, Y_grid), method='nearest')

        # 清除之前的图形
        self.graphWidget.clear()

        # 创建一个FigureCanvasQTAgg对象
        self.canvas = FigureCanvasQTAgg(plt.Figure())
        ax = self.canvas.figure.subplots()

        # 设置等值线层次 
        levels = np.linspace(self.low_colorbar, self.high_colorbar, 100)  # 在10到60之间创建100个等值线层次

        
        # 绘制等值线图
        contour = ax.contourf(X_grid, Y_grid, Z_grid, levels=levels, cmap=self.custom_cmap)

        cbar = self.canvas.figure.colorbar(contour, ticks=np.linspace(self.low_colorbar, self.high_colorbar, num=11), format='%.0f')  

        # 绘制等值线图
        levels = np.linspace(self.low_colorbar, self.high_colorbar, 100)
        contour = pg.ImageItem(image=Z_grid.T, levels=(self.low_colorbar, self.high_colorbar))
        contour.setLookupTable(pg.colormap.getFromMatplotlib('viridis').getLookupTable())
        self.graphWidget.addItem(contour)

        # 添加颜色条  
        cbar.setImageItem(contour, insert_in=self.graphWidget.plotItem)
    
    def darw_field(self):  
        # 读取CSV文件
        df = pd.read_csv(r'1.csv')
        
        # 提取X, Y, Z数据
        X = df['X'].values
        Y = df['Y'].values
        Z = df['Z'].values

        # 将X, Y, Z数据转换为网格数据
        xi = np.linspace(min(X), max(X), 400)
        yi = np.linspace(min(Y), max(Y), 400)
        X_grid, Y_grid = np.meshgrid(xi, yi)
        Z_grid = griddata((X, Y), Z, (X_grid, Y_grid), method='nearest')

        grid_data = {
            'Path': [],
            'X': [],
            'Y': [],
            'Z': []
        }

        for i in range(len(xi)):
            for j in range(len(yi)):
                grid_data['Path'].append(0)
                grid_data['X'].append(X_grid[i, j])
                grid_data['Y'].append(Y_grid[i, j])
                grid_data['Z'].append(Z_grid[i, j])
        grid_df = pd.DataFrame(grid_data)
        grid_df.to_csv(r'temp.csv', index=False)

        # 创建一个新的窗口
        self.field_window = QMainWindow()
        self.field_window.setWindowTitle("场图")

        # 创建一个中央小部件和布局
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.field_window.setCentralWidget(central_widget)

        # 创建一个FigureCanvasQTAgg对象
        self.canvas = FigureCanvasQTAgg(plt.Figure())
        layout.addWidget(self.canvas)

        # 获取Figure对象并绘制图形
        ax = self.canvas.figure.subplots()

        # 设置等值线层次 
        levels = np.linspace(self.low_colorbar, self.high_colorbar, 100)  # 在10到60之间创建100个等值线层次

        
        # 绘制等值线图
        contour = ax.contourf(X_grid, Y_grid, Z_grid, levels=levels, cmap=self.custom_cmap)
        if self.z == 0:
            format = '%.0f'
        elif self.z == 1:
            format = '%.1f'
        elif self.z == 2:
            format ='%.2f'
        elif self.z == 3:
            format ='%.3f'

        cbar = self.canvas.figure.colorbar(contour, ticks=np.linspace(self.low_colorbar, self.high_colorbar, num=11), format=format)  

        # 设置x轴和y轴标签的字体大小
        ax.tick_params(axis='x', labelsize=12)
        ax.tick_params(axis='y', labelsize=12)

        # 显示窗口
        self.field_window.setWindowModality(Qt.ApplicationModal)
        self.field_window.show()

        # 创建保存按钮
        self.save_button = QPushButton("保存图片", self.field_window)
        layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_image)
        self.save_csv_button = QPushButton("保存CSV", self.field_window)
        layout.addWidget(self.save_csv_button)
        self.save_csv_button.clicked.connect(self.save_csv)

    def save_csv(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "保存CSV文件", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_path:
            # 读取CSV文件
            df = pd.read_csv(r'1.csv')
            # 提取X, Y, Z数据
            X = df['X'].values
            Y = df['Y'].values
            Z = df['Z'].values

            # 将X, Y, Z数据转换为网格数据
            xi = np.linspace(min(X), max(X), 400)
            yi = np.linspace(min(Y), max(Y), 400)
            X_grid, Y_grid = np.meshgrid(xi, yi)
            Z_grid = griddata((X, Y), Z, (X_grid, Y_grid), method='nearest')

            # 创建新的DataFrame存储网格数据
            grid_data = {
            'X': [],
            'Y': [],
            'Z': []
            }

            for i in range(len(xi)):
                for j in range(len(yi)):
                    grid_data['X'].append(X_grid[i, j])
                    grid_data['Y'].append(Y_grid[i, j])
                    grid_data['Z'].append(Z_grid[i, j])

            grid_df = pd.DataFrame(grid_data)
            grid_df.to_csv(file_path, index=False)
            QMessageBox.information(self, "保存CSV", f"CSV文件已保存到 {file_path}")

    def save_image(self):
        options = QFileDialog.Options()
        
        file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            # 保存当前绘制的图像
            self.canvas.figure.savefig(file_path, dpi=800)
            QMessageBox.information(self, "保存图片", f"图片已保存到 {file_path}")

    def num_label(self):
        # 创建一个QLineEdit控件
        self.input_box = QLineEdit(self.graphWidget)
        self.input_box.setGeometry(self.graphWidget.plotItem.vb.mapViewToScene(pg.Point(self.relative_x, self.relative_y)).toPoint().x(), 
                                    self.graphWidget.plotItem.vb.mapViewToScene(pg.Point(self.relative_x, self.relative_y)).toPoint().y(), 
                                    50, 30)  # 设置位置和大小
        self.input_box.setAlignment(Qt.AlignCenter)  # 设置文本居中
        self.input_box.setPlaceholderText("输入数字")  # 设置占位符文本
        self.input_box.setFocus()  # 设置焦点到输入框
        self.input_box.show()  # 显示输入框

        # 初始化input_boxes容器
        if not hasattr(self, 'input_boxes'):
            self.input_boxes = []

        # 将新创建的input_box添加到容器中
        self.input_boxes.append(self.input_box)

        # 连接输入框的回车键按下信号到修改函数
        self.input_box.returnPressed.connect(self.modify_path_z)

    def modify_path_z(self):
        # 获取输入的数字
        new_z_value = self.input_box.text()

        # 读取CSV文件
        df = pd.read_csv(r'1.csv')
        reply = QMessageBox.question(self, '确认修改', f'是否将Path {self.nearest_path} 修改为 {new_z_value}', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 修改对应Path的Z列
            df.loc[df['Path'] == self.nearest_path, 'Z'] = new_z_value

            # 保存回CSV文件
            df.to_csv(r'1.csv', index=False)
            print(f"Path {self.nearest_path} 的Z列已修改为 {new_z_value}")
            self.draw_image()  # 重新绘制图像
        else:
            print('已取消修改')
            return

        # 隐藏并删除所有输入框
        for input_box in self.input_boxes:
            input_box.hide()
            input_box.deleteLater()
        self.input_boxes = []
        
    def change(self, event):
        self.get_path(event)

    def end(self):
        self.label.mousePressEvent = None

    def up(self):
        # 重新加载csv文件，展示图片
        self.load_file()         

    def about_soft(self):
        webbrowser.open_new_tab('https://www.x-mol.com/groups/lyw557')

    def load_file(self):
        self.filename, _ = QFileDialog.getOpenFileName(self, "加载SVG文件", "", "加载SVG(*.svg)") 
        
    
    def draw_image(self):
        # 清除之前的图形
        self.graphWidget.clear()
        df = pd.read_csv(r"1.csv")
        # 根据Path列的不同，使用X Y绘制折线图
        for path_id in df['Path'].unique():
            print(path_id)
            path_data = df[df['Path'] == path_id].reset_index(drop=True)
            self.graphWidget.plot(path_data['X'], path_data['Y'], pen=pg.mkPen(width=2),
                 name=f'Path {path_id}: {df[df["Path"] == path_id]["Z"].values[0]}')
            # 在折线上添加标签
            mid_index = len(path_data) // 2
            mid_point = path_data.iloc[mid_index]
            text = pg.TextItem(text=f'{path_id}: {df[df["Path"] == path_id]["Z"].values[0]}', anchor=(0.5, 0.5))
            text.setPos(mid_point['X'], mid_point['Y'])
            self.graphWidget.addItem(text)

        # 设置标题和标签
        self.graphWidget.setLabel('left', 'Y')
        self.graphWidget.setLabel('bottom', 'X')

    def load_file(self):
        self.filename, _ = QFileDialog.getOpenFileName(self, "加载SVG文件", "", "加载SVG(*.svg)")
        if self.filename:
            self.svg2image(self.filename)
            self.draw_image()


    def svg2image(self, filename):
        # 读取SVG文件
        paths, attributes = svg2paths(filename)

        # 准备数据存储
        data = []

        # 遍历每一条路径
        for i, path in enumerate(paths):
            # 遍历路径上的每一段
            for segment in path:
                points = np.linspace(0, 1, 300)  # 100表示每条线段取样100个点
                for t in points:
                    point = segment.point(t)
                    data.append([i+1, point.real, -point.imag, 0])  
        # 创建DataFrame
        df = pd.DataFrame(data, columns=['Path', 'X', 'Y', 'Z'])
        # 缩放X和Y的值
        df['X'] = (df['X'] - df['X'].min()) / (df['X'].max() - df['X'].min()) * 300
        df['Y'] = (df['Y'] - df['Y'].min()) / (df['Y'].max() - df['Y'].min()) * 300

        # 存储到CSV文件
        df.to_csv(r'1.csv', index=False)
        print("坐标数据已保存到 1.csv 文件中。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_win = LoadMain()
    
    my_win.show()
    sys.exit(app.exec_())
    