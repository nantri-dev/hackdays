import sqlite3
import os
import time

class LocalStore:
    def __init__(self, db_path="offline_queue.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS fault_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    sensor_idx INTEGER,
                    fault_type TEXT,
                    raw_value REAL,
                    synced BOOLEAN,
                    llm_explanation TEXT
                )
            ''')
            conn.commit()
            
    def queue_event(self, sensor_idx, fault_type, raw_value, fallback_msg):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO fault_events (timestamp, sensor_idx, fault_type, raw_value, synced, llm_explanation)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (time.time(), sensor_idx, fault_type, raw_value, False, fallback_msg))
            conn.commit()
            
    def get_unsynced_events(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM fault_events WHERE synced = 0 ORDER BY timestamp ASC')
            return [dict(row) for row in c.fetchall()]
            
    def mark_synced(self, event_id, real_explanation):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE fault_events 
                SET synced = 1, llm_explanation = ?
                WHERE id = ?
            ''', (real_explanation, event_id))
            conn.commit()
            
    def get_queue_size(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM fault_events WHERE synced = 0')
            return c.fetchone()[0]

    def clear_all(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM fault_events')
            conn.commit()
