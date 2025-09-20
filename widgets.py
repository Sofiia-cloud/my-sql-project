# widgets.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QTextEdit, QCheckBox, QSpinBox, QComboBox,
    QTextEdit, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from datetime import datetime
from database import create_tables, insert_demo_data, create_connection
from models import PostgreSQLTableModel
from styles import create_styled_button, create_group_box, create_table
from config import STYLES, PgConfig
from psycopg2 import errors
from database import create_tables, insert_demo_data, create_connection, drop_and_recreate_tables

class AIModelsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.model = PostgreSQLTableModel(conn, "ai_models", self)
        self.setup_ui()

    def setup_ui(self):
        # Заголовок
        title_label = QLabel("Управление моделями ИИ")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 10px;
                background-color: #3498db;
                border-radius: 8px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)

        # Форма ввода
        form_group = create_group_box("Добавить новую модель")
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название модели")
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("Введите версию")
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setPlaceholderText("Описание модели...")
        self.active_checkbox = QCheckBox("Активная модель")
        self.active_checkbox.setChecked(True)

        form_layout.addRow("Название:", self.name_edit)
        form_layout.addRow("Версия:", self.version_edit)
        form_layout.addRow("Описание:", self.desc_edit)
        form_layout.addRow("", self.active_checkbox)
        form_group.setLayout(form_layout)

        # Кнопки
        self.add_btn = create_styled_button("➕ Добавить модель", STYLES["success_color"])
        self.add_btn.clicked.connect(self.add_model)
        self.refresh_btn = create_styled_button("🔄 Обновить", STYLES["accent_color"])
        self.refresh_btn.clicked.connect(self.refresh_data)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addStretch()

        # Таблица
        table_group = create_group_box("Список моделей")
        table_layout = QVBoxLayout()
        self.table = create_table()
        self.table.setModel(self.model)
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(form_group)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(table_group)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.setLayout(main_layout)

    def add_model(self):
        name = self.name_edit.text().strip()
        version = self.version_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        is_active = self.active_checkbox.isChecked()

        if not name or not version:
            QMessageBox.warning(self, "Ошибка", "Название и версия обязательны")
            return

        try:
            # Явно начинаем транзакцию
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO ai_models (name, version, description, is_active) VALUES (%s, %s, %s, %s)",
                        (name, version, description, is_active)
                    )
            
            self.refresh_data()
            self.name_edit.clear()
            self.version_edit.clear()
            self.desc_edit.clear()
            QMessageBox.information(self, "Успех", "Модель успешно добавлена!")
            
        except errors.UniqueViolation:
            QMessageBox.critical(self, "Ошибка", "Модель с таким именем и версией уже существует")
            self.conn.rollback()  # Явный откат
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {e}")
            self.conn.rollback()  # Явный откат
    def refresh_data(self):
        self.model.refresh()

class AttacksTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.model = PostgreSQLTableModel(conn, "ddos_attacks", self)
        self.setup_ui()

    def setup_ui(self):
        # Заголовок
        title_label = QLabel("Управление DDoS атаками")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 10px;
                background-color: #e74c3c;
                border-radius: 8px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)

        # Форма ввода
        form_group = create_group_box("Добавить новую атаку")
        form_layout = QFormLayout()
        
        self.source_ip_edit = QLineEdit()
        self.source_ip_edit.setPlaceholderText("192.168.1.100")
        self.target_ip_edit = QLineEdit()
        self.target_ip_edit.setPlaceholderText("10.0.0.50")
        self.attack_type_cb = QComboBox()
        self.attack_type_cb.addItems(['udp_flood', 'icmp_flood', 'http_flood', 'syn_flood'])
        self.packet_count_spin = QSpinBox()
        self.packet_count_spin.setRange(1, 1000000)
        self.packet_count_spin.setValue(1000)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(60)
        self.ports_edit = QLineEdit()
        self.ports_edit.setPlaceholderText("80,443,8080")

        form_layout.addRow("Source IP:", self.source_ip_edit)
        form_layout.addRow("Target IP:", self.target_ip_edit)
        form_layout.addRow("Тип атаки:", self.attack_type_cb)
        form_layout.addRow("Пакеты:", self.packet_count_spin)
        form_layout.addRow("Длительность (сек):", self.duration_spin)
        form_layout.addRow("Порты:", self.ports_edit)
        form_group.setLayout(form_layout)

        # Кнопки
        self.add_btn = create_styled_button("➕ Добавить атаку", STYLES["danger_color"])
        self.add_btn.clicked.connect(self.add_attack)
        self.refresh_btn = create_styled_button("🔄 Обновить", STYLES["accent_color"])
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.clear_btn = create_styled_button("🗑️ Очистить", STYLES["warning_color"])
        self.clear_btn.clicked.connect(self.clear_form)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addStretch()

        # Таблица
        table_group = create_group_box("История атак")
        table_layout = QVBoxLayout()
        self.table = create_table()
        self.table.setModel(self.model)
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(form_group)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(table_group)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.setLayout(main_layout)

    def add_attack(self):
        source_ip = self.source_ip_edit.text().strip()
        target_ip = self.target_ip_edit.text().strip()
        attack_type = self.attack_type_cb.currentText()
        packet_count = self.packet_count_spin.value()
        duration = self.duration_spin.value()
        ports_text = self.ports_edit.text().strip()
        
        target_ports = [int(p.strip()) for p in ports_text.split(',') if p.strip()] if ports_text else None

        if not source_ip or not target_ip:
            QMessageBox.warning(self, "Ошибка", "IP адреса обязательны")
            return

        try:
            # Явно начинаем транзакцию
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO ddos_attacks 
                        (source_ip, target_ip, attack_type, packet_count, duration_seconds, target_ports) 
                        VALUES (%s, %s, %s, %s, %s, %s)""",
                        (source_ip, target_ip, attack_type, packet_count, duration, target_ports)
                    )
            
            self.refresh_data()
            self.clear_form()
            QMessageBox.information(self, "Успех", "Атака успешно добавлена!")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {e}")
            self.conn.rollback()  # Явный откат
    def clear_form(self):
        self.source_ip_edit.clear()
        self.target_ip_edit.clear()
        self.packet_count_spin.setValue(1000)
        self.duration_spin.setValue(60)
        self.ports_edit.clear()

    def refresh_data(self):
        self.model.refresh()

class SetupTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = None
        self.cfg = PgConfig()
        self.setup_ui()

    def setup_ui(self):
        # Заголовок
        title_label = QLabel("Подключение к базе данных")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 10px;
                background-color: #34495e;
                border-radius: 8px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)

        # Форма подключения
        conn_group = create_group_box("Параметры подключения PostgreSQL")
        conn_layout = QFormLayout()
        
        self.host_edit = QLineEdit(self.cfg.host)
        self.port_edit = QLineEdit(str(self.cfg.port))
        self.db_edit = QLineEdit(self.cfg.dbname)
        self.user_edit = QLineEdit(self.cfg.user)
        self.pw_edit = QLineEdit(self.cfg.password)
        self.pw_edit.setEchoMode(QLineEdit.Password)

        # Стилизация полей ввода
        for edit in [self.host_edit, self.port_edit, self.db_edit, self.user_edit, self.pw_edit]:
            edit.setStyleSheet("""
                QLineEdit {
                    padding: 6px;
                    border: 2px solid #bdc3c7;
                    border-radius: 4px;
                    background-color: white;
                }
                QLineEdit:focus {
                    border-color: #3498db;
                }
            """)

        conn_layout.addRow("Хост:", self.host_edit)
        conn_layout.addRow("Порт:", self.port_edit)
        conn_layout.addRow("База данных:", self.db_edit)
        conn_layout.addRow("Пользователь:", self.user_edit)
        conn_layout.addRow("Пароль:", self.pw_edit)
        conn_group.setLayout(conn_layout)

        # Кнопки управления
        self.connect_btn = create_styled_button("🔗 Подключиться", STYLES["success_color"])
        self.connect_btn.clicked.connect(self.connect_db)
        self.disconnect_btn = create_styled_button("🔌 Отключиться", STYLES["danger_color"])
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self.disconnect_db)

        self.create_btn = create_styled_button("🗃️ Создать таблицы", STYLES["accent_color"])
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self.create_tables)

        self.demo_btn = create_styled_button("📊 Добавить демо-данные", STYLES["warning_color"])
        self.demo_btn.setEnabled(False)
        self.demo_btn.clicked.connect(self.add_demo_data)

        buttons_layout1 = QHBoxLayout()
        buttons_layout1.addWidget(self.connect_btn)
        buttons_layout1.addWidget(self.disconnect_btn)
        buttons_layout1.addStretch()

        buttons_layout2 = QHBoxLayout()
        buttons_layout2.addWidget(self.create_btn)
        buttons_layout2.addWidget(self.demo_btn)
        buttons_layout2.addStretch()

        # Лог
        log_group = create_group_box("Журнал событий")
        log_layout = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 4px;
                font-family: 'Courier New';
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log)
        log_group.setLayout(log_layout)

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(conn_group)
        main_layout.addLayout(buttons_layout1)
        main_layout.addLayout(buttons_layout2)
        main_layout.addWidget(log_group)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.setLayout(main_layout)

    def get_config(self):
        try:
            port = int(self.port_edit.text().strip())
        except ValueError:
            port = self.cfg.port
            
        return PgConfig(
            host=self.host_edit.text().strip(),
            port=port,
            dbname=self.db_edit.text().strip(),
            user=self.user_edit.text().strip(),
            password=self.pw_edit.text(),
            sslmode=self.cfg.sslmode
        )

    def connect_db(self):
        cfg = self.get_config()
        self.conn = create_connection(cfg)
        
        if self.conn:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log.append(f"[{timestamp}] ✅ Подключено к {cfg.host}:{cfg.port}/{cfg.dbname}")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.create_btn.setEnabled(True)
            self.demo_btn.setEnabled(True)
            self.window().on_connection_established(self.conn)
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log.append(f"[{timestamp}] ❌ Ошибка подключения к БД")

    def disconnect_db(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] 🔌 Отключено от БД")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.create_btn.setEnabled(False)
        self.demo_btn.setEnabled(False)
        self.window().on_connection_closed()

    def create_tables(self):
        if self.conn:
            if drop_and_recreate_tables(self.conn):  # Используем новую функцию
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log.append(f"[{timestamp}] ✅ Таблицы успешно созданы")
                QMessageBox.information(self, "Успех", "Таблицы созданы успешно!")
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log.append(f"[{timestamp}] ❌ Ошибка создания таблиц")
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log.append(f"[{timestamp}] ⚠️ Нет подключения к БД")

    def add_demo_data(self):
        if self.conn:
            if insert_demo_data(self.conn):
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log.append(f"[{timestamp}] ✅ Демо-данные добавлены")
                QMessageBox.information(self, "Успех", "Демо-данные добавлены!")
                self.window().refresh_all_tabs()
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log.append(f"[{timestamp}] ❌ Ошибка добавления демо-данных")
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log.append(f"[{timestamp}] ⚠️ Нет подключения к БД")