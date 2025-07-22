import sqlite3
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Stamp:
    time: datetime
    stamper: str
    sid: int
    sname: str
    stype: str
    status: str


db_name = "db.db"
p = Path('.')

db_con = sqlite3.connect("db.db")
db_cur = db_con.cursor()
if db_name not in p:
    db_cur.execute("CREATE TABLE stamp(time, stamper, sid, sname, stype, status)")

db_con.close()
