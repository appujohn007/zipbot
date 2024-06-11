import os
import logging
from pyrogram import Client, filters, types
from zipfile import ZipFile
from os import remove, rmdir, mkdir
from utils import zip_work, dir_work, up_progress, list_dir, db_session, User, commit, download_progress
import time

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
    try:
        if msg.from_user is None:
            msg.reply("An error occurred. Please try again later.")
            return

        uid = msg.from_user.id
        with db_session:
            if not User.get(uid=uid):
                User(uid=uid, status=0)  # Initializing the user on database
                commit()

        msg.reply("Welcome! You can use /zip command to start zipping files.")
    except Exception as e:
        logger.error(f"Error in start: {e}")
        msg.reply("An error occurred. Please try again later.")

@app.on_message(filters.command("zip"))
def start_zip(client, msg: types.Message):
    """Ask for zip name and initialize the folder"""
    try:
        if msg.from_user is None:
            msg.reply("An error occurred. Please try again later.")
            return

        uid = msg.from_user.id
        msg.reply("Please provide the name for the zip file (e.g., test.zip).")

        with db_session:
            User.get(uid=uid).status = 1  # change user-status to "INSERT"
            commit()

        # Clear and recreate the user's directory
        try:
            mkdir(dir_work(uid))
        except FileExistsError:
            for file in list_dir(uid):
                remove(dir_work(uid) + file)
            rmdir(dir_work(uid))
            mkdir(dir_work(uid))
    except Exception as e:
        logger.error(f"Error in start_zip: {e}")
        msg.reply(f"Error in zipping: {e}")

@app.on_message(filters.text & filters.private)
def set_zip_name(client, msg: types.Message):
    """Set the zip name based on user input"""
    try:
        if msg.from_user is None:
            msg.reply("An error occurred. Please try again later.")
            return

        uid = msg.from_user.id

        with db_session:
            usr = User.get(uid=uid)
            if usr.status == 1:  # Ensure the user is in INSERT mode
                usr.zip_name = msg.text  # Store the zip name in the user's entry
                commit()
                msg.reply(f"Zip file name set to {msg.text}. Please send the files you want to zip.")
            else:
                msg.reply("Please use /zip command to start the zipping process.")
    except Exception as e:
        logger.error(f"Error in set_zip_name: {e}")
        msg.reply(f"An error occurred. Please try again later.\n\nError in set_zip_name: {e}")

@app.on_message(filters.media)
def enter_files(client, msg: types.Message):
    """Download files"""
    try:
        if msg.from_user is None:
            msg.reply("An error occurred. Please try again later.")
            return

        uid = msg.from_user.id
        logger.info(f"Received media from user {uid}")

        with db_session:
            usr = User.get(uid=uid)
            if usr.status == 1:  # check if user-status is "INSERT"
                file_type = msg.document or msg.video or msg.photo or msg.audio

                if file_type.file_size > 2097152000:
                    msg.reply("The file size exceeds the maximum limit.")
                elif len(list_dir(uid)) > 500:
                    msg.reply("You have reached the maximum number of files allowed.")
                else:
                    start_time = time.time()
                    downsts = msg.reply("Downloading file...", True)  # send status-download message
                    msg.download(dir_work(uid, usr.zip_name), progress=download_progress, progress_args=(downsts, start_time))
            else:
                msg.reply("Please use /zip command to start the zipping process.")
    except Exception as e:
        logger.error(f"Error in enter_files: {e}")
        msg.reply(f"An error occurred. Please try again later.\n\nError in enter_files: {e}")


# Start to make zip
@app.on_message(filters.command("done"))
def stop_zip(client, msg: types.Message):
    """Exit from insert mode and send the archive"""
    try:
        if msg.from_user is None:
            msg.reply("An error occurred. Please try again later.")
            return

        uid = msg.from_user.id
        with db_session:
            usr = User.get(uid=uid)
            if usr.status == 1:
                usr.status = 0  # change user-status to "NOT-INSERT"
                commit()
            else:
                msg.reply("Please use /zip command to start the zipping process.")
                return

        zip_name = usr.zip_name or 'archive'
        zip_path = zip_work(uid, zip_name)

        stsmsg = msg.reply(f"Zipping files... Total: {len(list_dir(uid, zip_name))}")  # send status-message "ZIPPING" and count files

        if not list_dir(uid, zip_name):  # if len files is zero
            msg.reply("No files to zip.")
            rmdir(dir_work(uid, zip_name))
            return

        # Add files to zip with unique names to avoid duplicates
        with ZipFile(zip_path, "w") as zip:
            for file in list_dir(uid, zip_name):
                file_path = f"{dir_work(uid, zip_name)}/{file}"
                zip.write(file_path, arcname=file)  # add files to zip-archive with original names
                remove(file_path)  # delete files that added

        stsmsg.edit_text("Uploading the zip archive...")  # change status-msg to "UPLOADING"
        
        start_time = time.time()
        try:
            msg.reply_document(zip_path, progress=up_progress,  # send the zip-archive
                               progress_args=(stsmsg, start_time))
        except ValueError as e:
            msg.reply(f"An unknown error occurred: {str(e)}")

        stsmsg.delete()  # delete the status-msg
        remove(zip_path)  # delete the zip-archive
        rmdir(dir_work(uid, zip_name))  # delete the static-folder
    except Exception as e:
        logger.error(f"Error in stop_zip: {e}")
        msg.reply("An error occurred. Please try again later.")

if __name__ == '__main__':
    try:
        mkdir("static")  # create static files folder
    except FileExistsError:
        pass

    try:
        app.run()
    except Exception as e:
        logger.error(f"Error running the bot: {e}")
