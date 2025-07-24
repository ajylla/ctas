import sqlite3
import json
import configparser
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


def status_callback(args):
    print("Status!")


def stamp_callback(args):
    print(f"Stamped: {args.name}")


# Read config
config = configparser.ConfigParser()
config.read("config.ini")

# Init database
db_path = Path(config["Paths"]["DBPath"])
db_exists = db_path.exists()
db_con = sqlite3.connect(db_path)
db_cur = db_con.cursor()
if not db_exists:
    db_cur.execute("CREATE TABLE stamp(time, stamper, sid, sname, stype, status)")

del db_exists


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="CTAS")
    subparsers = parser.add_subparsers()

    # 'status' subcommand
    parser_status = subparsers.add_parser("status")
    parser_status.set_defaults(func=status_callback)

    # 'stamp' subcommand
    parser_stamp = subparsers.add_parser("stamp")
    parser_stamp.add_argument("name", type=str, help="Name of the stamp")
    parser_stamp.set_defaults(func=stamp_callback)

    args = parser.parse_args()
    args.func(args)

    db_con.close()
