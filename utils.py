import os
import time
import logging
from pyrogram.types import Message
from zipfile import ZipFile
from os import remove, mkdir, listdir, rmdir
import asyncio
from pyrogram.errors import FloodWait
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///example.db"  # Replace with your database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)

Base.metadata.create_all(bind=engine)

def db_session():
    """Create a new database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def commit():
    """Commit the current database transaction."""
    session = SessionLocal()
    session.commit()

def dir_work(uid):
    """Return the directory path for user files."""
    return f"static/{uid}/"

def zip_work(uid):
    """Return the zip file path for user files."""
    return f"static/{uid}.zip"

def list_dir(uid):
    """Return a list of files in the user directory."""
    return listdir(dir_work(uid))

last_update_time = {}

async def should_update_progress(chat_id):
    global last_update_time
    current_time = time.time()
    if chat_id not in last_update_time or (current_time - last_update_time[chat_id]) >= 1:
        last_update_time[chat_id] = current_time
        return True
    return False

async def download_progress(current, total, msg: Message):
    """Edit status-msg with progress of the downloading"""
    if await should_update_progress(msg.chat.id):
        progress = current / total
        speed = current / (time.time() - msg.date)
        eta = (total - current) / speed

        if eta >= 60:
            eta_min = int(eta // 60)
            eta_sec = int(eta % 60)
            eta_str = f"{eta_min} min {eta_sec} sec"
        else:
            eta_str = f"{int(eta)} sec"

        speed_str = f"{speed / 1024:.2f} KB/s" if speed < 1024 * 1024 else f"{speed / (1024 * 1024):.2f} MB/s"

        try:
            await msg.edit(f"**Download progress: {progress * 100:.1f}%**\n"
                           f"**Speed:** {speed_str}\n"
                           f"**ETA:** {eta_str}")
        except FloodWait as e:
            await handle_flood_wait(e)

async def up_progress(current, total, msg: Message):
    """Edit status-msg with progress of the uploading"""
    if await should_update_progress(msg.chat.id):
        progress = current / total
        speed = current / (time.time() - msg.date)
        eta = (total - current) / speed

        if eta >= 60:
            eta_min = int(eta // 60)
            eta_sec = int(eta % 60)
            eta_str = f"{eta_min} min {eta_sec} sec"
        else:
            eta_str = f"{int(eta)} sec"

        speed_str = f"{speed / 1024:.2f} KB/s" if speed < 1024 * 1024 else f"{speed / (1024 * 1024):.2f} MB/s"

        try:
            await msg.edit(f"**Upload progress: {progress * 100:.1f}%**\n"
                           f"**Speed:** {speed_str}\n"
                           f"**ETA:** {eta_str}")
        except FloodWait as e:
            await handle_flood_wait(e)

async def handle_flood_wait(e: FloodWait):
    """Handle FloodWait exception by sleeping for the required duration"""
    logger.warning(f"FloodWait: Sleeping for {e.x} seconds")
    await asyncio.sleep(e.x)
