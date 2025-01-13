import sqlite3
import os
import sys
from db_crud import connect_to_db

conn = connect_to_db()
cursor = conn.cursor()

# write sql command
command1 = """
    CREATE TABLE IF NOT EXISTS stock(
        id INTEGER PRIMARY KEY,
        sec_code TEXT NOT NULL,
        sec_name TEXT NOT NULL,
        exchange TEXT
    )
"""

command2 = """
    CREATE TABLE IF NOT EXISTS stock_price(
        id INTEGER PRIMARY KEY,
        stock_id INTEGER,
        date NOT NULL,
        open NOT NULL,
        high NOT NULL,
        low NOT NULL,
        close NOT NULL,
        volume NOT NULL,
        turnover REAL,
        FOREIGN KEY (stock_id) REFERENCES stock (id)
    )
"""

command3 = """
    CREATE TABLE IF NOT EXISTS strategy(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT
    )
"""

command4 = """
    CREATE TABLE IF NOT EXISTS stock_strategy(
        stock_id INTEGER,
        strategy_id INTEGER,
        FOREIGN KEY (stock_id) REFERENCES stock (id),
        FOREIGN KEY (strategy_id) REFERENCES strategy (id),
        PRIMARY KEY (stock_id,strategy_id)
    )
"""


commands = [command3,command4]
for command in commands:
    cursor.execute(command)
    conn.commit()