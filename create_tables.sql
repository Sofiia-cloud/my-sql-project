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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
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
    target_ports INTEGER[],
    detected_by_model_id INTEGER,
    
   
    CONSTRAINT fk_detected_by_model 
        FOREIGN KEY (detected_by_model_id) 
        REFERENCES ai_models(model_id)
        ON DELETE SET NULL  
        ON UPDATE CASCADE,  

    CONSTRAINT chk_valid_ip_addresses 
        CHECK (source_ip ~ '^[0-9a-fA-F\.:]+$'), 
    
    CONSTRAINT chk_duration_reasonable 
        CHECK (duration_seconds <= 86400)  
);