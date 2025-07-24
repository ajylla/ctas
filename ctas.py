import sqlite3
import json
import configparser
from string import ascii_lowercase
from random import choice
from hashlib import sha1
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Stamp:
    uid: str
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


def write_stamp(stamp):
    data = [stamp.uid, stamp.time, stamp.stamper, stamp.sid,
            stamp.sname, stamp.stype, stamp.status]
    db_cur.execute("INSERT INTO stamp VALUES(?, ?, ?, ?, ?, ?, ?)", data)
    db_con.commit()


def status_callback(args):
    print(db_cur.execute("SELECT * FROM stamp").fetchall())


def stamp_callback(args):
    # Main argument can be either name or ID of stamp,
    # so we check for this, and also that this stamp
    # is found in the stamps.json file.
    try:
        sid = int(args.stamp)
        sname = next((s['sname'] for s in stamps if s['sid'] == sid), None)
    except ValueError:
        sname = args.stamp
        sid = next((s['sid'] for s in stamps if s['sname'] == sname), None)
    if sid is None:
        raise ValueError(f"{args.stamp} is not a valid stamp name.")
    if sname is None:
        raise ValueError(f"{args.stamp} is not a valid stamp ID.")

    time = datetime.now()
    salt = "".join(choice(ascii_lowercase) for i in range(10))
    uid = sha1(b"{time.isoformat()}{salt}").hexdigest()
    stamper = args.stamper if args.stamper else config["User"]["Stamper"]
    stype = next((s['stype'] for s in stamps if s['sid'] == sid))
    status = "not-accepted"
    stamp = Stamp(uid, time, stamper,
                  sid, sname, stype, status)

    write_stamp(stamp)


# Read config
config = configparser.ConfigParser()
config.read("config.ini")

with open(config["Paths"]["StampsPath"]) as f:
    stamps = json.load(f)['stamps']

# Init database
db_path = Path(config["Paths"]["DBPath"])
db_exists = db_path.exists()
db_con = sqlite3.connect(db_path)
db_cur = db_con.cursor()

# sqlite3.connect() creates the db if it does not exists,
# so we check the existance before connection.
if not db_exists:
    db_cur.execute("CREATE TABLE stamp(uid, time, stamper, sid, sname, stype, status)")

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
    parser_stamp.add_argument("stamp", help="Name or ID of the stamp")
    parser_stamp.add_argument("--stamper", type=str)
    parser_stamp.set_defaults(func=stamp_callback)

    args = parser.parse_args()
    args.func(args)

    db_con.close()
