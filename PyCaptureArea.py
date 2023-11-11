import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QStackedLayout, QToolBar, QSizePolicy, QPushButton, QVBoxLayout, QVBoxLayout, QColorDialog, QLineEdit
from PyQt6.QtCore import Qt, QPoint, QSize, QEvent
from PyQt6.QtGui import QMouseEvent, QColor, QPixmap, QScreen, QGuiApplication, QCursor, QHoverEvent, QIcon, QAction
import pyautogui
from PIL import Image
import pytesseract
import cv2
import pyperclip

# PyQT6

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set the window type to remove the title bar
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMouseTracking(True)
        
        # Set the window flags to allow moving and resizing
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set the window size and position
        self.setGeometry(100, 100, 500, 300)
        
        # Set the window background color to transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")
        
        # Create a main widget to hold the stacked layout
        self.main_widget = QWidget(self)
        
        # Create a stacked layout to hold the two containers
        self.stacked_layout = QStackedLayout(self.main_widget)
        
        # Create the first container
        self.container1 = QWidget()
        self.selected_color = QColor('#ffffff')
        self.updateBorderColor(self.selected_color)
        
        # Add the containers to the stacked layout
        self.stacked_layout.addWidget(self.container1)
        
        # Set the main widget as the central widget of the main window
        # self.setCentralWidget(self.main_widget)
        
            # Create a toolbar to hold the buttons
        toolbar = QToolBar(self)
        self.addToolBar(toolbar)

        # Add a separator to push the buttons to the right
        toolbar.addSeparator()

        # Add a stretchable spacer item to push the buttons to the right edge
        spacer = QWidget(self)
        # spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # Create the "Close" button, connect it to the close function
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("QPushButton { font-size: 16px; color: black; background: rgba(255, 255, 255, 0.9); padding: 6px; border-radius:5px; }")
        toolbar.addWidget(close_button)

        # Create the "Copy" button, connect it to the copy function
        copy_button = QPushButton("Copy Text", self)
        copy_button.clicked.connect(self.copy_text)
        copy_button.setStyleSheet("QPushButton { font-size: 16px; color: black; background: rgba(255, 255, 255, 0.9); padding: 6px; border-radius:5px; }")
        toolbar.addWidget(copy_button)
        
        # Create the "Resize" button, connect it to the close function
        resize_button = QPushButton("Save Image", self)
        resize_button.clicked.connect(self.save_image_button)
        resize_button.setStyleSheet("QPushButton { font-size: 16px; color: black; background: rgba(255, 255, 255, 0.9); padding: 6px; border-radius:5px; }")
        toolbar.addWidget(resize_button)
        
        # Text box for saving the image as a file name
        self.save_filename = "Screenshot.png"
        text_box = QLineEdit(self)
        text_box.setText(self.save_filename)
        text_box.setStyleSheet("QLineEdit { font-size: 16px; background-color: white; color: black; padding: 6px; border-radius:5px; }")
        text_box.setFixedWidth(120)
        text_box.textChanged.connect(self.on_text_changed)
        toolbar.addWidget(text_box)
        
        # Add color picker
        color_picker_action = QAction(QIcon('images/color-wheel.png'), 'Color Picker', self)
        color_picker_action.triggered.connect(self.open_color_picker)
        toolbar.addAction(color_picker_action)
        
        # Set the toolbar style
        toolbar.setStyleSheet("QToolBar { spacing: 10px; width: 100%; background-color: rgba(255, 255, 255, 0.0); }")
        
        # Create a layout to hold the image and the toolbar
        layout = QVBoxLayout()
        layout.addWidget(self.main_widget)
        layout.addWidget(toolbar)

        # Create a widget to hold the layout
        widget = QWidget(self)
        widget.setLayout(layout)

        # Set the widget as the central widget
        self.setCentralWidget(widget)
        
        # Initialize variables for tracking mouse movements
        self.is_mouse_pressed = False
        self.mouse_press_position = QPoint()
        
        self.installEventFilter(self)
        self.resizing = False
        
        self.show()
        
    def on_text_changed(self, text):
        # print(f"Text changed: {text}")
        self.save_filename = text
        
    def open_color_picker(self):
        # print("Open Color Picker")
        # Create a QColorDialog with the initial color and options
        color_dialog = QColorDialog()

        # Set the options
        color_dialog.setOption(QColorDialog.ColorDialogOption.NoButtons)
        color_dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog)
        color_dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel)

        
        # Open the color picker dialog
        color = color_dialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            print("Selected Color: "+self.selected_color)
            self.updateBorderColor(color)
            
    def updateBorderColor(self, color: QColor):
        self.container1.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.0); border: 15px solid rgba({color.red()}, {color.green()}, {color.blue()}, 0.5);")
        
    def eventFilter(self, source, event):
        pos = None
        if isinstance(event, QMouseEvent):
            pos = event.pos()
        if isinstance(event, QHoverEvent):
            pos = event.oldPos()
        # print(event.type(), event, pos)

        if event.type() == QEvent.Type.HoverMove and pos and not self.resizing:
            self.resize_type = self.on_border(pos)
            if self.resize_type:
                if self.resize_type in ['TL_Diagonal', 'BR_Diagonal']:
                    self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
                elif self.resize_type in ['TR_Diagonal', 'BL_Diagonal']:
                    self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
                elif self.resize_type in ['Left', 'Right']:
                    self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
                elif self.resize_type in ['Top', 'Bottom']:
                    self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                
        elif event.type() == QEvent.Type.MouseButtonPress and pos:
            if self.on_border(pos):
                self.resizing = True
        elif event.type() == QEvent.Type.MouseButtonRelease and pos:
            self.resizing = False
        elif event.type() == QEvent.Type.MouseMove and pos:
            if self.resizing:
                qsize = super().size() # Size of Window
                windowSizeX, windowSizeY = qsize.width(), qsize.height()
                
                coords = self.pos() # Position of the window
                windowX, windowY = coords.x(), coords.y()
                
                cursorYOffset = 10
                cursorXOffset = 12
                bottomOffset = 55 # 12 + 43 (offset + button height)
                
                if self.resize_type == 'TR_Diagonal':
                    resizeX = pos.x()+cursorXOffset
                    resizeY = -pos.y() + windowSizeY + cursorYOffset
                    moveY = windowY+pos.y()-cursorYOffset
                    self.move_resize(None, moveY, resizeX, resizeY)
                elif self.resize_type == 'BR_Diagonal':
                    resizeX = pos.x()+cursorXOffset
                    resizeY = pos.y()+bottomOffset
                    self.move_resize(None, None, resizeX, resizeY)
                elif self.resize_type == 'BL_Diagonal':
                    resizeX = -pos.x() + windowSizeX + cursorXOffset
                    resizeY = pos.y()+bottomOffset
                    moveX = windowX+pos.x()-cursorXOffset
                    self.move_resize(moveX, None, resizeX, resizeY)
                elif self.resize_type == 'TL_Diagonal':
                    resizeX = -pos.x() + windowSizeX + cursorXOffset
                    resizeY = -pos.y() + windowSizeY + cursorYOffset
                    moveX = windowX+pos.x()-cursorXOffset
                    moveY = windowY+pos.y()-cursorYOffset
                    self.move_resize(moveX, moveY, resizeX, resizeY)
                elif self.resize_type == 'Left':
                    resizeX = -pos.x() + windowSizeX + cursorXOffset
                    moveX = windowX+pos.x()-cursorXOffset
                    self.move_resize(moveX, None, resizeX, windowSizeY)
                elif self.resize_type == 'Right':
                    resizeX = pos.x()+cursorXOffset
                    self.move_resize(None, None, resizeX, windowSizeY)
                elif self.resize_type == 'Top':
                    resizeY = -pos.y() + windowSizeY + cursorYOffset
                    moveY = windowY+pos.y()-cursorYOffset
                    self.move_resize(None, moveY, windowSizeX, resizeY)
                elif self.resize_type == 'Bottom':
                    resizeY = pos.y()+bottomOffset
                    self.move_resize(None, None, windowSizeX, resizeY)
        return super().eventFilter(source, event)

    def move_resize(self, moveX, moveY, resizeX, resizeY):
        coords = self.pos() # Position of the window
        windowX, windowY = coords.x(), coords.y()
        # qsize = super().size() # Size of Window
        # windowSizeX, windowSizeY = qsize.width(), qsize.height()
        
        # Clamp size to min 300x200
        if resizeX < 300:
            resizeX = 300
            moveX = None
        if resizeY < 200:
            resizeY = 200
            moveY = None
        
        if moveX and not moveY:
            self.move(moveX, windowY)
        elif moveY and not moveX:
            self.move(windowX, moveY)
        elif moveX and moveY:
            self.move(moveX, moveY)
        
        # print(f'Resizing Type: {self.resize_type} ({windowSizeX}, {windowSizeY}) to ({resizeX}, {resizeY})')
        super().resize(resizeX, resizeY)
        
    def on_border(self, pos):
        border_type = None
        tolerance = 15
        height = self.height() - 43 # Offset because of buttons
        # print(f'Height: {height} - {pos.y()}')
        if pos.y() > height: # Conditional because of buttons
            return None
        
        if pos.x() < tolerance:
            if pos.y() < tolerance:
                border_type = 'TL_Diagonal'  # Top-Left Diagonal
            elif pos.y() > height - tolerance:
                border_type = 'BL_Diagonal'  # Bottom-Left Diagonal
            else:
                border_type = 'Left'
        elif pos.x() > self.width() - tolerance:
            if pos.y() < tolerance:
                border_type = 'TR_Diagonal'  # Top-Right Diagonal
            elif pos.y() > height - tolerance:
                border_type = 'BR_Diagonal'  # Bottom-Right Diagonal
            else:
                border_type = 'Right'
        elif pos.y() < tolerance:
            border_type = 'Top'
        elif pos.y() > height - tolerance:
            border_type = 'Bottom'
            
        if not border_type:
            return None
        return border_type
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_mouse_pressed = True
            self.mouse_press_position = event.globalPosition().toPoint() - self.pos()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        # self.mousePos = event.globalPosition().toPoint()
        
        # self.mousePos = event.pos()
        # print("Mouse Moved"+ str(self.mousePos))
        
        if self.is_mouse_pressed and not self.resizing:
            self.move(event.globalPosition().toPoint() - self.mouse_press_position)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_mouse_pressed = False
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggleMaximized()
    
    def resizeEvent(self, event):
        # print("resizeEvent")
        super().resizeEvent(event)
        # self.container1.setGeometry(self.rect())
        # self.container1.setGeometry(self.rect())
        # self.container1.setStyleSheet("background-color: rgba(0, 0, 0, 0.0); border: 15px solid rgba(255, 255, 255, 0.5);")
    
    def toggleMaximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def copy_text(self):
        # Implement the copy functionality here
        # print("Copy text button clicked")
        _, screenshot = self.save_image('screenshots', 'temp.png', save_to_disk=False)
        text = pytesseract.image_to_string(screenshot)
        print("Copied Text: "+text)
        pyperclip.copy(text) # Copy to clipboard

    def save_image_button(self):
        # print("Save image button clicked")
        path, _ = self.save_image(file_name=self.save_filename)
        print(f"Screenshot saved as {path}")
        
    def save_image(self, image_dir='screenshots', file_name='screenshot.png', save_to_disk=True) -> str:
        # Get the geometry of the self.main_widget container
        geometry = self.main_widget.frameGeometry()
        pos = self.pos()
        
        # Get the position and size of the application on the screen
        offset = 23
        size_offset = offset + 5
        
        x = pos.x() + offset
        y = pos.y() + offset
        width = geometry.width() - size_offset
        height = geometry.height() - size_offset
        # print("Loc: "+str(x)+", "+str(y)+", "+str(width)+", "+str(height))

        # Capture the screenshot
        screenshot = pyautogui.screenshot(region=(x, y, width, height))

        # Save the screenshot as a PNG file
        path = os.path.join(image_dir, file_name)
        if save_to_disk:
            screenshot.save(path)
        return path, screenshot

    def close(self):
        # Close the application
        QApplication.instance().quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec())
