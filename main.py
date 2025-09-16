# -*- coding: utf-8 -*-
"""
PySide6 + PostgreSQL — MLOps система для обнаружения DDoS-атак
Современный интерфейс с улучшенным дизайном
"""

import sys
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import faulthandler
import psycopg2
from psycopg2 import sql, errors
import logging
from datetime import datetime

faulthandler.enable()

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QSpinBox,
    QComboBox, QCheckBox, QTextEdit, QTableView, QGroupBox, QTabWidget,
    QFrame, QSizePolicy
)
from PySide6.QtGui import QFont, QPalette, QColor, QIcon

# -------------------------------
# Конфигурация подключения и логирование
# -------------------------------
@dataclass
class PgConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "ddos_mlops_db"
    user: str = "postgres"
    password: str = "root"
    sslmode: str = "prefer"

# Настройка логирования
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# -------------------------------
# Стили и цвета
# -------------------------------
STYLES = {
    "primary_color": "#5b856a",
    "secondary_color": "#345e49",
    "accent_color": "#34db69",
    "success_color": "#27ae60",
    "danger_color": "#e74c3c",
    "warning_color": "#f39c12",
    "light_color": "#ecf0f1",
    "dark_color": "#182e20",
    "text_color": "#2c503a",
    "background_color": "#f8f9fa"
}

def apply_dark_theme(app):
    """Применяет темную тему к приложению"""
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)

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

