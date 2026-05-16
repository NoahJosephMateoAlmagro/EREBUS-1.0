"""
Data table metadata for the EREBUS presentation layer.

This module centralizes column display metadata used by the Data page table,
including column widths, alignment rules, semantic column groups and
table-specific rendering limits.
"""


class DataTableMetadata:
    """
    Static metadata used to render database tables.
    """

    DEFAULT_COLUMN_WIDTH = 170
    MAX_COLUMN_WIDTH = 360
    DEFAULT_MAX_CELL_LENGTH = 220

    COLUMN_MIN_WIDTHS = {
        "id": 72,
        "execution_id": 190,
        "target": 170,
        "domain": 190,
        "ip": 150,
        "url": 260,
        "script_url": 300,
        "source_url": 260,
        "page_url": 260,
        "source": 150,
        "status": 130,
        "mx_records": 150,
        "mail_provider": 170,
        "spf_policy": 170,
        "external_services": 210,
        "record_type": 150,
        "record_value": 210,
        "provider": 140,
        "target_resolvable": 170,
        "exposure_level": 150,
        "technique": 150,
        "header": 190,
        "value": 220,
        "category": 130,
        "description": 260,
        "registrar": 190,
        "creation_date": 150,
        "expiration_date": 150,
        "updated_date": 150,
        "name_servers": 230,
        "emails": 230,
        "email": 220,
        "raw_text": 300,
        "context": 280,
        "links": 320,
        "scripts": 320,
        "urls": 320,
        "type": 120,
        "port": 90,
        "protocol": 110,
        "state": 120,
        "service": 150,
        "product": 170,
        "version": 170,
        "start_time": 160,
        "end_time": 160,
        "created_at": 160,
    }

    COLUMN_MAX_WIDTHS = {
        "id": 260,
        "execution_id": 260,
        "target": 260,
        "domain": 320,
        "ip": 260,
        "url": 620,
        "script_url": 760,
        "source_url": 620,
        "page_url": 620,
        "source": 320,
        "status": 180,
        "mx_records": 300,
        "mail_provider": 240,
        "spf_policy": 280,
        "external_services": 360,
        "record_type": 190,
        "record_value": 420,
        "provider": 220,
        "target_resolvable": 220,
        "exposure_level": 220,
        "technique": 240,
        "header": 280,
        "value": 520,
        "category": 180,
        "description": 620,
        "registrar": 280,
        "creation_date": 190,
        "expiration_date": 190,
        "updated_date": 190,
        "name_servers": 520,
        "emails": 520,
        "email": 380,
        "raw_text": 680,
        "context": 680,
        "links": 900,
        "scripts": 900,
        "urls": 900,
        "type": 180,
        "port": 120,
        "protocol": 150,
        "state": 160,
        "service": 220,
        "product": 320,
        "version": 320,
        "start_time": 210,
        "end_time": 210,
        "created_at": 210,
    }

    TABLE_COLUMN_MIN_WIDTHS = {
        "executions": {
            "id": 240,
            "target": 180,
            "start_time": 180,
            "end_time": 180,
            "status": 160,
        },
        "domain_results": {
            "id": 80,
            "execution_id": 220,
            "domain": 240,
            "source": 220,
            "status": 170,
            "mx_records": 220,
        },
        "resolved_domain_results": {
            "id": 80,
            "execution_id": 220,
            "domain": 240,
            "ip": 210,
            "source": 180,
        },
        "dns_observations": {
            "id": 80,
            "execution_id": 220,
            "domain": 240,
            "record_type": 150,
            "record_value": 280,
            "source": 220,
            "technique": 190,
            "provider": 180,
        },
        "http_headers": {
            "id": 80,
            "execution_id": 220,
            "domain": 220,
            "url": 420,
            "header": 240,
            "value": 360,
            "description": 420,
        },
        "whois_results": {
            "id": 80,
            "execution_id": 220,
            "domain": 220,
            "registrar": 240,
            "name_servers": 360,
            "emails": 340,
            "raw_text": 460,
        },
        "email_results": {
            "id": 80,
            "execution_id": 220,
            "email": 260,
            "domain": 240,
            "technique": 190,
            "source": 320,
            "context": 420,
        },
        "crawler_results": {
            "id": 80,
            "execution_id": 220,
            "url": 760,
            "emails": 360,
            "links": 900,
            "scripts": 900,
        },
        "js_results": {
            "id": 80,
            "execution_id": 220,
            "script_url": 900,
            "emails": 360,
            "urls": 900,
        },
        "credential_results": {
            "id": 80,
            "execution_id": 220,
            "type": 160,
            "value": 420,
            "technique": 190,
            "source": 420,
            "context": 520,
        },
        "nmap_results": {
            "id": 80,
            "execution_id": 220,
            "ip": 210,
            "port": 110,
            "protocol": 130,
            "state": 140,
            "service": 180,
            "product": 240,
            "version": 240,
            "source": 180,
        },
    }

    TABLE_COLUMN_MAX_WIDTHS = {
        "executions": {
            "id": 300,
            "target": 260,
            "start_time": 220,
            "end_time": 220,
            "status": 180,
        },
        "domain_results": {
            "execution_id": 280,
            "domain": 340,
            "source": 300,
            "status": 200,
            "mx_records": 340,
        },
        "resolved_domain_results": {
            "execution_id": 280,
            "domain": 340,
            "ip": 300,
            "source": 260,
        },
        "dns_observations": {
            "execution_id": 280,
            "domain": 340,
            "record_value": 460,
            "source": 320,
            "technique": 260,
            "provider": 240,
        },
        "http_headers": {
            "execution_id": 280,
            "domain": 320,
            "url": 760,
            "header": 340,
            "value": 620,
            "description": 760,
        },
        "whois_results": {
            "execution_id": 280,
            "domain": 320,
            "registrar": 340,
            "name_servers": 620,
            "emails": 620,
            "raw_text": 760,
        },
        "email_results": {
            "execution_id": 280,
            "email": 420,
            "domain": 340,
            "technique": 260,
            "source": 520,
            "context": 760,
        },
        "crawler_results": {
            "execution_id": 280,
            "url": 1000,
            "emails": 620,
            "links": 1200,
            "scripts": 1200,
        },
        "js_results": {
            "execution_id": 280,
            "script_url": 1200,
            "emails": 620,
            "urls": 1200,
        },
        "credential_results": {
            "execution_id": 280,
            "value": 620,
            "source": 620,
            "context": 760,
        },
        "nmap_results": {
            "execution_id": 280,
            "ip": 300,
            "product": 340,
            "version": 340,
        },
    }

    TABLE_CELL_LENGTHS = {
        "crawler_results": {
            "url": 420,
            "links": 700,
            "scripts": 700,
            "emails": 360,
        },
        "js_results": {
            "script_url": 700,
            "urls": 700,
            "emails": 360,
        },
        "http_headers": {
            "url": 420,
            "value": 420,
            "description": 420,
        },
        "whois_results": {
            "raw_text": 500,
            "name_servers": 400,
            "emails": 360,
        },
        "credential_results": {
            "value": 420,
            "context": 500,
            "source": 420,
        },
    }

    COLUMN_CELL_LENGTHS = {
        "url": 420,
        "script_url": 500,
        "source_url": 420,
        "page_url": 420,
        "urls": 500,
        "links": 500,
        "scripts": 500,
        "raw_text": 500,
        "context": 420,
        "description": 420,
        "value": 360,
        "emails": 320,
        "name_servers": 320,
    }

    CENTERED_COLUMNS = {
        "id",
        "port",
        "protocol",
        "state",
        "status",
        "category",
        "record_type",
        "target_resolvable",
        "exposure_level",
        "enabled",
    }

    DATETIME_COLUMNS = {
        "start_time",
        "end_time",
        "creation_date",
        "expiration_date",
        "updated_date",
        "created_at",
    }

    IDENTIFIER_COLUMNS = {
        "id",
        "execution_id",
    }

    DOMAIN_COLUMNS = {
        "target",
        "domain",
        "host",
        "hostname",
        "email",
    }

    URL_COLUMNS = {
        "url",
        "script_url",
        "source_url",
        "page_url",
        "urls",
    }

    IP_COLUMNS = {
        "ip",
    }

    LARGE_TEXT_COLUMNS = {
        "raw_text",
        "context",
        "description",
        "links",
        "scripts",
        "emails",
        "name_servers",
        "value",
        "external_services",
        "mx_records",
        "urls",
    }

    MULTILINE_COLUMNS = {
        "url",
        "script_url",
        "source_url",
        "page_url",
        "urls",
        "links",
        "scripts",
        "raw_text",
        "context",
        "description",
        "value",
        "emails",
        "name_servers",
    }

    @classmethod
    def get_min_width(cls, column_name: str, table_name: str | None = None) -> int:
        """
        Gets the minimum display width for a column.

        Args:
            column_name: Database column name.
            table_name: Optional database table name.

        Returns:
            int: Minimum column width.
        """
        table_widths = cls.TABLE_COLUMN_MIN_WIDTHS.get(table_name or "", {})

        if column_name in table_widths:
            return table_widths[column_name]

        return cls.COLUMN_MIN_WIDTHS.get(column_name, cls.DEFAULT_COLUMN_WIDTH)

    @classmethod
    def get_max_width(cls, column_name: str, table_name: str | None = None) -> int:
        """
        Gets the maximum display width for a column.

        Args:
            column_name: Database column name.
            table_name: Optional database table name.

        Returns:
            int: Maximum column width.
        """
        table_widths = cls.TABLE_COLUMN_MAX_WIDTHS.get(table_name or "", {})

        if column_name in table_widths:
            return table_widths[column_name]

        return cls.COLUMN_MAX_WIDTHS.get(column_name, cls.MAX_COLUMN_WIDTH)

    @classmethod
    def get_max_cell_length(
        cls,
        column_name: str,
        table_name: str | None = None,
        default_length: int | None = None,
    ) -> int:
        """
        Gets the maximum amount of text loaded into a cell preview.

        Args:
            column_name: Database column name.
            table_name: Optional database table name.
            default_length: Fallback length.

        Returns:
            int: Maximum cell text length.
        """
        table_lengths = cls.TABLE_CELL_LENGTHS.get(table_name or "", {})

        if column_name in table_lengths:
            return table_lengths[column_name]

        if column_name in cls.COLUMN_CELL_LENGTHS:
            return cls.COLUMN_CELL_LENGTHS[column_name]

        if default_length is not None:
            return default_length

        return cls.DEFAULT_MAX_CELL_LENGTH

    @classmethod
    def get_max_lines(cls, column_name: str, table_name: str | None = None) -> int:
        """
        Gets the maximum number of visual lines for a column.

        Args:
            column_name: Database column name.
            table_name: Optional database table name.

        Returns:
            int: Maximum number of visual lines.
        """
        if table_name in {"crawler_results", "js_results"}:
            if column_name in {"url", "script_url", "urls", "links", "scripts"}:
                return 4

        if column_name in cls.MULTILINE_COLUMNS:
            return 3

        return 2

    @classmethod
    def is_centered(cls, column_name: str) -> bool:
        """
        Checks whether a column should use centered text.

        Args:
            column_name: Database column name.

        Returns:
            bool: True if the column should be centered.
        """
        return column_name in cls.CENTERED_COLUMNS

    @classmethod
    def is_datetime(cls, column_name: str) -> bool:
        """
        Checks whether a column stores datetime-like values.

        Args:
            column_name: Database column name.

        Returns:
            bool: True if the column should be formatted as datetime.
        """
        return column_name in cls.DATETIME_COLUMNS

    @classmethod
    def is_identifier(cls, column_name: str) -> bool:
        """
        Checks whether a column stores identifier-like values.

        Args:
            column_name: Database column name.

        Returns:
            bool: True if the column stores identifiers.
        """
        return column_name in cls.IDENTIFIER_COLUMNS

    @classmethod
    def is_domain(cls, column_name: str) -> bool:
        """
        Checks whether a column stores domain-like values.

        Args:
            column_name: Database column name.

        Returns:
            bool: True if the column stores domain-like values.
        """
        return column_name in cls.DOMAIN_COLUMNS

    @classmethod
    def is_url(cls, column_name: str) -> bool:
        """
        Checks whether a column stores URL-like values.

        Args:
            column_name: Database column name.

        Returns:
            bool: True if the column stores URL-like values.
        """
        return column_name in cls.URL_COLUMNS

    @classmethod
    def is_ip(cls, column_name: str) -> bool:
        """
        Checks whether a column stores IP-like values.

        Args:
            column_name: Database column name.

        Returns:
            bool: True if the column stores IP-like values.
        """
        return column_name in cls.IP_COLUMNS

    @classmethod
    def is_large_text(cls, column_name: str) -> bool:
        """
        Checks whether a column stores long text.

        Args:
            column_name: Database column name.

        Returns:
            bool: True if the column stores long text.
        """
        return column_name in cls.LARGE_TEXT_COLUMNS

    @classmethod
    def is_multiline(cls, column_name: str) -> bool:
        """
        Checks whether a column benefits from additional visual lines.

        Args:
            column_name: Database column name.

        Returns:
            bool: True if the column can use more than two lines.
        """
        return column_name in cls.MULTILINE_COLUMNS