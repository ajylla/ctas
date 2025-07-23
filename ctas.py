import sqlite3
import json
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

    # Enforce correct field types.
    def __post_init__(self):
        for (item, typ) in self.__annotations__.items():
            if not isinstance(self.__dict__[item], typ):
                current_t = type(self.__dict__[item])
                raise TypeError(f"{item} needs to be of type {typ}, not {current_t}.")


def write_stamp(stamp, db_cur) -> None:
    data = [stamp.time, stamp.stamper, stamp.sid,
            stamp.sname, stamp.stype, stamp.status]
    db_cur.execute("INSERT INTO stamp(?, ?, ?, ?, ?, ?)", data)


def db_init():
    db_name = "db.db"
    p = Path(f"./{db_name}")

    db_exists = p.exists()
    db_con = sqlite3.connect(db_name)
    db_cur = db_con.cursor()

    if not db_exists:
        db_cur.execute("CREATE TABLE stamp(time, stamper, sid, sname, stype, status)")

    return db_con, db_cur


if __name__ == "__main__":
    db_con, db_cur = db_init()
    db_con.close()
