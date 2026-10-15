"""
Database Connection and Initialization Module.
Connects to MySQL Server and initializes the library schema.
"""

import os
import pandas as pd
import mysql.connector
from config import MYSQL_CONFIG, CHARTS_DIR


def get_raw_connection():
    """
    Opens a new connection to the configured MySQL server.
    The database is created automatically if it does not exist yet.
    Raises ConnectionError with an actionable message if the server is
    unreachable or the credentials are wrong.
    """
    server_config = {k: v for k, v in MYSQL_CONFIG.items() if k != "database"}

    try:
        # Connect without a database first so we can create it if missing.
        bootstrap = mysql.connector.connect(**server_config)
        cursor = bootstrap.cursor()
        db_name = MYSQL_CONFIG["database"]
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        bootstrap.commit()
        cursor.close()
        bootstrap.close()
    except mysql.connector.Error as e:
        raise ConnectionError(
            f"Could not connect to MySQL at {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']} "
            f"as user '{MYSQL_CONFIG['user']}' ({e}).\n"
            "Check that the MySQL server is running and that MYSQL_HOST / MYSQL_USER / "
            "MYSQL_PASSWORD are set correctly in your .env file."
        ) from e

    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except mysql.connector.Error as e:
        raise ConnectionError(
            f"Could not open database '{MYSQL_CONFIG['database']}' ({e})."
        ) from e


class Database:
    """Helper wrapper for database queries."""

    @classmethod
    def execute(cls, query: str, params: tuple = None, commit: bool = True):
        """Executes INSERT, UPDATE, DELETE queries and returns lastrowid or rowcount."""
        conn = get_raw_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if commit:
                conn.commit()
            last_id = cursor.lastrowid
            return last_id
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def fetchall(cls, query: str, params: tuple = None):
        """Fetches all rows as a list of tuples."""
        conn = get_raw_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def fetchone(cls, query: str, params: tuple = None):
        """Fetches a single row as a tuple."""
        conn = get_raw_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            return row
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def get_dataframe(cls, query: str, params: tuple = None) -> pd.DataFrame:
        """Loads query results directly into a Pandas DataFrame."""
        conn = get_raw_connection()
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()


def initialize_database():
    """Initializes tables for books, borrowers, and loans."""
    # Ensure charts directory exists
    os.makedirs(CHARTS_DIR, exist_ok=True)

    conn = get_raw_connection()
    cursor = conn.cursor()

    create_books_table = """
    CREATE TABLE IF NOT EXISTS books (
        book_id INT AUTO_INCREMENT PRIMARY KEY,
        isbn VARCHAR(20) NOT NULL UNIQUE,
        title VARCHAR(150) NOT NULL,
        author VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        copies_available INT NOT NULL DEFAULT 1
    ) ENGINE=InnoDB;
    """

    create_borrowers_table = """
    CREATE TABLE IF NOT EXISTS borrowers (
        borrower_id INT AUTO_INCREMENT PRIMARY KEY,
        borrower_name VARCHAR(100) NOT NULL,
        roll_no VARCHAR(50) NOT NULL UNIQUE
    ) ENGINE=InnoDB;
    """

    create_loans_table = """
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INT AUTO_INCREMENT PRIMARY KEY,
        book_id INT NOT NULL,
        borrower_id INT NOT NULL,
        issue_date DATE NOT NULL,
        due_date DATE NOT NULL,
        return_date DATE NULL,
        FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
        FOREIGN KEY (borrower_id) REFERENCES borrowers(borrower_id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """

    cursor.execute(create_books_table)
    cursor.execute(create_borrowers_table)
    cursor.execute(create_loans_table)
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database '{MYSQL_CONFIG['database']}' successfully initialized on MySQL.")