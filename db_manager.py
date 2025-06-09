from queue import Queue
from threading import Lock

import pymysql
from pymysql import cursors, Error
from config import DB_CONFIG, SLAVE_DB_CONFIG


def initialize_database():
    """
    Create the database and required tables if they do not exist.
    """
    try:
        # Try to connect to the target database
        conn = pymysql.connect(cursorclass=cursors.DictCursor, **DB_CONFIG)
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1049:  # Unknown database error
            # Connect without database name to create the database
            temp_config = DB_CONFIG.copy()
            temp_config.pop('database')
            conn = pymysql.connect(**temp_config)
            try:
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} \
                                     DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    conn.commit()
            finally:
                conn.close()
            # Reconnect to the new database
            conn = pymysql.connect(cursorclass=cursors.DictCursor, **DB_CONFIG)
        else:
            raise

    # Create tables
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feeds (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url VARCHAR(512) NOT NULL UNIQUE,
                    title VARCHAR(255),
                    description TEXT,
                    last_fetched_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_tagged BOOLEAN DEFAULT FALSE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword (
                    feed_id INT NOT NULL,
                    keyword VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (feed_id, keyword)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            conn.commit()
    finally:
        conn.close()


class DatabaseManager:
    def __init__(self, use_slave=True):
        self._pool = Queue(maxsize=5)
        self._lock = Lock()
        self.use_slave = use_slave
        for _ in range(5):
            self._pool.put(self._create_connection())

    def _create_connection(self):
        config = SLAVE_DB_CONFIG if self.use_slave else DB_CONFIG
        return pymysql.connect(cursorclass=cursors.DictCursor, **config)

    def execute_query(self, query, params=None, fetch=False, return_lastrowid=False):
        conn = self._pool.get()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                else:
                    conn.commit()
                    if return_lastrowid:
                        return cursor.lastrowid
        finally:
            self._pool.put(conn)


if __name__ == '__main__':
    initialize_database()
