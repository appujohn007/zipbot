from pony.orm import *
from pyrogram.types import Message
from os import listdir
import time

# ========= DB build =========
db = Database()

class User(db.Entity):
    uid = PrimaryKey(int, size=64)  # Allows larger values for uid
    status = Required(int)  # status-user: "INSERT"/"NOT-INSERT"

db.bind(provider='sqlite', filename='zipbot.sqlite', create_db=True)
db.generate_mapping(create_tables=True)

# ========= helping func =========
def dir_work(uid: int) -> str:
    """ static-user folder """
    return f"static/{uid}/"

def zip_work(uid: int) -> str:
    """ zip-archive file """
    return f'static/{uid}.zip'

def list_dir(uid: int) -> list:
    """ items in static-user folder """
    return listdir(dir_work(uid))

def up_progress(current, total, msg: Message):
    """ edit status-msg with progress of the uploading """
    progress = current / total
    speed = current / (time.time() - start_time)
    eta = (total - current) / speed if speed > 0 else 0
    msg.edit(f"**Upload progress: {progress * 100:.1f}%**\n"
             f"**Speed:** {speed / 1024:.2f} KB/s\n"
             f"**ETA:** {eta:.2f} s")

def download_progress(current, total, msg: Message):
    """ edit status-msg with progress of the downloading """
    progress = current / total
    speed = current / (time.time() - start_time)
    eta = (total - current) / speed if speed > 0 else 0
    msg.edit(f"**Download progress: {progress * 100:.1f}%**\n"
             f"**Speed:** {speed / 1024:.2f} KB/s\n"
             f"**ETA:** {eta:.2f} s")

# ========= MSG class =========
class Msg:
    def start(msg: Message) -> str:
        """ return start-message text """
        txt = f"Hey {msg.from_user.mention}!\n" \
              "\nI can compress files into an archive." \
              "\nJust send /zip, and follow the instructions."
        return txt

    zip = "Send the files you want to compress, and at the end send /done after all the files have been downloaded.\n" \
          "\n\nNote: due to upload limit, the total size of the file(s) can be at most 2GB."
    too_big = "Note: due to upload limit, the total size of the file(s) can be at most 2GB."
    too_much = "Note: the total number of files can be at most 500."
    send_zip = "Send /zip to compress the files."
    zipping = "Start compressing {} files..."
    uploading = "Uploading archive..."
    unknow_error = "An unknown error occurred."
    downloading = "Downloading..."
    zero_files = "No files were sent."

# ========= Global Variables =========
start_time = time.time()
