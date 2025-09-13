# -*- coding: utf-8 -*-
"""
PySide6 + SQLAlchemy (PostgreSQL) — MLOps система для обнаружения DDoS-атак
"""

import sys
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import faulthandler

# Проверка наличия необходимых библиотек
try:
    import psycopg2
except ImportError:
    print("Ошибка: Не установлен модуль psycopg2. Установите его с помощью: pip install psycopg2")
    sys.exit(1)

try:
    from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
        QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QSpinBox,
        QComboBox, QCheckBox, QTextEdit, QTableView, QGroupBox
    )
    from sqlalchemy import (
        create_engine, MetaData, Table, Column, Integer, String, DateTime,
        ForeignKey, UniqueConstraint, CheckConstraint, select, insert, delete,
        Text, Boolean, Float, func
    )
    from sqlalchemy.dialects.postgresql import ARRAY, ENUM
    from sqlalchemy.engine import Engine
    from sqlalchemy.engine.url import URL
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError
except ImportError as e:
    print(f"Ошибка: Не установлены необходимые библиотеки: {e}")
    print("Установите зависимости с помощью: pip install PySide6 sqlalchemy psycopg2")
    sys.exit(1)

faulthandler.enable()

# -------------------------------
# Конфигурация подключения
# -------------------------------
@dataclass
class PgConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "ddos_mlops_db"
    user: str = "postgres"
    password: str = "root"
    sslmode: str = "prefer"
    connect_timeout: int = 5
    driver: str = "psycopg2"
    client_encoding: str = "utf8"

# -------------------------------
# Создание Engine и схемы
# -------------------------------
def make_engine(cfg: PgConfig) -> Engine:
    drivername_map = {
        "psycopg2": "postgresql+psycopg2",
        "psycopg": "postgresql+psycopg",
        "pg8000": "postgresql+pg8000",
    }
    drivername = drivername_map.get(cfg.driver, "postgresql+psycopg2")

    query = {
        "sslmode": cfg.sslmode,
        "application_name": "DDosMLOpsDemo",
        "connect_timeout": str(cfg.connect_timeout),
        "client_encoding": cfg.client_encoding,
    }

    try:
        url = URL.create(
            drivername=drivername,
            username=cfg.user,
            password=cfg.password,
            host=cfg.host,
            port=cfg.port,
            database=cfg.dbname,
            query=query,
        )

        engine = create_engine(url, future=True, pool_pre_ping=True)
        
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
            conn.exec_driver_sql(f"SET client_encoding TO '{cfg.client_encoding}'")
        return engine
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        raise

