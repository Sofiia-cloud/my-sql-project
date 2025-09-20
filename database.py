import psycopg2
from psycopg2 import sql, errors
import logging
from config import PgConfig

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

def insert_demo_data(conn):
    """Вставляет демонстрационные данные"""
    try:
        with conn:
            with conn.cursor() as cur:
                # Проверяем, есть ли уже данные
                cur.execute("SELECT COUNT(*) FROM ai_models")
                if cur.fetchone()[0] > 0:
                    logging.info("Демо-данные уже существуют")
                    return True
                
                # Добавляем модели ИИ
                cur.execute("""
                    INSERT INTO ai_models (name, version, description, is_active) VALUES
                    ('DeepPacket', '1.2.0', 'CNN для анализа сетевых пакетов', TRUE),
                    ('FlowAnalyzer', '2.1.5', 'RNN для анализа сетевых потоков', TRUE),
                    ('LegacyDetector', '0.9.1', 'Старая модель на основе правил', FALSE)
                """)
                
                # Добавляем данные об атаках
                cur.execute("""
                    INSERT INTO ddos_attacks (source_ip, target_ip, attack_type, packet_count, duration_seconds, target_ports) VALUES
                    ('192.168.1.100', '10.0.0.50', 'udp_flood', 10000, 60, ARRAY[80, 443]),
                    ('fe80::1', '2001:db8::1', 'http_flood', 50000, 120, ARRAY[8080]),
                    ('172.16.0.10', '10.0.0.100', 'syn_flood', 75000, 30, ARRAY[22, 3389])
                """)
                
                # Добавляем эксперимент
                cur.execute("""
                    INSERT INTO experiments (name, model_id, total_attacks, detected_attacks) VALUES
                    ('Test Run #1 - DeepPacket', 1, 3, 2)
                """)
                
                # Добавляем результаты эксперимента
                cur.execute("""
                    INSERT INTO experiment_results (experiment_id, attack_id, is_detected, confidence, detection_time_ms) VALUES
                    (1, 1, TRUE, 0.99, 150),
                    (1, 2, TRUE, 0.85, 220),
                    (1, 3, FALSE, 0.10, 50)
                """)
        
        logging.info("Демо-данные успешно добавлены")
        return True
        
    except Exception as e:
        logging.error(f"Ошибка вставки демо-данных: {e}")
        conn.rollback()
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

def check_table_exists(conn, table_name: str) -> bool:
    """Проверяет, существует ли таблица"""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                (table_name,)
            )
            return cur.fetchone()[0]
    except Exception as e:
        logging.error(f"Ошибка проверки таблицы {table_name}: {e}")
        return False