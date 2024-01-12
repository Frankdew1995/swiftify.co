from app import db
from datetime import datetime


'''
Auxillary tables below
'''

class Message(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.String(1000))

    # the user who receives the message
    owner = db.Column(db.String(128))

    container = db.Column(db.String(5000))

    timeCreated = db.Column(db.DateTime, default=datetime.utcnow)

    isRead = db.Column(db.Boolean, default=False)

    # system/user
    kind = db.Column(db.String(128))

    def __repr__(self):

        return f'Message: {self.content}'