def build_metadata() -> Tuple[MetaData, Dict[str, Table]]:
    md = MetaData()

    ai_models = Table(
        "ai_models", md,
        Column("model_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(100), nullable=False),
        Column("version", String(50), nullable=False),
        Column("description", Text),
        Column("is_active", Boolean, server_default='TRUE'),
        UniqueConstraint("name", "version", name="uq_ai_models_name_version")
    )

    experiments = Table(
        "experiments", md,
        Column("experiment_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(255), nullable=False, unique=True),
        Column("start_time", DateTime(timezone=True), server_default=func.now()),
        Column("end_time", DateTime(timezone=True)),
        Column("total_attacks", Integer, CheckConstraint("total_attacks >= 0")),
        Column("detected_attacks", Integer, CheckConstraint("detected_attacks >= 0 AND detected_attacks <= total_attacks")),
        Column("model_id", Integer, ForeignKey("ai_models.model_id", ondelete="SET NULL")),
    )

    ddos_attacks = Table(
        "ddos_attacks", md,
        Column("attack_id", Integer, primary_key=True, autoincrement=True),
        Column("source_ip", String(45), nullable=False),
        Column("target_ip", String(45), nullable=False),
        Column("attack_type", ENUM('udp_flood', 'icmp_flood', 'http_flood', 'syn_flood', name='attack_type', create_type=True), nullable=False),
        Column("packet_count", Integer, CheckConstraint("packet_count > 0")),
        Column("duration_seconds", Integer, CheckConstraint("duration_seconds > 0")),
        Column("timestamp", DateTime(timezone=True), server_default=func.now()),
        Column("target_ports", ARRAY(Integer))
    )

    experiment_results = Table(
        "experiment_results", md,
        Column("result_id", Integer, primary_key=True, autoincrement=True),
        Column("experiment_id", Integer, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), nullable=False),
        Column("attack_id", Integer, ForeignKey("ddos_attacks.attack_id", ondelete="CASCADE"), nullable=False),
        Column("is_detected", Boolean, nullable=False),
        Column("confidence", Float, CheckConstraint("confidence >= 0.0 AND confidence <= 1.0")),
        Column("detection_time_ms", Integer, CheckConstraint("detection_time_ms >= 0")),
        UniqueConstraint("experiment_id", "attack_id", name="uq_result_experiment_attack")
    )

    return md, {
        "ai_models": ai_models,
        "experiments": experiments,
        "ddos_attacks": ddos_attacks,
        "experiment_results": experiment_results
    }

def drop_and_create_schema_sa(engine: Engine, md: MetaData) -> bool:
    try:
        with engine.begin() as conn:
            md.drop_all(engine)
            md.create_all(engine)
        return True
    except SQLAlchemyError as e:
        print(f"Ошибка при создании схемы: {e}")
        return False

def insert_demo_data_sa(engine: Engine, t: Dict[str, Table]) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(t["ai_models"].insert(), [
                {"name": "DeepPacket", "version": "1.2.0", "description": "CNN для анализа сетевых пакетов", "is_active": True},
                {"name": "FlowAnalyzer", "version": "2.1.5", "description": "RNN для анализа сетевых потоков", "is_active": True},
                {"name": "LegacyDetector", "version": "0.9.1", "description": "Старая модель на основе правил", "is_active": False},
            ])

            conn.execute(t["ddos_attacks"].insert(), [
                {"source_ip": "192.168.1.100", "target_ip": "10.0.0.50", "attack_type": "udp_flood", "packet_count": 10000, "duration_seconds": 60, "target_ports": [80, 443]},
                {"source_ip": "fe80::1", "target_ip": "2001:db8::1", "attack_type": "http_flood", "packet_count": 50000, "duration_seconds": 120, "target_ports": [8080]},
                {"source_ip": "172.16.0.10", "target_ip": "10.0.0.100", "attack_type": "syn_flood", "packet_count": 75000, "duration_seconds": 30, "target_ports": [22, 3389]},
            ])

            conn.execute(t["experiments"].insert(), [
                {"name": "Test Run #1 - DeepPacket", "model_id": 1, "total_attacks": 3, "detected_attacks": 2},
            ])

            conn.execute(t["experiment_results"].insert(), [
                {"experiment_id": 1, "attack_id": 1, "is_detected": True, "confidence": 0.99, "detection_time_ms": 150},
                {"experiment_id": 1, "attack_id": 2, "is_detected": True, "confidence": 0.85, "detection_time_ms": 220},
                {"experiment_id": 1, "attack_id": 3, "is_detected": False, "confidence": 0.10, "detection_time_ms": 50},
            ])
        return True
    except SQLAlchemyError as e:
        print(f"Ошибка при вставке демо-данных: {e}")
        return False

# -------------------------------
# QAbstractTableModel для SQLAlchemy
# -------------------------------
class SATableModel(QAbstractTableModel):
    def __init__(self, engine: Engine, table: Table, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.table = table
        self.columns: List[str] = [c.name for c in self.table.columns]
        self.pk_col = list(self.table.primary_key.columns)[0]
        self._rows: List[Dict[str, Any]] = []
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(select(self.table).order_by(self.pk_col.asc()))
                self._rows = [dict(r._mapping) for r in res]
        except SQLAlchemyError as e:
            print(f"Ошибка при обновлении данных таблицы: {e}")
        finally:
            self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        row = self._rows[index.row()]
        col_name = self.columns[index.column()]
        val = row.get(col_name)
        return "" if val is None else str(val)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        return self.columns[section] if orientation == Qt.Horizontal else section + 1

    def pk_value_at(self, row: int):
        return self._rows[row].get(self.pk_col.name) if 0 <= row < len(self._rows) else None

# -------------------------------
# Вкладка «Модели ИИ»
# -------------------------------
class AIModelsTab(QWidget):
    def __init__(self, engine: Engine, tables: Dict[str, Table], parent=None):
        super().__init__(parent)
        self.engine = engine
        self.t = tables
        self.model = SATableModel(engine, self.t["ai_models"], self)

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

        self.add_btn = QPushButton("Добавить модель (INSERT)")
        self.add_btn.clicked.connect(self.add_model)
        self.del_btn = QPushButton("Удалить выбранную модель")
        self.del_btn.clicked.connect(self.delete_selected)

        btns = QHBoxLayout()
        btns.addWidget(self.add_btn)
        btns.addWidget(self.del_btn)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.table)

    def add_model(self):
        if self.engine is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД")
            return
            
        name = self.name_edit.text().strip()
        version = self.version_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        is_active = self.active_checkbox.isChecked()

        if not name or not version:
            QMessageBox.warning(self, "Ввод", "Название и версия модели обязательны (NOT NULL)")
            return
            
        try:
            with self.engine.begin() as conn:
                conn.execute(insert(self.t["ai_models"]).values(
                    name=name, version=version, description=description, is_active=is_active
                ))
            self.model.refresh()
            self.name_edit.clear()
            self.version_edit.clear()
            self.desc_edit.clear()
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка INSERT", f"Нарушение ограничений базы данных: {str(e.orig)}")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка INSERT", f"Ошибка базы данных: {str(e)}")

    def delete_selected(self):
        if self.engine is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД")
            return
            
        idx = self.table.currentIndex()
        if not idx.isValid():
            QMessageBox.information(self, "Удаление", "Выберите модель")
            return
            
        mid = self.model.pk_value_at(idx.row())
        try:
            with self.engine.begin() as conn:
                conn.execute(delete(self.t["ai_models"]).where(self.t["ai_models"].c.model_id == mid))
            self.model.refresh()
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка удаления", f"Не удалось удалить модель: {str(e.orig)}")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка удаления", f"Ошибка базы данных: {str(e)}")

