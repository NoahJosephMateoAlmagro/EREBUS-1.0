SCHEMA_SQL = """
        /* ------------------------
        -- Executions
        -- ------------------------*/

        CREATE TABLE IF NOT EXISTS EXECUTIONS (
            id TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT NOT NULL
        );


        /* ------------------------
        -- Discovered domains
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS DOMAIN_RESULTS (
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
        -- Resolved domains (DNS)
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS RESOLVED_DOMAIN_RESULTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            ip TEXT NOT NULL,
            source TEXT,
            UNIQUE (execution_id, domain, ip),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS DNS_OBSERVATIONS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Execution context
            execution_id TEXT NOT NULL,
            domain TEXT NOT NULL,

            -- DNS observation
            record_type TEXT NOT NULL,        -- NS | CNAME
            record_value TEXT NOT NULL,       -- normalized target

            -- Source
            source TEXT,
            technique TEXT,

            -- OSINT enrichment
            provider TEXT,                   -- AWS | Azure | Cloudflare | Unknown
            target_resolvable INTEGER,       -- 1 | 0 | NULL
            exposure_level TEXT,             -- NONE | LOW | MEDIUM | HIGH

            UNIQUE(execution_id, domain, record_type, record_value),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        -- HTTP headers
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS HTTP_HEADERS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            url TEXT NOT NULL,
            header TEXT NOT NULL,
            value TEXT,
            category TEXT NOT NULL,      -- security | tech
            status TEXT,
            exposure_level TEXT,         -- NONE | LOW | MEDIUM | HIGH
            description TEXT,
            UNIQUE(execution_id, domain, url, header),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        -- WHOIS
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS WHOIS_RESULTS (
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
        -- Emails (unified)
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS EMAIL_RESULTS (
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
        -- Crawler results (debug / traceability)
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS CRAWLER_RESULTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            url TEXT,
            emails TEXT,
            links TEXT,
            scripts TEXT,
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        -- JS results (debug / traceability)
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS JS_RESULTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            script_url TEXT,
            emails TEXT,
            urls TEXT,
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        -- Exposed credentials
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS CREDENTIAL_RESULTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            type TEXT,
            value TEXT,
            technique TEXT,
            source TEXT,
            context TEXT,
            UNIQUE (execution_id, type, value),
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        -- Nmap results
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS NMAP_RESULTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL,
            ip TEXT NOT NULL,
            port INTEGER NOT NULL,
            protocol TEXT,
            state TEXT,
            service TEXT,
            product TEXT,
            version TEXT,
            source TEXT,
            FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE
        );

        /* ------------------------
        -- API credentials
        -- ------------------------*/
        CREATE TABLE IF NOT EXISTS API_CREDENTIALS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            api_key TEXT NOT NULL,
            extra TEXT,
            description TEXT,
            enabled INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider, api_key)
        );

        /* ------------------------
        -- Indexes
        -- ------------------------*/

        CREATE INDEX IF NOT EXISTS IDX_EMAIL_EXECUTION
        ON email_results (execution_id);

        CREATE INDEX IF NOT EXISTS IDX_EMAIL_VALUE
        ON email_results (email);

        CREATE INDEX IF NOT EXISTS IDX_DOMAIN_EXECUTION
        ON domain_results (execution_id);

        CREATE INDEX IF NOT EXISTS IDX_DOMAIN_VALUE
        ON domain_results (domain);

        CREATE INDEX IF NOT EXISTS IDX_DNS_EXECUTION
        ON dns_observations (execution_id);

        CREATE INDEX IF NOT EXISTS IDX_DNS_DOMAIN
        ON dns_observations (domain);

        CREATE INDEX IF NOT EXISTS IDX_NMAP_EXECUTION
        ON nmap_results (execution_id);

        CREATE INDEX IF NOT EXISTS IDX_HEADERS_EXECUTION
        ON http_headers (execution_id);

        CREATE INDEX IF NOT EXISTS IDX_CREDENTIALS_EXECUTION
        ON credential_results (execution_id);
"""