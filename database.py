# database.py
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