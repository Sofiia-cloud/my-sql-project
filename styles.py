# styles.py
from PySide6.QtWidgets import QPushButton, QGroupBox, QTableView
from PySide6.QtGui import QColor
from config import STYLES

def create_styled_button(text, color=STYLES["accent_color"], font_size=10):
    """Создает стилизованную кнопку"""
    button = QPushButton(text)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            font-size: {font_size}px;
        }}
        QPushButton:hover {{
            background-color: {QColor(color).darker(120).name()};
        }}
        QPushButton:pressed {{
            background-color: {QColor(color).darker(150).name()};
        }}
        QPushButton:disabled {{
            background-color: #95a5a6;
            color: #7f8c8d;
        }}
    """)
    return button

def create_group_box(title):
    """Создает стилизованную группу"""
    group = QGroupBox(title)
    group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #2c3e50;
        }
    """)
    return group

def create_table():
    """Создает стилизованную таблицу"""
    table = QTableView()
    table.setStyleSheet("""
        QTableView {
            gridline-color: #bdc3c7;
            background-color: white;
            alternate-background-color: #f8f9fa;
        }
        QTableView::item:selected {
            background-color: #3498db;
            color: white;
        }
        QHeaderView::section {
            background-color: #34495e;
            color: white;
            padding: 4px;
            border: 1px solid #2c3e50;
            font-weight: bold;
        }
    """)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableView.SelectRows)
    table.setSortingEnabled(True)
    return table

def get_app_stylesheet():
    """Возвращает CSS для всего приложения"""
    return """
        QMainWindow, QWidget {
            background-color: #ecf0f1;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QLabel {
            color: #2c3e50;
            font-size: 11px;
        }
        
        QLineEdit, QTextEdit, QSpinBox, QComboBox {
            padding: 6px;
            border: 2px solid #bdc3c7;
            border-radius: 4px;
            background-color: white;
            font-size: 11px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
            border-color: #3498db;
        }
        
        QTabWidget::pane {
            border: 1px solid #bdc3c7;
            background-color: white;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #95a5a6;
            color: white;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #3498db;
            font-weight: bold;
        }
        
        QTabBar::tab:hover {
            background-color: #7f8c8d;
        }
    """