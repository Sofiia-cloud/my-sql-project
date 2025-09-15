# -*- coding: utf-8 -*-
"""
PySide6 + PostgreSQL — MLOps система для обнаружения DDoS-атак
Создание таблиц через явные SQL-запросы
"""

import sys
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import faulthandler
import psycopg2
from psycopg2 import sql, errors
import logging

faulthandler.enable()

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QSpinBox,
    QComboBox, QCheckBox, QTextEdit, QTableView, QGroupBox, QTabWidget
)

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
    
    # SQL-скрипт для создания таблиц
    sql_script = """
    -- Создание типа ENUM для типов атак
    DO $$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attack_type') THEN
            CREATE TYPE attack_type AS ENUM ('udp_flood', 'icmp_flood', 'http_flood', 'syn_flood');
        END IF;
    END $$;

    -- Таблица моделей ИИ
    CREATE TABLE IF NOT EXISTS ai_models (
        model_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        version VARCHAR(50) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        CONSTRAINT unique_model_name_version UNIQUE (name, version)
    );

    -- Таблица экспериментов
    CREATE TABLE IF NOT EXISTS experiments (
        experiment_id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP WITH TIME ZONE,
        total_attacks INTEGER CHECK (total_attacks >= 0),
        detected_attacks INTEGER CHECK (detected_attacks >= 0 AND detected_attacks <= total_attacks),
        model_id INTEGER REFERENCES ai_models(model_id) ON DELETE SET NULL
    );

    -- Таблица DDoS атак
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

    -- Таблица результатов экспериментов
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
            # Вставка моделей ИИ
            cur.execute("""
                INSERT INTO ai_models (name, version, description, is_active) VALUES
                ('DeepPacket', '1.2.0', 'CNN для анализа сетевых пакетов', TRUE),
                ('FlowAnalyzer', '2.1.5', 'RNN для анализа сетевых потоков', TRUE),
                ('LegacyDetector', '0.9.1', 'Старая модель на основе правил', FALSE)
            """)
            
            # Вставка атак
            cur.execute("""
                INSERT INTO ddos_attacks (source_ip, target_ip, attack_type, packet_count, duration_seconds, target_ports) VALUES
                ('192.168.1.100', '10.0.0.50', 'udp_flood', 10000, 60, ARRAY[80, 443]),
                ('fe80::1', '2001:db8::1', 'http_flood', 50000, 120, ARRAY[8080]),
                ('172.16.0.10', '10.0.0.100', 'syn_flood', 75000, 30, ARRAY[22, 3389])
            """)
            
            # Вставка эксперимента
            cur.execute("""
                INSERT INTO experiments (name, model_id, total_attacks, detected_attacks) VALUES
                ('Test Run #1 - DeepPacket', 1, 3, 2)
            """)
            
            # Вставка результатов
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

        self.name_edit = QLineEdit()
        self.version_edit = QLineEdit()
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.active_checkbox = QCheckBox("Активная модель")
        self.active_checkbox.setChecked(True)

        form = QFormLayout()
        form.addRow("Название модели:", self.name_edit)
        form.addRow("Версия:", self.version_edit)
        form.addRow("Описание:", self.desc_edit)
        form.addRow("", self.active_checkbox)

        self.add_btn = QPushButton("Добавить модель")
        self.add_btn.clicked.connect(self.add_model)
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.refresh_data)

        btns = QHBoxLayout()
        btns.addWidget(self.add_btn)
        btns.addWidget(self.refresh_btn)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.table)

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

        self.source_ip_edit = QLineEdit()
        self.target_ip_edit = QLineEdit()
        self.attack_type_cb = QComboBox()
        self.attack_type_cb.addItems(['udp_flood', 'icmp_flood', 'http_flood', 'syn_flood'])
        self.packet_count_spin = QSpinBox()
        self.packet_count_spin.setRange(1, 1000000)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.ports_edit = QLineEdit()
        self.ports_edit.setPlaceholderText("80,443,8080")

        form = QFormLayout()
        form.addRow("Source IP:", self.source_ip_edit)
        form.addRow("Target IP:", self.target_ip_edit)
        form.addRow("Тип атаки:", self.attack_type_cb)
        form.addRow("Количество пакетов:", self.packet_count_spin)
        form.addRow("Длительность (сек):", self.duration_spin)
        form.addRow("Целевые порты:", self.ports_edit)

        self.add_btn = QPushButton("Добавить атаку")
        self.add_btn.clicked.connect(self.add_attack)
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.refresh_data)

        btns = QHBoxLayout()
        btns.addWidget(self.add_btn)
        btns.addWidget(self.refresh_btn)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.table)

    def add_attack(self):
        source_ip = self.source_ip_edit.text().strip()
        target_ip = self.target_ip_edit.text().strip()
        attack_type = self.attack_type_cb.currentText()
        packet_count = self.packet_count_spin.value()
        duration = self.duration_spin.value()
        ports_text = self.ports_edit.text().strip()
        
        # Преобразуем порты в массив
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
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {e}")

    def clear_form(self):
        self.source_ip_edit.clear()
        self.target_ip_edit.clear()
        self.packet_count_spin.setValue(1)
        self.duration_spin.setValue(1)
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
        
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.host_edit = QLineEdit(self.cfg.host)
        self.port_edit = QLineEdit(str(self.cfg.port))
        self.db_edit = QLineEdit(self.cfg.dbname)
        self.user_edit = QLineEdit(self.cfg.user)
        self.pw_edit = QLineEdit(self.cfg.password)
        self.pw_edit.setEchoMode(QLineEdit.Password)

        conn_form = QFormLayout()
        conn_form.addRow("Host:", self.host_edit)
        conn_form.addRow("Port:", self.port_edit)
        conn_form.addRow("DB name:", self.db_edit)
        conn_form.addRow("User:", self.user_edit)
        conn_form.addRow("Password:", self.pw_edit)

        conn_box = QGroupBox("Параметры подключения PostgreSQL")
        conn_box.setLayout(conn_form)

        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.clicked.connect(self.connect_db)
        self.disconnect_btn = QPushButton("Отключиться")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self.disconnect_db)

        self.create_btn = QPushButton("Создать таблицы")
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self.create_tables)

        self.demo_btn = QPushButton("Добавить демо-данные")
        self.demo_btn.setEnabled(False)
        self.demo_btn.clicked.connect(self.add_demo_data)

        top_btns = QHBoxLayout()
        top_btns.addWidget(self.connect_btn)
        top_btns.addWidget(self.disconnect_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(conn_box)
        layout.addLayout(top_btns)
        layout.addWidget(self.create_btn)
        layout.addWidget(self.demo_btn)
        layout.addWidget(QLabel("Лог:"))
        layout.addWidget(self.log)

    def get_config(self):
        """Получает текущую конфигурацию из полей ввода"""
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
            self.log.append(f"Подключено к {cfg.host}:{cfg.port}/{cfg.dbname}")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.create_btn.setEnabled(True)
            self.demo_btn.setEnabled(True)
            self.window().on_connection_established(self.conn)
        else:
            self.log.append("Ошибка подключения к БД")

    def disconnect_db(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        self.log.append("Отключено от БД")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.create_btn.setEnabled(False)
        self.demo_btn.setEnabled(False)
        self.window().on_connection_closed()

    def create_tables(self):
        if self.conn:
            if create_tables(self.conn):
                self.log.append("Таблицы успешно созданы")
                QMessageBox.information(self, "Успех", "Таблицы созданы успешно!")
            else:
                self.log.append("Ошибка создания таблиц")
        else:
            self.log.append("Нет подключения к БД")

    def add_demo_data(self):
        if self.conn:
            if insert_demo_data(self.conn):
                self.log.append("Демо-данные добавлены")
                QMessageBox.information(self, "Успех", "Демо-данные добавлены!")
                self.window().refresh_all_tabs()
            else:
                self.log.append("Ошибка добавления демо-данных")
        else:
            self.log.append("Нет подключения к БД")

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