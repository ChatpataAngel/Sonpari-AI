#!/usr/bin/env python3
"""Create/validate/restore an AIKO SQLite backup. Stop the bot before restore."""
import argparse
from aiko.backup import create_backup, restore_backup, validate_sqlite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    backup = subs.add_parser("backup"); backup.add_argument("database"); backup.add_argument("--dir"); backup.add_argument("--keep", type=int, default=7)
    validate = subs.add_parser("validate"); validate.add_argument("backup")
    restore = subs.add_parser("restore"); restore.add_argument("backup"); restore.add_argument("database")
    args = parser.parse_args()
    if args.action == "backup":
        print(create_backup(args.database, args.dir, args.keep))
    elif args.action == "validate":
        ok, message = validate_sqlite(args.backup); print(f"{'OK' if ok else 'INVALID'}: {message}"); raise SystemExit(0 if ok else 1)
    else:
        print(restore_backup(args.backup, args.database))
        print("Restore complete. Start the bot and inspect startup logs.")

if __name__ == "__main__": main()
