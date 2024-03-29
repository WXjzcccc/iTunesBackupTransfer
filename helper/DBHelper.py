import sqlite3

class DBHelper:
    def __init__(self,db_path: str):
        db_path = db_path.replace('\\','/').replace('//','/')
        if db_path[-1] != '/':
            db_path += '/'
        self.conn = None
        if db_path.split('/')[-2].startswith('Manifest'):
            self.conn = sqlite3.connect(db_path[:-1])
        else:
            self.conn = sqlite3.connect(db_path+'Manifest.db')
        self.cursor = self.conn.cursor()

    def select(self,sql: str) -> list:
        """
        @sql:       要执行的SQL语句
        """
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows
        
    def close(self) -> None:
        self.cursor.close()
        self.conn.close()