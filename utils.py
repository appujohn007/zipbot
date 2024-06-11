from pony.orm import *
from pyrogram.types import Message
from os import listdir, mkdir
import time

# ========= DB build =========

db = Database()

class User(db.Entity):
    uid = PrimaryKey(int, size=64)  
    status = Required(int)
    zip_name = Optional(str)  # Change to store the zip name

db.bind(provider='sqlite', filename='zipbot.sqlite', create_db=True)
db.generate_mapping(create_tables=True)

# ========= helping func =========
def dir_work(uid: int, zip_name: str) -> str:
    """ static-user folder """
    return f"static/{uid}/{zip_name}/"

def zip_work(uid: int, zip_name: str) -> str:
    """ zip-archive file """
    return f'static/{uid}/{zip_name}.zip'

def list_dir(uid: int, zip_name: str) -> list:
    """ items in static-user folder """
    return listdir(dir_work(uid, zip_name))

def format_speed_and_eta(speed, eta):
    """Format speed to display in KB/s or MB/s and ETA in minutes and seconds"""
    speed_str = f"{speed / 1024:.2f} KB/s" if speed < 1024 * 1024 else f"{speed / (1024 * 1024):.2f} MB/s"
    eta_str = f"{eta // 60:.0f} min {eta % 60:.0f} sec" if eta >= 60 else f"{eta:.0f} sec"
    return speed_str, eta_str

# Controls how often the progress bar updates
UPDATE_INTERVAL = 3  # Update every 3 seconds

def download_progress(current, total, msg: Message, start_time, last_update=[0]):
    """ edit status-msg with progress of the downloading """
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time
    progress = current / total * 100
    eta = (total - current) / speed
    speed_str, eta_str = format_speed_and_eta(speed, eta)

    new_content = (f"**Download progress: {progress:.1f}%**\n"
                   f"Speed: {speed_str}\n"
                   f"ETA: {eta_str}")
    
    current_time = time.time()
    if current_time - last_update[0] >= UPDATE_INTERVAL:
        try:
            if msg.text != new_content:
                msg.edit(new_content)
                last_update[0] = current_time
        except Exception as e:
            # Log the error or handle it as needed
            pass

def up_progress(current, total, msg: Message, start_time, last_update=[0]):
    """ edit status-msg with progress of the uploading """
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time
    progress = current / total * 100
    eta = (total - current) / speed
    speed_str, eta_str = format_speed_and_eta(speed, eta)

    new_content = (f"**Upload progress: {progress:.1f}%**\n"
                   f"Speed: {speed_str}\n"
                   f"ETA: {eta_str}")
    
    current_time = time.time()
    if current_time - last_update[0] >= UPDATE_INTERVAL:
        try:
            if msg.text != new_content:
                msg.edit(new_content)
                last_update[0] = current_time
        except Exception as e:
            # Log the error or handle it as needed
            pass
