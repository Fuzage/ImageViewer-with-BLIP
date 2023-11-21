import sys
import os
from PyQt5.QtCore import Qt, QRectF, QDir, QSettings
from PyQt5.QtGui import QPixmap, QPainter, QFont
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QWidget, QTreeView, QFileSystemModel, QSplitter, QSizePolicy,
    QLabel, QHBoxLayout, QTextEdit
)
import winreg
from PIL import Image
from datetime import datetime


class ImageViewer(QGraphicsView):
    def __init__(self):
        super(ImageViewer, self).__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # 加载图片
        self.image_item = QGraphicsPixmapItem()
        self.scene.addItem(self.image_item)

        # 启用滚轮缩放
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.HighQualityAntialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)


    def load_image(self, file_path):
        pixmap = QPixmap(file_path)
        self.image_item.setPixmap(pixmap)

        # 获取图片尺寸
        image_width = pixmap.width()
        image_height = pixmap.height()

        # 获取当前视图的尺寸
        view_width = self.viewport().width()
        view_height = self.viewport().height()

        # 计算缩放因子，使图片能完整显示在视图内
        scale_factor = min(view_width / image_width, view_height / image_height)

        # 设置缩放
        self.resetTransform()
        self.scale(scale_factor, scale_factor)

        # 将图片居中显示
        self.centerOn(image_width / 2, image_height / 2)

        # 更新场景矩形区域
        rectf = QRectF(self.image_item.pixmap().rect())
        self.setSceneRect(rectf)

    def wheelEvent(self, event):
        factor = 1.2  # 缩放因子
        if event.angleDelta().y() < 0:
            factor = 1.0 / factor
        self.scale(factor, factor)


class ImageDetails(QWidget):
    def __init__(self):
        super(ImageDetails, self).__init__()

        # 创建一个文本编辑框用于显示详细信息
        self.details_text_edit = QTextEdit()
        self.details_text_edit.setReadOnly(True)

        # 设置较大的字体
        font = QFont()
        font.setPointSize(14)  # Set the desired font size
        self.details_text_edit.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self.details_text_edit)

        self.setLayout(layout)

    def set_image_details(self, file_path):
        # 获取文件路径
        details_text = f"图片路径: {file_path}"

        # 获取额外的图片信息
        image_details = self.get_image_additional_details(file_path)

        # 显示额外的图片信息
        if image_details:
            details_text += f"\n{image_details}"

        self.details_text_edit.setPlainText(details_text)

    def get_image_additional_details(self, file_path):
        try:
            # 使用Pillow库打开图片
            image = Image.open(file_path)

            # 获取图片的详细信息
            width, height = image.size
            mode = image.mode

            # 使用os模块获取文件信息
            file_info = os.stat(file_path)
            creation_time = datetime.fromtimestamp(file_info.st_ctime).strftime('%Y-%m-%d')  # 创建时间
            modification_time = datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d')  # 修改时间
            file_size = file_info.st_size / (1024 * 1024)  # 存储大小，转换为MB

            # 返回完整的图片信息字符串
            return f"详细信息:\n   宽：{width}, 高：{height}\n   模式：{mode}\n" \
                   f"   创建日期：{creation_time}\n   修改日期：{modification_time}\n   图片大小：{file_size:.2f} MB"
        except Exception as e:
            return f"Error reading image details: {str(e)}"


class FileExplorer(QWidget):
    def __init__(self, viewer, details_widget):
        super(FileExplorer, self).__init__()

        self.viewer = viewer
        self.details_widget = details_widget

        # 获取程序所在目录
        current_path = os.path.dirname(os.path.realpath(__file__))

        # 创建文件系统模型
        model = QFileSystemModel()
        model.setRootPath(current_path)

        # 设置只显示ImageDatabase文件夹中的内容
        model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)
        model.setNameFilters(['*.jpg', '*.png', '*.jpeg', '*.gif'])  # 这里添加需要显示的图片格式
        model.setNameFilterDisables(False)

        # 设置根路径
        model.setRootPath(current_path + '/ImageDatabase')

        # 创建目录选择器
        self.tree_view = QTreeView()
        self.tree_view.setModel(model)
        self.tree_view.setRootIndex(model.index(current_path + '/ImageDatabase'))

        # 连接项的点击事件到槽函数
        self.tree_view.clicked.connect(self.item_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.tree_view)

        self.setLayout(layout)

    def item_clicked(self, index):
        # 获取选中项的路径
        file_path = self.sender().model().filePath(index)

        # 加载图片到视图
        self.viewer.load_image(file_path)

        # 设置图片详细信息（示例：文件路径）
        self.details_widget.set_image_details(file_path)


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.viewer = ImageViewer()
        self.image_details = ImageDetails()
        self.explorer = FileExplorer(self.viewer, self.image_details)

        # 创建一个垂直分隔窗口
        self.splitter_main = QSplitter(Qt.Vertical)
        self.splitter_main.addWidget(self.viewer)
        self.splitter_main.addWidget(self.image_details)

        # 创建一个水平分隔窗口
        self.splitter_left = QSplitter(Qt.Horizontal)
        self.splitter_left.addWidget(self.explorer)
        self.splitter_left.addWidget(self.splitter_main)

        # 设置StretchFactor，使左右两个框体的尺寸可调节
        self.splitter_left.setStretchFactor(0, 1)
        self.splitter_left.setStretchFactor(1, 2)

        # 设置Splitter的SizePolicy，使其在水平方向上占满窗体
        self.splitter_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 将布局设置到主窗口
        layout = QHBoxLayout(self)
        layout.addWidget(self.splitter_left)

        self.setWindowTitle("ImageViewer with BLIP")

        # 在初始化时检查是否是第一次启动
        if not self.is_first_run():
            # 如果不是第一次启动，则加载窗口尺寸和分隔器位置
            self.load_settings()
        else:
            # 如果是第一次启动，则设置默认的窗口尺寸和分隔器位置
            self.setGeometry(100, 100, 1000, 800)
            self.center_on_screen()
            # Set initial splitter states
            self.splitter_main.setSizes([int(self.height() * 3 / 4), int(self.height() * 1 / 4)])
            self.splitter_left.setSizes([int(self.width() * 1 / 3), int(self.width() * 3 / 4)])


    def center_on_screen(self):
        # 将窗口居中显示在屏幕上
        screen_geometry = QApplication.desktop().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        # 保存窗口尺寸和分隔器位置
        self.save_settings()
        event.accept()

    def load_settings(self):
        # 从设置中读取窗口尺寸和分隔器位置
        settings = QSettings("Shoukaku03s", "ImageViewer with BLIP")
        self.restoreGeometry(settings.value("geometry", self.saveGeometry()))
        self.splitter_main.restoreState(settings.value("splitter_main_state", self.splitter_main.saveState()))
        self.splitter_left.restoreState(settings.value("splitter_left_state", self.splitter_left.saveState()))

    def save_settings(self):
        # 将窗口尺寸和分隔器位置保存到设置中
        settings = QSettings("Shoukaku03s", "ImageViewer with BLIP")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("splitter_main_state", self.splitter_main.saveState())
        settings.setValue("splitter_left_state", self.splitter_left.saveState())

    def is_first_run(self):
        # 检查是否是第一次运行，通过检查注册表项是否存在
        key_path = r"Software\Shoukaku03s\ImageViewer with BLIP"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path):
                return False
        except FileNotFoundError:
            return True

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())
