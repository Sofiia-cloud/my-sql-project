# main.py
import sys
import faulthandler
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from config import setup_logging
from widgets import SetupTab, AIModelsTab, AttacksTab
from styles import get_app_stylesheet

faulthandler.enable()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔒 MLOps система для обнаружения DDoS-атак")
        self.resize(1400, 900)
        self.setStyleSheet(get_app_stylesheet())
        
        self.conn = None
        self.tabs = QTabWidget()
        
        self.setup_tab = SetupTab()
        self.tabs.addTab(self.setup_tab, "🔗 Подключение")
        
        self.ai_models_tab = None
        self.attacks_tab = None

        self.setCentralWidget(self.tabs)

    def on_connection_established(self, conn):
        """Вызывается при успешном подключении к БД"""
        self.conn = conn
        self.setup_tabs()

    def on_connection_closed(self):
        """Вызывается при отключении от БД"""
        self.conn = None
        self.close_tabs()

    def setup_tabs(self):
        """Создает вкладки для работы с данными"""
        if self.conn:
            self.ai_models_tab = AIModelsTab(self.conn)
            self.tabs.addTab(self.ai_models_tab, "🤖 Модели ИИ")
            
            self.attacks_tab = AttacksTab(self.conn)
            self.tabs.addTab(self.attacks_tab, "⚡ DDoS Атаки")

    def close_tabs(self):
        """Закрывает вкладки с данными"""
        for i in range(self.tabs.count() - 1, 0, -1):
            self.tabs.removeTab(i)
        self.ai_models_tab = None
        self.attacks_tab = None

    def refresh_all_tabs(self):
        """Обновляет все вкладки с данными"""
        if self.ai_models_tab:
            self.ai_models_tab.refresh_data()
        if self.attacks_tab:
            self.attacks_tab.refresh_data()

def main():
    # Настройка логирования
    setup_logging()
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Создание и отображение главного окна
    win = MainWindow()
    win.show()
    
    # Запуск основного цикла
    sys.exit(app.exec())

if __name__ == '__main__':
    main()