# -------------------------------
# Вкладка «DDoS Атаки»
# -------------------------------
class AttacksTab(QWidget):
    def __init__(self, engine: Engine, tables: Dict[str, Table], parent=None):
        super().__init__(parent)
        self.engine = engine
        self.t = tables
        self.model = SATableModel(engine, self.t["ddos_attacks"], self)

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

        self.add_btn = QPushButton("Добавить атаку (INSERT)")
        self.add_btn.clicked.connect(self.add_attack)
        self.del_btn = QPushButton("Удалить выбранную атаку")
        self.del_btn.clicked.connect(self.delete_selected)

        btns = QHBoxLayout()
        btns.addWidget(self.add_btn)
        btns.addWidget(self.del_btn)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.table)

    def add_attack(self):
        if self.engine is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД")
            return
            
        source_ip = self.source_ip_edit.text().strip()
        target_ip = self.target_ip_edit.text().strip()
        attack_type = self.attack_type_cb.currentText()
        packet_count = self.packet_count_spin.value()
        duration = self.duration_spin.value()
        
        ports_text = self.ports_edit.text().strip()
        try:
            target_ports = [int(port.strip()) for port in ports_text.split(',') if port.strip()] if ports_text else None
            if target_ports and any(port <= 0 or port > 65535 for port in target_ports):
                QMessageBox.warning(self, "Ввод", "Порты должны быть в диапазоне 1-65535")
                return
        except ValueError:
            QMessageBox.warning(self, "Ввод", "Некорректный формат портов. Используйте числа, разделенные запятыми")
            return

        if not source_ip or not target_ip:
            QMessageBox.warning(self, "Ввод", "Source IP и Target IP обязательны")
            return
            
        try:
            with self.engine.begin() as conn:
                conn.execute(insert(self.t["ddos_attacks"]).values(
                    source_ip=source_ip,
                    target_ip=target_ip,
                    attack_type=attack_type,
                    packet_count=packet_count,
                    duration_seconds=duration,
                    target_ports=target_ports
                ))
            self.model.refresh()
            self.source_ip_edit.clear()
            self.target_ip_edit.clear()
            self.packet_count_spin.setValue(1)
            self.duration_spin.setValue(1)
            self.ports_edit.clear()
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка INSERT", f"Нарушение ограничений базы данных: {str(e.orig)}")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка INSERT", f"Ошибка базы данных: {str(e)}")

    def delete_selected(self):
        if self.engine is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД")
            return
            
        idx = self.table.currentIndex()
        if not idx.isValid():
            QMessageBox.information(self, "Удаление", "Выберите атаку")
            return
            
        aid = self.model.pk_value_at(idx.row())
        try:
            with self.engine.begin() as conn:
                conn.execute(delete(self.t["ddos_attacks"]).where(self.t["ddos_attacks"].c.attack_id == aid))
            self.model.refresh()
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка удаления", f"Не удалось удалить атаку: {str(e.orig)}")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка удаления", f"Ошибка базы данных: {str(e)}")

