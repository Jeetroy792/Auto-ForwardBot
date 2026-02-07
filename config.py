from os import environ 

class Config:
    API_ID = environ.get("API_ID", "24670806")
    API_HASH = environ.get("API_HASH", "82134723a32b2cae76b9cfb3b1570745")
    BOT_TOKEN = environ.get("BOT_TOKEN", "7933011109:AAEh6m_MoKYtHHbOvJfJeXWZxBHIYUPJ3Tc") 
    BOT_SESSION = environ.get("BOT_SESSION", "forward-bot") 
    DATABASE_URI = environ.get("DATABASE", "mongodb+srv://botuser:botuserpass1234@cluster0.bcz3n2q.mongodb.net/?retryWrites=true&w=majority")
    DATABASE_NAME = environ.get("DATABASE_NAME", "forward-bot")
    BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '8229228616').split()]

class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
    
