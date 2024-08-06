from flask import g
import sqlite3
import os


def connect_db():
    current_path = os.getcwd()
    db_name = "questions.db"
    sql = sqlite3.connect(f"{current_path}/{db_name}")
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
