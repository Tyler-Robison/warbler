"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class UserModelTestCase(TestCase):
    """Test methods for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        u1 = User.signup("testuser1", "email1@test.com", "password1", None)
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup("testuser2", "email2@test.com", "password2", None)
        uid2 = 2222
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        msg = Message(text='test msg')
        self.u1.messages.append(msg)
        msgid = 1111
        msg.id = msgid
    
        db.session.commit()

        msg1 = Message.query.get(msgid)
        self.msg1 = msg1

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res      

    def test_message_model(self):
        """Tests that message model works"""

        self.assertEqual(self.msg1.text, 'test msg')   
        self.assertEqual(self.msg1.id, 1111) 
        self.assertEqual(self.msg1.user_id, 1111) 
        self.assertEqual(self.msg1.user, self.u1) 

    def test_repr(self):
        """Tests that message repr works as intended"""

        self.assertEqual(repr(self.msg1), '<Message #1111, Text: test msg, user_id: 1111>')

    def test_delete_message(self):
        """Tests that we can delete a message"""

        self.assertEqual(self.msg1.text, 'test msg')   
        self.assertEqual(self.msg1.id, 1111) 

        db.session.delete(self.msg1)
        db.session.commit()
        
        self.assertEqual(Message.query.filter_by(id=1111).first(), None)

    def test_message_likes(self):
        """Tests that we can like a message"""

        self.assertEqual(len(self.u2.likes), 0)
        self.u2.likes.append(self.msg1)
        self.assertEqual(len(self.u2.likes), 1)

        likes = Likes.query.filter(Likes.user_id == 2222).all()
        self.assertEqual(likes[0].message_id, 1111)


    