# -------------------------------
# Вкладка «Эксперименты»
# -------------------------------
class ExperimentsTab(QWidget):
    def __init__(self, engine: Engine, tables: Dict[str, Table], parent=None):
        super().__init__(parent)
        self.engine = engine
        self.t = tables
        self.model = SATableModel(engine, self.t["experiments"], self)

        self.name_edit = QLineEdit()
        self.model_cb = QComboBox()
        self.total_attacks_spin = QSpinBox()
        self.total_attacks_spin.setRange(0, 1000000)
        self.detected_attacks_spin = QSpinBox()
        self.detected_attacks_spin.setRange(0, 1000000)
        
        self.refresh_models()

        form = QFormLayout()
        form.addRow("Название эксперимента:", self.name_edit)
        form.addRow("Модель ИИ:", self.model_cb)
        form.addRow("Всего атак:", self.total_attacks_spin)
        form.addRow("Обнаружено атак:", self.detected_attacks_spin)

        self.add_btn = QPushButton("Добавить эксперимент (INSERT)")
        self.add_btn.clicked.connect(self.add_experiment)
        self.del_btn = QPushButton("Удалить выбранный эксперимент")
        self.del_btn.clicked.connect(self.delete_selected)

        btns = QHBoxLayout()
        btns.addWidget(self.add_btn)
        btns.addWidget(self.del_btn)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.table)

    def refresh_models(self):
        self.model_cb.clear()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(select(self.t["ai_models"].c.model_id, self.t["ai_models"].c.name))
                for row in res:
                    self.model_cb.addItem(row.name, row.model_id)
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка загрузки моделей", f"Ошибка базы данных: {str(e)}")

    def add_experiment(self):
        if self.engine is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД")
            return
            
        name = self.name_edit.text().strip()
        model_id = self.model_cb.currentData()
        total_attacks = self.total_attacks_spin.value()
        detected_attacks = self.detected_attacks_spin.value()

        if not name:
            QMessageBox.warning(self, "Ввод", "Название эксперимента обязательно")
            return
            
        if detected_attacks > total_attacks:
            QMessageBox.warning(self, "Ввод", "Обнаруженных атак не может быть больше общего количества")
            return

        try:
            with self.engine.begin() as conn:
                conn.execute(insert(self.t["experiments"]).values(
                    name=name,
                    model_id=model_id,
                    total_attacks=total_attacks,
                    detected_attacks=detected_attacks
                ))
            self.model.refresh()
            self.name_edit.clear()
            self.total_attacks_spin.setValue(0)
            self.detected_attacks_spin.setValue(0)
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка INSERT", f"Нарушение ограничений базы данных: {str(e.orig)}")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка INSERT", f"Ошибка базы данных: {str(e)}")

    def delete_selected(self):
        if self.engine is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД")
            return
            
        idx = self.table.currentIndex()
        if not idx.isValid():
            QMessageBox.information(self, "Удаление", "Выберите эксперимент")
            return
            
        eid = self.model.pk_value_at(idx.row())
        try:
            with self.engine.begin() as conn:
                conn.execute(delete(self.t["experiments"]).where(self.t["experiments"].c.experiment_id == eid))
            self.model.refresh()
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка удаления", f"Не удалось удалить эксперимент: {str(e.orig)}")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка удаления", f"Ошибка базы данных: {str(e)}")

