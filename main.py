import os
from pyrogram import Client
from os import mkdir

app_id = int(os.environ.get("API_ID", 10471716))
app_key = os.environ.get('API_HASH', "f8a1b21a13af154596e2ff5bed164860")
token = os.environ.get('BOT_TOKEN', "6916875347:AAEVxR4cO_sIBB6V57ANA92pHKxzw9G3yX0")

app = Client("zipBot", app_id, app_key, bot_token=token)

# Import the handlers
import bot.private

if __name__ == '__main__':
    try:
        mkdir("static")  # create static files folder
    except FileExistsError:
        pass

    app.run()
