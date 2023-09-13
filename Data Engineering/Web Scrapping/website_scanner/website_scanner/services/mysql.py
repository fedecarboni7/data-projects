import mysql.connector
from mysql.connector import pooling
import sys
from datetime import datetime

class DatabasePool(object):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def setConfig(self, config):
        self.config = config

    def get_pool(self, pool_size: int) :
        return pooling.MySQLConnectionPool(
            pool_name = 'DatabasePool',
            pool_size = pool_size,
            **self.config
            )

    def get_single_connection(self):
        return mysql.connector.connect(**self.config)
    
def get_proxies():
    obj = DatabasePool()
    conn = obj.get_single_connection()
    cursor = conn.cursor(buffered=True)

    cursor.execute(f'SELECT url FROM proxy ORDER BY RAND()')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    proxies = [ row[0] for row in rows]
    
    return proxies

def notify_process(process_category:str,  process_key:str, affected_tables: str, status: str, details: str):
    obj = DatabasePool()
    conn = obj.get_single_connection()
    cursor = conn.cursor(buffered=True)
    today = datetime.now()

    cursor.execute(f'SELECT * FROM di_process WHERE process_group=%s and process=%s',[process_category, process_key])
    row = cursor.fetchone()

    if row == None :
        cursor.execute(f'INSERT INTO di_process (process_group, process, affected_tables, status, details) VALUES (%s, %s, %s, %s, %s)',
                       [process_category, process_key, affected_tables, status, details])

        
    else :
        cursor.execute(f'UPDATE di_process SET affected_tables=%s, status=%s, details=%s, last_execution_date=%s WHERE process_group=%s and process=%s',
                       [affected_tables, status, details, today, process_category, process_key])

    conn.commit()
    cursor.close()
    conn.close()
