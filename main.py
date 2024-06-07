import os
import logging
from pyrogram import Client, filters, types
from zipfile import ZipFile
from os import remove, rmdir, mkdir
from utils import zip_work, dir_work, up_progress, list_dir, Msg, db_session, User, commit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Pyrogram logging level to ERROR
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# Bot credentials from environment variables
app_id = int(os.environ.get("API_ID", 10471716))
app_key = os.environ.get('API_HASH', "f8a1b21a13af154596e2ff5bed164860")
token = os.environ.get('BOT_TOKEN', "6916875347:AAEVxR4cO_sIBB6V57ANA92pHKxzw9G3yX0")

# Initialize the client
app = Client("zipBot", app_id, app_key, bot_token=token)

@app.on_message(filters.command("start"))
def start(client, msg: types.Message):
    """Reply start message and add the user to database"""
    uid = msg.from_user.id
    logger.info(f"Received /start from user {uid}")

    with db_session:
        if not User.get(uid=uid):
            User(uid=uid, status=0)  # Initializing the user on database
            commit()

    msg.reply(Msg.hello)

@app.on_message(filters.command("zip"))
def start_zip(client, msg: types.Message):
    """Starting get files to archive"""
    uid = msg.from_user.id
    logger.info(f"Received /zip from user {uid}")

    msg.reply(Msg.zip)

    with db_session:
        User.get(uid=uid).status = 1  # change user-status to "INSERT"
        commit()

    try:
        mkdir(dir_work(uid))  # create static-folder for user
    except FileExistsError:  # in case the folder already exists
        for file in list_dir(uid):
            remove(dir_work(uid) + file)  # delete all files from folder
        rmdir(dir_work(uid))  # delete folder
        mkdir(dir_work(uid))

@app.on_message(filters.media)
def enter_files(client, msg: types.Message):
    """Download files"""
    uid = msg.from_user.id
    logger.info(f"Received media from user {uid}")

    with db_session:
        usr = User.get(uid=uid)
        if usr.status == 1:  # check if user-status is "INSERT"
            file_type = msg.document or msg.video or msg.photo or msg.audio

            if file_type.file_size > 2097152000:
                msg.reply(Msg.too_big)
            elif len(list_dir(uid)) > 500:
                msg.reply(Msg.too_much)
            else:
                downsts = msg.reply(Msg.downloading, True)  # send status-download message
                msg.download(dir_work(uid))

                downsts.delete()  # delete status-download message
        else:
            msg.reply(Msg.send_zip)  # if user-status is not "INSERT"

@app.on_message(filters.command("stopzip"))
def stop_zip(client, msg: types.Message):
    """Exit from insert mode and send the archive"""
    uid = msg.from_user.id
    logger.info(f"Received /stopzip from user {uid}")

    if len(msg.command) == 1:
        zip_path = zip_work(uid)
    else:
        zip_path = "static/" + msg.command[1]  # custom zip-file name

    with db_session:
        usr = User.get(uid=uid)
        if usr.status == 1:
            usr.status = 0  # change user-status to "NOT-INSERT"
            commit()
        else:
            msg.reply(Msg.send_zip)
            return

    stsmsg = msg.reply(Msg.zipping.format(len(list_dir(uid))))  # send status-message "ZIPPING" and count files

    if not list_dir(uid):  # if len files is zero
        msg.reply(Msg.zero_files)
        rmdir(dir_work(uid))
        return

    for file in list_dir(uid):
        with ZipFile(zip_path, "a") as zip:
            zip.write(f"{dir_work(uid)}/{file}")  # add files to zip-archive
        remove(f"{dir_work(uid)}{file}")  # delete files that added

    stsmsg.edit_text(Msg.uploading)  # change status-msg to "UPLOADING"

    try:
        msg.reply_document(zip_path, progress=up_progress,  # send the zip-archive
                           progress_args=(stsmsg,))
    except ValueError as e:
        msg.reply(Msg.unknown_error.format(str(e)))

    stsmsg.delete()  # delete the status-msg
    remove(zip_path)  # delete the zip-archive
    rmdir(dir_work(uid))  # delete the static-folder

if __name__ == '__main__':
    try:
        mkdir("static")  # create static files folder
    except FileExistsError:
        pass

    app.run()
