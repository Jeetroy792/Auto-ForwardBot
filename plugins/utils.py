import time as tm
from database import db

class STS:
    def __init__(self, id):
        self.id = str(id)

    def verify(self):
        # ডাটাবেস থেকে ডাটা চেক করা
        return db.get_forward_data(self.id)

    def store(self, From, to, skip, limit):
        data = {
            "_id": self.id,
            "FROW": From, 
            "TO": to, 
            "total_files": 0, 
            "skip": skip,
            "fetched": skip, 
            "filtered": 0, 
            "deleted": 0, 
            "duplicate": 0,
            "last_msg_id": limit
        }
        db.save_forward_data(self.id, data)
        return STS(self.id)

    def get(self, value=None, full=False):
        data = db.get_forward_data(self.id)
        if not data:
            return None
        if not full:
            # chat_id, toid, skip, last_msg_id ফরম্যাটে রিটার্ন
            return data.get('FROW'), data.get('TO'), data.get('skip'), data.get('last_msg_id')
        return data
