
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


CREATE TABLE IF NOT EXISTS experiments (
    experiment_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    total_attacks INTEGER CHECK (total_attacks >= 0),
    detected_attacks INTEGER CHECK (detected_attacks >= 0 AND detected_attacks <= total_attacks),
    model_id INTEGER REFERENCES ai_models(model_id) ON DELETE SET NULL
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