# -------------------------------
# Вкладка «Результаты экспериментов»
# -------------------------------
class ResultsTab(QWidget):
    def __init__(self, engine: Engine, tables: Dict[str, Table], parent=None):
        super().__init__(parent)
        self.engine = engine
        self.t = tables
        self.model = SATableModel(engine, self.t["experiment_results"], self)

        self.experiment_cb = QComboBox()
        self.attack_cb = QComboBox()
        self.detected_checkbox = QCheckBox("Обнаружена")
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.0, 1.0)
        self.confidence_spin.setSingleStep(0.01)
        self.detection_time_spin = QSpinBox()
        self.detection_time_spin.setRange(0, 1000000)
        
        self.refresh_experiments()
        self.refresh_attacks()

        form = QFormLayout()
        form.addRow("Эксперимент:", self.experiment_cb)
        form.addRow("Атака:", self.attack_cb)
        form.addRow("", self.detected_checkbox)
        form.addRow("Уверенность:", self.confidence_spin)
        form.addRow("Время обнаружения (мс):", self.detection_time_spin)

        self.add_btn = QPushButton("Добавить результат (INSERT)")
        self.add_btn.clicked.connect(self.add_result)
        self.del_btn = QPushButton("Удалить выбранный результат")
        self.del_btn.clicked.connect(self.delete_selected)

        btns = QHBoxLayout()
        btns.addWidget(self.add_btn)
        btns.addWidget(self.del_btn)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.table)

    def refresh_experiments(self):
        self.experiment_cb.clear()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(select(self.t["experiments"].c.experiment_id, self.t["experiments"].c.name))
                for row in res:
                    self.experiment_cb.addItem(row.name, row.experiment_id)
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка загрузки экспериментов", f"Ошибка базы данных: {str(e)}")

    def refresh_attacks(self):
        self.attack_cb.clear()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(select(
                    self.t["ddos_attacks"].c.attack_id,
                    func.concat(self.t["ddos_attacks"].c.source_ip, ' -> ', self.t["ddos_attacks"].c.target_ip).label('description')
                ))
                for row in res:
                    self.attack_cb.addItem(row.description, row.attack_id)
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка загрузки атак", f"Ошибка базы данных: {str(e)}")

    def add_result(self):
        if self.engine is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД")
            return
            
        experiment_id = self.experiment_cb.currentData()
        attack_id = self.attack_cb.currentData()
        is_detected = self.detected_checkbox.isChecked()
        confidence = self.confidence_spin.value()
        detection_time = self.detection_time_spin.value()

        if not experiment_id or not attack_id:
            QMessageBox.warning(self, "Ввод", "Выберите эксперимент и атаку")
            return

        try:
            with self.engine.begin() as conn:
                conn.execute(insert(self.t["experiment_results"]).values(
                    experiment_id=experiment_id,
                    attack_id=attack_id,
                    is_detected=is_detected,
                    confidence=confidence,
                    detection_time_ms=detection_time
                ))
            self.model.refresh()
            self.confidence_spin.setValue(0.0)
            self.detection_time_spin.setValue(0)
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка INSERT", f"Нарушение ограничений базы данных: {str(e.orig)}")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка INSERT", f"Ошибка базы данных: {str(e)}")

    def delete_selected(self):
        if self.engine is None:
            QMessageBox.critical(self, "Ошибка", "Нет подключения к БД")
            return
            
        idx = self.table.currentIndex()
        if not idx.isValid():
            QMessageBox.information(self, "Удаление", "Выберите результат")
            return
            
        rid = self.model.pk_value_at(idx.row())
        try:
            with self.engine.begin() as conn:
                conn.execute(delete(self.t["experiment_results"]).where(self.t["experiment_results"].c.result_id == rid))
            self.model.refresh()
        except IntegrityError as e:
            QMessageBox.critical(self, "Ошибка удаления", f"Не удалось удалить результат: {str(e.orig)}")
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Ошибка удаления", f"Ошибка базы данных: {str(e)}")

# -------------------------------
# Главное окно
# -------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MLOps система для обнаружения DDoS-атак")
        self.setGeometry(100, 100, 1200, 800)

        self.engine = None
        self.tables = {}
        
        self.init_ui()
        self.connect_db()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.tabs = QTabWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.tabs)
        
        self.reconnect_btn = QPushButton("Переподключиться к БД")
        self.reconnect_btn.clicked.connect(self.connect_db)
        layout.addWidget(self.reconnect_btn)

    def connect_db(self):
        try:
            cfg = PgConfig()
            self.engine = make_engine(cfg)
            
            metadata, self.tables = build_metadata()
            
            while self.tabs.count() > 0:
                self.tabs.removeTab(0)
            
            if drop_and_create_schema_sa(self.engine, metadata):
                if insert_demo_data_sa(self.engine, self.tables):
                    self.create_tabs()
                    QMessageBox.information(self, "Успех", "База данных инициализирована с демо-данными")
                else:
                    QMessageBox.warning(self, "Предупреждение", "Демо-данные не загружены")
                    self.create_tabs()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось создать схему БД")
                
        except Exception as e:
            error_msg = str(e)
            if "codec" in error_msg.lower() and "byte" in error_msg.lower():
                error_msg = "Ошибка кодировки при подключении к БД. Проверьте настройки кодировки PostgreSQL и убедитесь, что установлен psycopg2."
            QMessageBox.critical(self, "Ошибка подключения", f"Не удалось подключиться к БД: {error_msg}")
            self.engine = None
            self.create_tabs()

    def create_tabs(self):
        if self.engine is None:
            error_widget = QWidget()
            layout = QVBoxLayout(error_widget)
            layout.addWidget(QLabel("Нет подключения к базе данных. Нажмите 'Переподключиться к БД'"))
            self.tabs.addTab(error_widget, "Нет подключения")
            return
            
        self.tabs.addTab(AIModelsTab(self.engine, self.tables), "Модели ИИ")
        self.tabs.addTab(AttacksTab(self.engine, self.tables), "DDoS Атаки")
        self.tabs.addTab(ExperimentsTab(self.engine, self.tables), "Эксперименты")
        self.tabs.addTab(ResultsTab(self.engine, self.tables), "Результаты")

# -------------------------------
# Точка входа
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())