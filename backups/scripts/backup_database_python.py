#!/usr/bin/env python3
"""
Python-based database backup using psycopg2 (no pg_dump required)
Works on Windows without PostgreSQL client tools installed
"""

import os
import sys
import json
import gzip
import logging
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from backup_config import DATABASE_CONFIG, LOCAL_PATHS, SCHEMAS_TO_BACKUP

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("backup_python")


def get_connection():
    """Create database connection using psycopg2"""
    import psycopg2

    conn = psycopg2.connect(
        host=DATABASE_CONFIG['host'],
        port=DATABASE_CONFIG['port'],
        dbname=DATABASE_CONFIG['database'],
        user=DATABASE_CONFIG['user'],
        password=DATABASE_CONFIG['password'],
        sslmode='require'
    )
    return conn


def backup_table_data(cursor, schema: str, table: str) -> list:
    """Export table data as INSERT statements"""
    cursor.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table))

    columns = cursor.fetchall()
    if not columns:
        return []

    column_names = [c[0] for c in columns]
    column_list = ', '.join(f'"{c}"' for c in column_names)

    cursor.execute(f'SELECT * FROM "{schema}"."{table}"')
    rows = cursor.fetchall()

    statements = []
    for row in rows:
        values = []
        for i, val in enumerate(row):
            if val is None:
                values.append('NULL')
            elif isinstance(val, (int, float)):
                values.append(str(val))
            elif isinstance(val, bool):
                values.append('TRUE' if val else 'FALSE')
            elif isinstance(val, (dict, list)):
                # JSON/JSONB
                json_str = json.dumps(val).replace("'", "''")
                values.append(f"'{json_str}'")
            elif isinstance(val, datetime):
                values.append(f"'{val.isoformat()}'")
            else:
                # Escape single quotes
                str_val = str(val).replace("'", "''")
                values.append(f"'{str_val}'")

        values_str = ', '.join(values)
        statements.append(f'INSERT INTO "{schema}"."{table}" ({column_list}) VALUES ({values_str});')

    return statements


def backup_table_schema(cursor, schema: str, table: str) -> str:
    """Get CREATE TABLE statement"""
    # Get columns
    cursor.execute(f"""
        SELECT column_name, data_type, character_maximum_length,
               column_default, is_nullable, udt_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table))

    columns = cursor.fetchall()
    if not columns:
        return ""

    col_defs = []
    for col in columns:
        name, dtype, max_len, default, nullable, udt = col

        # Build column type
        if dtype == 'character varying':
            col_type = f'VARCHAR({max_len})' if max_len else 'VARCHAR'
        elif dtype == 'USER-DEFINED':
            col_type = udt.upper()
        elif dtype == 'ARRAY':
            col_type = f'{udt}[]'
        else:
            col_type = dtype.upper()

        col_def = f'    "{name}" {col_type}'

        if default:
            col_def += f' DEFAULT {default}'
        if nullable == 'NO':
            col_def += ' NOT NULL'

        col_defs.append(col_def)

    # Get primary key
    cursor.execute(f"""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema = %s
            AND tc.table_name = %s
            AND tc.constraint_type = 'PRIMARY KEY'
    """, (schema, table))

    pk_cols = [r[0] for r in cursor.fetchall()]
    if pk_cols:
        pk_str = ', '.join(f'"{c}"' for c in pk_cols)
        col_defs.append(f'    PRIMARY KEY ({pk_str})')

    cols_str = ',\n'.join(col_defs)
    return f'CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (\n{cols_str}\n);'


def run_backup(backup_type: str = "daily") -> Path:
    """Run full database backup"""
    import psycopg2

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = LOCAL_PATHS[backup_type]
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use .sql.gz for compressed SQL dump
    output_file = output_dir / f"backup_{timestamp}_{backup_type}.sql.gz"

    logger.info(f"Starting Python-based {backup_type} backup...")
    logger.info(f"Schemas: {', '.join(SCHEMAS_TO_BACKUP)}")
    logger.info(f"Output: {output_file}")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        all_statements = []
        all_statements.append(f"-- Backup created: {datetime.now().isoformat()}")
        all_statements.append(f"-- Schemas: {', '.join(SCHEMAS_TO_BACKUP)}")
        all_statements.append("")

        for schema in SCHEMAS_TO_BACKUP:
            logger.info(f"Backing up schema: {schema}")
            all_statements.append(f"\n-- Schema: {schema}")
            all_statements.append(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')
            all_statements.append("")

            # Get all tables in schema
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema,))

            tables = [r[0] for r in cursor.fetchall()]
            logger.info(f"  Found {len(tables)} tables")

            for table in tables:
                all_statements.append(f"\n-- Table: {schema}.{table}")

                # Schema
                schema_sql = backup_table_schema(cursor, schema, table)
                if schema_sql:
                    all_statements.append(schema_sql)

                # Data
                data_sql = backup_table_data(cursor, schema, table)
                if data_sql:
                    all_statements.extend(data_sql)
                    logger.info(f"    {table}: {len(data_sql)} rows")

        cursor.close()
        conn.close()

        # Write compressed output
        sql_content = '\n'.join(all_statements)
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            f.write(sql_content)

        size_mb = output_file.stat().st_size / (1024 * 1024)
        logger.info(f"Backup complete: {output_file.name} ({size_mb:.2f} MB)")

        return output_file

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Python-based database backup")
    parser.add_argument("--type", choices=["daily", "weekly"], default="daily")
    args = parser.parse_args()

    try:
        output_file = run_backup(args.type)
        print(f"\nBackup successful: {output_file}")
        return 0
    except Exception as e:
        print(f"\nBackup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
