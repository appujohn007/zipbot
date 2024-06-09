import asyncio
import time
import logging
from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

async def handle_flood_wait(func, *args, **kwargs):
    """Handle FloodWait exceptions with exponential backoff."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            wait_time = e.x + (2 ** attempt)  # Exponential backoff
            logger.warning(f"FloodWait: Sleeping for {wait_time} seconds.")
            await asyncio.sleep(wait_time)
    logger.error("Max retries reached. Could not complete the request.")
    return None

def up_progress(current, total, msg, start_time):
    """Progress function for upload."""
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time
    percentage = current / total * 100
    eta = (total - current) / speed
    eta_min, eta_sec = divmod(eta, 60)

    speed_str = f"{speed / 1024:.2f} KB/s" if speed < 1048576 else f"{speed / (1024 * 1024):.2f} MB/s"
    eta_str = f"{int(eta_min)} min {int(eta_sec)} sec" if eta_min else f"{int(eta_sec)} sec"

    progress_message = (f"**Upload progress: {percentage:.1f}%**\n"
                        f"Speed: {speed_str}\n"
                        f"ETA: {eta_str}")
    
    asyncio.run(handle_flood_wait(msg.edit_text, progress_message))

def download_progress(current, total, msg, start_time):
    """Progress function for download."""
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time
    percentage = current / total * 100
    eta = (total - current) / speed
    eta_min, eta_sec = divmod(eta, 60)

    speed_str = f"{speed / 1024:.2f} KB/s" if speed < 1048576 else f"{speed / (1024 * 1024):.2f} MB/s"
    eta_str = f"{int(eta_min)} min {int(eta_sec)} sec" if eta_min else f"{int(eta_sec)} sec"

    progress_message = (f"**Download progress: {percentage:.1f}%**\n"
                        f"Speed: {speed_str}\n"
                        f"ETA: {eta_str}")
    
    asyncio.run(handle_flood_wait(msg.edit_text, progress_message))

def zip_work(uid):
    """Returns zip file name based on user ID"""
    return f"static/{uid}.zip"

def dir_work(uid):
    """Returns directory name based on user ID"""
    return f"static/{uid}/"

def list_dir(uid):
    """Lists files in user's directory"""
    return os.listdir(dir_work(uid))
