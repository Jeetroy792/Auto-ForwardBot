import time as tm
from database import db

class STS:
    def __init__(self, id):
        self.id = str(id)

    async def verify(self):
        # ডাটাবেস থেকে চেক করবে
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
            return None
        if full:
            # এটিকে একটি অবজেক্টের মতো ব্যবহার করার জন্য SimpleNamespace বা Dot notation সুবিধা দেয়
            from types import SimpleNamespace
            return SimpleNamespace(**data)
        if value:
            return data.get(value)
        return data.get('FROW'), data.get('TO'), data.get('skip'), data.get('last_msg_id')

    async def add(self, key, value=1):
        # প্রোগ্রেস আপডেট করার জন্য ডাটাবেসে ভ্যালু বাড়াবে
        data = await db.get_forward_data(self.id)
        if data:
            if key == 'time':
                data['start'] = tm.time()
            else:
                data[key] = data.get(key, 0) + value
            await db.save_forward_data(self.id, data)
        return True

    async def get_data(self, user_id, client=None):
        # আপনার ডাটাবেস থেকে সেটিংস ডেটা নিয়ে আসবে
        # এটি আপনার database.py এর লজিকের সাথে সামঞ্জস্যপূর্ণ হতে হবে
        settings = await db.get_settings(user_id) 
        if not settings:
            return None, None, False, {}, False, None
        
        _bot = settings.get('bot')
        caption = settings.get('caption')
        forward_tag = settings.get('forward_tag', False)
        protect = settings.get('protect', False)
        button = settings.get('button')
        return _bot, caption, forward_tag, settings, protect, button

    def divide(self, n, d):
        # স্পিড ক্যালকুলেশনের জন্য
        return n / d if d else 0
