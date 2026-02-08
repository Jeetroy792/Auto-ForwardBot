import time as tm
from database import db

class STS:
    def __init__(self, id):
        self.id = str(id)

    async def verify(self):
        # ডাটাবেস থেকে চেক করার সময় await যোগ করা হয়েছে
        return await db.get_forward_data(self.id)

    async def store(self, From, to, skip, limit):
        data = {
            "_id": self.id,
            "FROW": From, 
            "TO": to, 
            "skip": skip,
            "last_msg_id": limit
        }
        # ডাটাবেসে সেভ করার সময় await যোগ করা হয়েছে
        await db.save_forward_data(self.id, data)
        return STS(self.id)

    async def get(self, value=None, full=False):
        # ডাটাবেস থেকে ডেটা নেওয়ার সময় await যোগ করা হয়েছে
        data = await db.get_forward_data(self.id)
        if not data:
            return None
        if not full:
            return data.get('FROW'), data.get('TO'), data.get('skip'), data.get('last_msg_id')
        return data
