import sqlite3
from pony.orm import db_session, commit
from utils import db, User

# Connect to the current database
conn = sqlite3.connect('zipbot.sqlite')
cursor = conn.cursor()

# Backup the data from the current database
cursor.execute("SELECT uid, status FROM User")
users = cursor.fetchall()

# Create a new database with the updated schema
db.bind(provider='sqlite', filename='zipbot_new.sqlite', create_db=True)
db.generate_mapping(create_tables=True)

with db_session:
    for uid, status in users:
        User(uid=uid, status=status, files=[])  # Initialize files with an empty list
    commit()

# Replace the old database file with the new one
conn.close()
import os
os.rename('zipbot.sqlite', 'zipbot_old.sqlite')
os.rename('zipbot_new.sqlite', 'zipbot.sqlite') 
