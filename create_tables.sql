
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


