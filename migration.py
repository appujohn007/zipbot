from pony.migrate import * 

migrations = [
    # Add the 'files' column to the User table
    ChangeSet("add_files_column_to_user", sql=[
        "ALTER TABLE User ADD COLUMN files TEXT",
    ]),
]
