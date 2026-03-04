SCHEMA_SQL = """
        /* ------------------------
        # Ejecuciones
        # ------------------------*/

        CREATE TABLE IF NOT EXISTS executions (
            id TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT NOT NULL
        );


        /* ------------------------
        # Dominios descubiertos
        # ------------------------*/
        CREATE TABLE IF NOT EXISTS domain_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            source TEXT,
            status TEXT NOT NULL,
            mx_records TEXT,
            mail_provider TEXT,
            spf_policy TEXT,
            external_services TEXT,
            UNIQUE (execution_id, domain), 
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        # Dominios resueltos (DNS)
        # ------------------------*/
        CREATE TABLE IF NOT EXISTS resolved_domain_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            ip TEXT NOT NULL,
            source TEXT,
            UNIQUE (execution_id, domain, ip),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS dns_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Contexto de ejecución
            execution_id TEXT NOT NULL,
            domain TEXT NOT NULL,

            -- Observación DNS
            record_type TEXT NOT NULL,        -- NS | CNAME
            record_value TEXT NOT NULL,        -- target normalizado

            -- Origen
            source TEXT,
            technique TEXT,

            -- Enriquecimiento OSINT
            provider TEXT,           -- AWS | Azure | Cloudflare | Unknown
            target_resolvable INTEGER,  -- 1 | 0 | NULL
            exposure_level TEXT,     -- NONE | LOW | MEDIUM | HIGH

            UNIQUE(execution_id, domain, record_type, record_value),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        # CABECERAS
        # ------------------------*/
        CREATE TABLE IF NOT EXISTS http_headers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            url TEXT NOT NULL,
            header TEXT NOT NULL,
            value TEXT,
            category TEXT NOT NULL,   -- security | tech
            status TEXT,              
            exposure_level TEXT,      -- low/medium/high
            description TEXT,
            UNIQUE(execution_id, domain, url, header),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );
        
        /* ------------------------
        # WHOIS
        # ------------------------*/
        CREATE TABLE IF NOT EXISTS whois_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            registrar TEXT,
            creation_date TEXT,
            expiration_date TEXT,
            updated_date TEXT,
            name_servers TEXT,
            status TEXT,
            emails TEXT,
            raw_text TEXT,
            UNIQUE (execution_id, domain),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        # Emails (UNIFICADOS)
        # ------------------------*/
        CREATE TABLE IF NOT EXISTS email_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            email TEXT NOT NULL,
            domain TEXT,
            technique TEXT,
            source TEXT,
            context TEXT,
            UNIQUE (execution_id, email),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        # Resultados del crawler (debug / trazabilidad)
        # ------------------------*/

        CREATE TABLE IF NOT EXISTS crawler_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            url TEXT,
            emails TEXT,
            links TEXT,
            scripts TEXT,
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        # Resultados JS (debug / trazabilidad)
        # ------------------------*/
        CREATE TABLE IF NOT EXISTS js_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            script_url TEXT,
            emails TEXT,
            urls TEXT,
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        # Credenciales expuestas
        # ------------------------*/
        CREATE TABLE IF NOT EXISTS credential_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL ,
            type TEXT,
            value TEXT,
            technique TEXT,
            source TEXT,
            context TEXT,
            UNIQUE (execution_id, type, value),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        # Métricas resumen
        # ------------------------*/
        CREATE TABLE IF NOT EXISTS execution_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            module_name TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(execution_id, module_name, metric_name)
        );
                
        CREATE INDEX IF NOT EXISTS idx_email_execution
        ON email_results (execution_id);
        
        CREATE INDEX IF NOT EXISTS idx_domain_execution
        ON domain_results (execution_id);
        
        CREATE INDEX IF NOT EXISTS idx_dns_execution
        ON dns_observations (execution_id);
"""
