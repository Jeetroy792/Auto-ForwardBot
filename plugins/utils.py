import time as tm
from database import db
from types import SimpleNamespace

class STS:
    def __init__(self, id):
        self.id = str(id)

    async def verify(self):
        # আপনার ডাটাবেস ফাইলের ফাংশন অনুযায়ী
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
            if full: return SimpleNamespace(fetched=0, total=0, total_files=0, duplicate=0, deleted=0, skip=0, start=tm.time(), id=self.id, TO=0)
            return None
        if full:
            return SimpleNamespace(**data)
        if value:
            return data.get(value)
        return data.get('FROW'), data.get('TO'), data.get('skip'), data.get('last_msg_id')

    async def add(self, key, value=1):
        """
        আপনার database.py এর 'db.forward_status' কালেকশনে সরাসরি আপডেট করবে।
        এটি ডেটা ফেচ না করেই সরাসরি MongoDB-তে ভ্যালু বাড়াবে ($inc)।
        """
        if key == 'time':
            await db.db.forward_status.update_one({'_id': self.id}, {'$set': {'start': tm.time()}})
        else:
            await db.db.forward_status.update_one({'_id': self.id}, {'$inc': {key: value}})
        return True

    async def get_data(self, user_id, client=None):
        """
        আপনার database.py এর get_configs এবং get_bot ফাংশন ব্যবহার করবে।
        """
        configs = await db.get_configs(user_id)
        _bot = await db.get_bot(user_id)
        
        if not _bot:
            return None, None, False, {}, False, None
            
        caption = configs.get('caption', "")
        forward_tag = configs.get('forward_tag', False)
        protect = configs.get('protect', False)
        button = configs.get('button', None)
        
        return _bot, caption, forward_tag, configs, protect, button

    def divide(self, n, d):
        try:
            return n / d if d else 0
        except:
            return 0
