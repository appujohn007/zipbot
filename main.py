import os
import logging
from pyrogram import Client, filters, types
from os import remove, rmdir, mkdir
from utils import zip_work, dir_work, up_progress, list_dir, db_session, User, commit, download_progress
from zipfile import ZipFile
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Pyrogram logging level to ERROR
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# Bot credentials from environment variables
app_id = int(os.environ.get("API_ID", 10471716))
app_key = os.environ.get('API_HASH', "f8a1b21a13af154596e2ff5bed164860")
token = os.environ.get('BOT_TOKEN', "YOUR_BOT_TOKEN")

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
                User(uid=uid, status=0)  # Initializing the user in the database
                commit()

        msg.reply("Welcome! You can use /zip command to start zipping files.")
    except Exception as e:
        logger.error(f"Error in start: {e}")
        msg.reply("An error occurred. Please try again later.")

@app.on_message(filters.command("zip"))
def s@app.on_message(filters.command("zip"))
def start_zip(client, msg: types.Message):
    """Starting get files to archive"""
    try:
        if msg.from_user is None:
            msg.reply("An error occurred. Please try again later.")
            return

        uid = msg.from_user.id

        msg.reply("Please send the files you want to zip.")

        with db_session:
            user = User.get(uid=uid)
            if user:
                user.status = 1  # Change user-status to "INSERT"
                user.files = []  # Initialize the files list
            else:
                User(uid=uid, status=1, files=[])  # Initialize the user in the database with an empty files list
            commit()

        try:
            mkdir(dir_work(uid))  # Create static-folder for user
        except FileExistsError:  # In case the folder already exists
            for file in list_dir(uid):
                remove(dir_work(uid) + file)  # Delete all files from folder
            rmdir(dir_work(uid))  # Delete folder
            mkdir(dir_work(uid))
    except Exception as e:
        logger.error(f"Error in start_zip: {e}")
        msg.reply(f"Error in zipping : {e}")

@app.on_message(filters.media)
def enter_files(client, msg: types.Message):
    """Store file information"""
    try:
        if msg.from_user is None:
            msg.reply("An error occurred. Please try again later.")
            return

        uid = msg.from_user.id
        logger.info(f"Received media from user {uid}")

        with db_session:
            user = User.get(uid=uid)
            if user.status == 1:  # Check if user status is "INSERT"
                file_type = msg.document or msg.video or msg.photo or msg.audio

                if file_type.file_size > 2097152000:
                    msg.reply("The file size exceeds the maximum limit.")
                elif len(user.files) >= 500:
                    msg.reply("You have reached the maximum number of files allowed.")
                else:
                    user.files.append(file_type.file_id)  # Store file_id
                    commit()
                    msg.reply("File stored successfully.")
            else:
                msg.reply("Please send the /done command to finish zipping and send the archive.")
    except Exception as e:
        logger.error(f"Error in enter_files: {e}")
        msg.reply(f"An error occurred. Please try again later.\nError in enter_files: {e}")

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
                usr.status = 0  # Change user-status to "NOT-INSERT"
                commit()
            else:
                msg.reply("Please send the /done command to finish zipping and send the archive.")
                return

        if not usr.files:
            msg.reply("No files to zip.")
            return

        user_dir = dir_work(uid)
        mkdir(user_dir)  # Ensure the user directory exists

        # Progress message
        progress_msg = msg.reply("Downloading files...", quote=True)
        start_time = time.time()

        # Download all stored files with progress
        for file_id in usr.files:
            file = client.get_messages(msg.chat.id, file_id)
            file.download(user_dir, progress=download_progress, progress_args=(progress_msg, start_time))

        zip_path = zip_work(uid)
        stsmsg = msg.reply(f"Zipping files... Total: {len(list_dir(uid))}")  # Send status-message "ZIPPING" and count files

        if not list_dir(uid):  # If no files
            msg.reply("No files to zip.")
            rmdir(user_dir)
            return

        # Add files to zip with unique names to avoid duplicates
        with ZipFile(zip_path, "w") as zip:
            for file in list_dir(uid):
                file_path = os.path.join(user_dir, file)
                zip.write(file_path, arcname=file)  # Add files to zip-archive with original names
                remove(file_path)  # Delete files that added

        stsmsg.edit_text("Uploading the zip archive...")  # Change status-msg to "UPLOADING"
        
        start_time = time.time()
        try:
            msg.reply_document(zip_path, progress=up_progress,  # Send the zip-archive
                               progress_args=(stsmsg, start_time))
        except ValueError as e:
            msg.reply(f"An unknown error occurred: {str(e)}")

        stsmsg.delete()  # Delete the status-msg
        remove(zip_path)  # Delete the zip-archive
        rmdir(user_dir)  # Delete the static-folder
    except Exception as e:
        logger.error(f"Error in stop_zip: {e}")
        msg.reply("An error occurred. Please try again later.")


if __name__ == '__main__':
    try:
        mkdir("static")  # Create static files folder
    except FileExistsError:
        pass

    try:
        app.run()
    except Exception as e:
        logger.error(f"Error running the bot: {e}")
