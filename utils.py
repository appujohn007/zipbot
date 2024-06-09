import os
import time
import logging
from pyrogram.types import Message
from zipfile import ZipFile
from os import remove, mkdir, listdir, rmdir
from database import db_session, User, commit
import asyncio
from pyrogram.errors import FloodWait

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def dir_work(uid):
    """Return the directory path for user files."""
    return f"static/{uid}/"

def zip_work(uid):
    """Return the zip file path for user files."""
    return f"static/{uid}.zip"

def list_dir(uid):
    """Return a list of files in the user directory."""
    return listdir(dir_work(uid))

async def handle_flood_wait(func, *args, **kwargs):
    """Handles FloodWait exceptions with exponential backoff."""
    delay = 1
    while True:
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            logger.warning(f"FloodWait: Sleeping for {e.x} seconds")
            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff

def download_progress(current, total, msg: Message, start_time):
    """Progress function for downloading files."""
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time if elapsed_time > 0 else 0
    percentage = current / total * 100

    if speed > 1024 * 1024:
        speed_str = f"{speed / (1024 * 1024):.2f} MB/s"
    else:
        speed_str = f"{speed / 1024:.2f} KB/s"

    eta = (total - current) / speed if speed > 0 else 0
    eta_minutes = int(eta // 60)
    eta_seconds = int(eta % 60)

    eta_str = f"{eta_minutes} min {eta_seconds} sec" if eta_minutes > 0 else f"{eta_seconds} sec"

    progress_message = (
        f"**Download progress: {percentage:.1f}%**\n"
        f"Speed: {speed_str}\n"
        f"ETA: {eta_str}"
    )

    try:
        msg.edit(progress_message)
    except Exception as e:
        logger.error(f"Error updating download progress: {e}")

def up_progress(current, total, msg: Message, start_time):
    """Progress function for uploading files."""
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time if elapsed_time > 0 else 0
    percentage = current / total * 100

    if speed > 1024 * 1024:
        speed_str = f"{speed / (1024 * 1024):.2f} MB/s"
    else:
        speed_str = f"{speed / 1024:.2f} KB/s"

    eta = (total - current) / speed if speed > 0 else 0
    eta_minutes = int(eta // 60)
    eta_seconds = int(eta % 60)

    eta_str = f"{eta_minutes} min {eta_seconds} sec" if eta_minutes > 0 else f"{eta_seconds} sec"

    progress_message = (
        f"**Upload progress: {percentage:.1f}%**\n"
        f"Speed: {speed_str}\n"
        f"ETA: {eta_str}"
    )

    try:
        msg.edit(progress_message)
    except Exception as e:
        logger.error(f"Error updating upload progress: {e}")

async def zip_and_send(uid, zip_path, msg, stsmsg):
    """Create zip file and send it."""
    try:
        with ZipFile(zip_path, "w") as zip:
            for file in list_dir(uid):
                file_path = f"{dir_work(uid)}/{file}"
                zip.write(file_path, arcname=file)
                remove(file_path)

        await handle_flood_wait(msg.reply_document, zip_path, progress=up_progress, progress_args=(stsmsg, time.time()))

        rmdir(dir_work(uid))
        remove(zip_path)
    except Exception as e:
        logger.error(f"Error in zip_and_send: {e}")
        msg.reply(f"An error occurred while creating or sending the zip file: {e}")
