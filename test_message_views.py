"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY, do_login

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 1234
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
    
            resp = c.post("/messages/new", json={"msg_text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)
 
            msg = Message.query.filter_by(id=1).first()
            self.assertEqual(msg.text, "Hello")

    def test_add_no_session(self):
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 99222224 # user does not exist

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_message_show(self):

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
        
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            m = Message.query.get(1234)

            resp = c.get(f'/messages/{m.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))    

    def test_invalid_message_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messages/99999999')

            self.assertEqual(resp.status_code, 404)        

    def test_logged_in_add_message(self):
        """When logged in, can we add a message"""    

        with self.client as c:
            c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            # Post comes from JS/Axios as JSON
            c.post('/messages/new', json={
                'msg_text': 'My New Post'
            })  

            resp = c.get('/')
            self.assertEqual(resp.status_code, 200)

            # Check that msg is displayed in homepage HTML
            html = resp.get_data(as_text=True)
            self.assertIn('My New Post', html)    

            # msg added to db
            msg = Message.query.filter_by(text='My New Post').first()
            self.assertEqual(msg.id, 1)
            self.assertEqual(msg.text, 'My New Post')        
            self.assertEqual(msg.user_id, 1234)
            
    def test_logged_in_delete_message(self):
        """When logged in, can we delete a message""" 

        with self.client as c:
            c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            c.post('/messages/new', json={
                'msg_text': 'My New Post'
            })  

            # Check that msg was succesfully added
            msg = Message.query.filter_by(text='My New Post').first()
            self.assertEqual(msg.id, 1)
            self.assertEqual(msg.text, 'My New Post')        
            self.assertEqual(msg.user_id, 1234)

            c.post('/messages/1/delete')

            # Check that msg was succesfully deleted
            self.assertEqual(Message.query.filter_by(id=1).first(), None)

    def test_logged_out_add_message(self):
        """When logged out, are we prohibited from adding messages"""

        with self.client as c:
            resp = c.post('/messages/new', json={
                'msg_text': 'My New Post'
            }, follow_redirects=True)  

            self.assertEqual(resp.status_code, 200)
             
            # check that we get unauthorized msg
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized', html)        

            # check that no messages in db
            messages = Message.query.all()
            self.assertEqual(len(messages), 0)      

    def test_logged_out_delete_message(self):
        """When logged out, are we prohibited from deleting a message""" 

        msg = Message(
            id=1234,
            text="test msg",
            user_id=self.testuser_id
        )
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            message = Message.query.get(1234)
            self.assertIsNotNone(message)    



    def test_delete_others_message(self):
        """When logged in, can we delete another user's message""" 

        other_user = User.signup(username="other_user",
                        email="otherusert@test.com",
                        password="password",
                        image_url=None)

        # msg owned by testuser, not other_user
        msg = Message(
               id=1111,
               text='not my message',
               user_id=1234
           )
        db.session.add_all([other_user, msg])   
        db.session.commit()

        # When used in combination with a with statement this opens a session transaction. 
        # This can be used to modify the session that the test client uses. Once the with block is left the session is stored back.
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = other_user.id

            resp = c.post("/messages/1111/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))    