# -------------------------------
# Функции работы с базой данных
# -------------------------------
def create_connection(cfg: PgConfig):
    """Создает подключение к PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=cfg.host,
            port=cfg.port,
            dbname=cfg.dbname,
            user=cfg.user,
            password=cfg.password,
            sslmode=cfg.sslmode
        )
        logging.info("Успешное подключение к PostgreSQL")
        return conn
    except Exception as e:
        logging.error(f"Ошибка подключения: {e}")
        return None

def execute_sql_script(conn, script: str):
    """Выполняет SQL-скрипт"""
    try:
        with conn.cursor() as cur:
            cur.execute(script)
        conn.commit()
        logging.info("SQL-скрипт выполнен успешно")
        return True
    except Exception as e:
        conn.rollback()
        logging.error(f"Ошибка выполнения SQL-скрипта: {e}")
        return False

def create_tables(conn):
    """Создает все необходимые таблицы через SQL-запросы"""
    
    sql_script = """
    DO $$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attack_type') THEN
            CREATE TYPE attack_type AS ENUM ('udp_flood', 'icmp_flood', 'http_flood', 'syn_flood');
        END IF;
    END $$;

    CREATE TABLE IF NOT EXISTS ai_models (
        model_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        version VARCHAR(50) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        CONSTRAINT unique_model_name_version UNIQUE (name, version)
    );

    CREATE TABLE IF NOT EXISTS experiments (
        experiment_id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP WITH TIME ZONE,
        total_attacks INTEGER CHECK (total_attacks >= 0),
        detected_attacks INTEGER CHECK (detected_attacks >= 0 AND detected_attacks <= total_attacks),
        model_id INTEGER REFERENCES ai_models(model_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS ddos_attacks (
        attack_id SERIAL PRIMARY KEY,
        source_ip VARCHAR(45) NOT NULL,
        target_ip VARCHAR(45) NOT NULL,
        attack_type attack_type NOT NULL,
        packet_count INTEGER CHECK (packet_count > 0),
        duration_seconds INTEGER CHECK (duration_seconds > 0),
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        target_ports INTEGER[]
    );

    CREATE TABLE IF NOT EXISTS experiment_results (
        result_id SERIAL PRIMARY KEY,
        experiment_id INTEGER NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
        attack_id INTEGER NOT NULL REFERENCES ddos_attacks(attack_id) ON DELETE CASCADE,
        is_detected BOOLEAN NOT NULL,
        confidence FLOAT CHECK (confidence >= 0.0 AND confidence <= 1.0),
        detection_time_ms INTEGER CHECK (detection_time_ms >= 0),
        CONSTRAINT unique_experiment_attack UNIQUE (experiment_id, attack_id)
    );
    """
    
    return execute_sql_script(conn, sql_script)

def insert_demo_data(conn):
    """Вставляет демонстрационные данные"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ai_models (name, version, description, is_active) VALUES
                ('DeepPacket', '1.2.0', 'CNN для анализа сетевых пакетов', TRUE),
                ('FlowAnalyzer', '2.1.5', 'RNN для анализа сетевых потоков', TRUE),
                ('LegacyDetector', '0.9.1', 'Старая модель на основе правил', FALSE)
            """)
            
            cur.execute("""
                INSERT INTO ddos_attacks (source_ip, target_ip, attack_type, packet_count, duration_seconds, target_ports) VALUES
                ('192.168.1.100', '10.0.0.50', 'udp_flood', 10000, 60, ARRAY[80, 443]),
                ('fe80::1', '2001:db8::1', 'http_flood', 50000, 120, ARRAY[8080]),
                ('172.16.0.10', '10.0.0.100', 'syn_flood', 75000, 30, ARRAY[22, 3389])
            """)
            
            cur.execute("""
                INSERT INTO experiments (name, model_id, total_attacks, detected_attacks) VALUES
                ('Test Run #1 - DeepPacket', 1, 3, 2)
            """)
            
            cur.execute("""
                INSERT INTO experiment_results (experiment_id, attack_id, is_detected, confidence, detection_time_ms) VALUES
                (1, 1, TRUE, 0.99, 150),
                (1, 2, TRUE, 0.85, 220),
                (1, 3, FALSE, 0.10, 50)
            """)
        
        conn.commit()
        logging.info("Демо-данные успешно добавлены")
        return True
    except Exception as e:
        conn.rollback()
        logging.error(f"Ошибка вставки демо-данных: {e}")
        return False

def fetch_data(conn, table_name: str):
    """Получает данные из таблицы"""
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return columns, rows
    except Exception as e:
        logging.error(f"Ошибка получения данных из {table_name}: {e}")
        return [], []

# -------------------------------
# Модель таблицы для Qt
# -------------------------------
class PostgreSQLTableModel(QAbstractTableModel):
    def __init__(self, conn, table_name: str, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.table_name = table_name
        self.columns = []
        self.rows = []
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        self.columns, self.rows = fetch_data(self.conn, self.table_name)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return str(self.rows[index.row()][index.column()])

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        return self.columns[section] if orientation == Qt.Horizontal else str(section + 1)

# -------------------------------
# Вкладка «Модели ИИ»
# -------------------------------
class AIModelsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.model = PostgreSQLTableModel(conn, "ai_models", self)
        
        # Заголовок
        title_label = QLabel("Управление моделями ИИ")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #3498db;
                color: white;
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
        self.setStyleSheet("background-color: #ecf0f1;")

    def add_model(self):
        name = self.name_edit.text().strip()
        version = self.version_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        is_active = self.active_checkbox.isChecked()

        if not name or not version:
            QMessageBox.warning(self, "Ошибка", "Название и версия обязательны")
            return

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ai_models (name, version, description, is_active) VALUES (%s, %s, %s, %s)",
                    (name, version, description, is_active)
                )
            self.conn.commit()
            self.refresh_data()
            self.name_edit.clear()
            self.version_edit.clear()
            self.desc_edit.clear()
            QMessageBox.information(self, "Успех", "Модель успешно добавлена!")
        except errors.UniqueViolation:
            QMessageBox.critical(self, "Ошибка", "Модель с таким именем и версией уже существует")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {e}")

    def refresh_data(self):
        self.model.refresh()

# -------------------------------
# Вкладка «DDoS Атаки»
# -------------------------------
class AttacksTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.model = PostgreSQLTableModel(conn, "ddos_attacks", self)
        
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
        self.add_btn = create_styled_button("Добавить атаку", STYLES["danger_color"])
        self.add_btn.clicked.connect(self.add_attack)
        self.refresh_btn = create_styled_button("Обновить", STYLES["accent_color"])
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.clear_btn = create_styled_button("Очистить", STYLES["warning_color"])
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
        self.setStyleSheet("background-color: #ecf0f1;")

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
            with self.conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO ddos_attacks 
                    (source_ip, target_ip, attack_type, packet_count, duration_seconds, target_ports) 
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (source_ip, target_ip, attack_type, packet_count, duration, target_ports)
                )
            self.conn.commit()
            self.refresh_data()
            self.clear_form()
            QMessageBox.information(self, "Успех", "Атака успешно добавлена!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {e}")

    def clear_form(self):
        self.source_ip_edit.clear()
        self.target_ip_edit.clear()
        self.packet_count_spin.setValue(1000)
        self.duration_spin.setValue(60)
        self.ports_edit.clear()

    def refresh_data(self):
        self.model.refresh()

# -------------------------------
# Вкладка подключения и управления БД
# -------------------------------
class SetupTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = None
        self.cfg = PgConfig()
        
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
        self.connect_btn = create_styled_button("Подключиться", STYLES["success_color"])
        self.connect_btn.clicked.connect(self.connect_db)
        self.disconnect_btn = create_styled_button("Отключиться", STYLES["danger_color"])
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self.disconnect_db)

        self.create_btn = create_styled_button("Создать таблицы", STYLES["accent_color"])
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self.create_tables)

        self.demo_btn = create_styled_button("Добавить демо-данные", STYLES["warning_color"])
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
        self.setStyleSheet("background-color: #ecf0f1;")

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
            if create_tables(self.conn):
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log.append(f"[{timestamp}] ✅ Таблицы успешно созданы")
                QMessageBox.information(self, "Успех", "Таблицы созданы успешно!")
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log.append(f"[{timestamp}] ❌ Ошибка создания таблиц")
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log.append(f"[{timestamp}] Нет подключения к БД")

    def add_demo_data(self):
        if self.conn:
            if insert_demo_data(self.conn):
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log.append(f"[{timestamp}] Демо-данные добавлены")
                QMessageBox.information(self, "Успех", "Демо-данные добавлены!")
                self.window().refresh_all_tabs()
            else:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log.append(f"[{timestamp}] Ошибка добавления демо-данных")
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log.append(f"[{timestamp}] Нет подключения к БД")



# -------------------------------
# Главное окно
# -------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MLOps система для обнаружения DDoS-атак")
        self.resize(1200, 800)

        self.conn = None
        self.tabs = QTabWidget()
        
        self.setup_tab = SetupTab()
        self.tabs.addTab(self.setup_tab, "Подключение к БД")
        
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
            self.tabs.addTab(self.ai_models_tab, "Модели ИИ")
            
            self.attacks_tab = AttacksTab(self.conn)
            self.tabs.addTab(self.attacks_tab, "DDoS Атаки")

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

# -------------------------------
# Точка входа
# -------------------------------
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()