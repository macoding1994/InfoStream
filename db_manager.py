from queue import Queue
from threading import Lock

import pymysql
from pymysql import cursors, Error
from config import DB_CONFIG


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
    def __init__(self):
        self._pool = Queue(maxsize=5)
        self._lock = Lock()
        for _ in range(5):
            self._pool.put(self._create_connection())

    def _create_connection(self):
        # First try to connect to the database
        try:
            return pymysql.connect(
                cursorclass=cursors.DictCursor,
                **DB_CONFIG
            )
        except pymysql.err.OperationalError as e:
            if e.args[0] == 1049:  # Unknown database error
                # Connect without database specified
                temp_config = DB_CONFIG.copy()
                temp_config.pop('database')
                temp_conn = pymysql.connect(**temp_config)

                try:
                    with temp_conn.cursor() as cursor:
                        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} "
                                       f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                        temp_conn.commit()

                    # Now try to connect again with database
                    conn = pymysql.connect(
                        cursorclass=cursors.DictCursor,
                        **DB_CONFIG
                    )

                    # Create tables if not exists
                    with conn.cursor() as cursor:
                        # Create feeds table
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

                        conn.commit()
                    # Create tables if not exists
                    with conn.cursor() as cursor:

                        # Create keyword table
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS keyword (
                                feed_id INT NOT NULL,
                                keyword VARCHAR(255) NOT NULL,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                                
                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                        """)
                        conn.commit()

                    return conn
                finally:
                    temp_conn.close()
            raise  # Re-raise other errors

    def get_connection(self):
        try:
            with self._lock:
                return self._pool.get()
        except Error as e:
            print(f"Error getting database connection: {e}")
            raise

    def execute_query(self, query, params=None, fetch=False, return_last_id=False):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if fetch:
                return cursor.fetchall()

            conn.commit()

            if return_last_id:
                return cursor.lastrowid  # ✅ 返回自增主键 ID
            return cursor.rowcount  # 默认返回影响行数

        except Error as e:
            if conn:
                conn.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._pool.put(conn)


if __name__ == '__main__':
    initialize_database()
