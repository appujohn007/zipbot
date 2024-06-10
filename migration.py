from pony.orm import *

db = Database()

class User(db.Entity):
    uid = PrimaryKey(int, size=64)
    status = Required(int)
    files = Optional(Json)  # Add the files attribute

db.bind(provider='sqlite', filename='zipbot.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
