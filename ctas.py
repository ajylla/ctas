#!/usr/bin/env python

import sqlite3
import json
import os
import configparser
from string import ascii_lowercase
from random import choice
from hashlib import sha1
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Stamp:
    uid: str
    time: datetime | str
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

        if type(self.time) is str:
            self.time = datetime.fromisoformat(self.time)


def write_stamp(stamp):
    data = [stamp.uid, stamp.time, stamp.stamper, stamp.sid,
            stamp.sname, stamp.stype, stamp.status]
    db_cur.execute("INSERT INTO stamp VALUES(?, ?, ?, ?, ?, ?, ?)", data)
    db_con.commit()


def walk(start, end):
    stamps = db_cur.execute("""SELECT * FROM stamp
                               WHERE time BETWEEN ?
                               AND ?
                               ORDER BY time ASC""", (start.isoformat(sep=' '),
                                                      end.isoformat(sep=' ')))

    clock_running = False
    start_time = None
    worktime = timedelta()
    for s in stamps:
        stamp = Stamp(*s)
        if not clock_running:
            if stamp.stype == "clock-start":
                start_time = stamp.time
                clock_running = True
            else:
                continue
        else:
            if stamp.stype == "clock-stop":
                dt = stamp.time - start_time
                worktime += dt
                clock_running = False
            else:
                continue

    return worktime




def status_callback(args):
    now = datetime.today()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    worktime = walk(start, end)
    print(f"Time worked today: {worktime}")
    working_hours = timedelta(hours=float(config["User"]["DailyHours"]))
    print(f"That's {worktime/working_hours * 100} %")


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


# Environment variable
try:
    path_prefix = os.environ['CTAS_PATH']
except KeyError:
    print("It looks like this is your first time running this program.")
    print("Ask sysadmin (Aleksi) for help with installation.")
    exit()


# Read config
config = configparser.ConfigParser()
config.read(path_prefix+"/config.ini")

with open(path_prefix+'/'+config["Paths"]["StampsPath"]) as f:
    stamps = json.load(f)['stamps']

# Init database
db_path = Path(path_prefix+'/'+config["Paths"]["DBPath"])
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
    parser_status = subparsers.add_parser("status", help="Command to show status",
                                          description="Use this command to show status")
    parser_status.set_defaults(func=status_callback)

    # 'stamp' subcommand
    parser_stamp = subparsers.add_parser("stamp", help="Command to make new stamps",
                                         description="Use this command to create stamps")
    parser_stamp.add_argument("stamp", help="Name or ID of the stamp")
    parser_stamp.add_argument("--stamper", type=str, help="Specify name of stamper")
    parser_stamp.set_defaults(func=stamp_callback)

    args = parser.parse_args()
    args.func(args)

    db_con.close()
