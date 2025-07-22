import sqlite3
from pathlib import Path


db_name = "db.db"
p = Path('.')

db_con = sqlite3.connect("db.db")
db_cur = db_con.cursor()
if db_name not in p:
    db_cur.execute("CREATE TABLE stamp(time, stamper, sid, sname, type, status)")


db_con.close()
