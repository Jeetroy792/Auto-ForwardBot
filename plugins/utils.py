import time as tm
from database import db
from types import SimpleNamespace

class STS:
    def __init__(self, id):
        self.id = str(id)

    async def verify(self):
        # সরাসরি ডাটাবেস থেকে চেক
        return await db.get_forward_data(self.id)

    async def store(self, From, to, skip, limit):
        data = {
            "_id": self.id,
            "FROW": From, 
            "TO": to, 
            "skip": skip,
            "last_msg_id": limit,
            "total": 0,
            "fetched": 0,
            "total_files": 0,
            "duplicate": 0,
            "filtered": 0,
            "deleted": 0,
            "start": tm.time()
        }
        await db.save_forward_data(self.id, data)
        return STS(self.id)

    async def get(self, value=None, full=False):
        data = await db.get_forward_data(self.id)
        if not data:
            if full: 
                # ডাটা না থাকলে ডিফল্ট ভ্যালু যাতে কোড ক্র্যাশ না করে
                return SimpleNamespace(fetched=0, total=0, total_files=0, duplicate=0, deleted=0, skip=0, start=tm.time(), id=self.id)
            return None
        if full:
            return SimpleNamespace(**data)
        if value:
            return data.get(value)
        return data.get('FROW'), data.get('TO'), data.get('skip'), data.get('last_msg_id')

    async def add(self, key, value=1):
        """
        MongoDB $inc ব্যবহার করে সরাসরি ডাটাবেসে ভ্যালু আপডেট। 
        এতে ডাটা ফেচ করার প্রয়োজন হয় না, তাই এটি অনেক ফাস্ট।
        """
        if key == 'time':
            # সময় আপডেট করার জন্য $set ব্যবহার
            await db.db.forward.update_one({"_id": self.id}, {"$set": {"start": tm.time()}})
        else:
            # সংখ্যা বাড়ানোর জন্য $inc ব্যবহার (MongoDB native operator)
            await db.db.forward.update_one({"_id": self.id}, {"$inc": {key: value}})
        return True

    async def get_data(self, user_id, client=None):
        settings = await db.get_settings(user_id) 
        if not settings:
            return None, None, False, {}, False, None
        
        _bot = settings.get('bot')
        caption = settings.get('caption', "")
        forward_tag = settings.get('forward_tag', False)
        protect = settings.get('protect', False)
        button = settings.get('button', None)
        return _bot, caption, forward_tag, settings, protect, button

    def divide(self, n, d):
        try:
            return n / d if d else 0
        except ZeroDivisionError:
            return 0
