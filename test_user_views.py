"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py



import os
from unittest import TestCase

from flask import session
from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app, CURR_USER_KEY


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

default_image = '/static/images/default-pic.png'
default_header_image = '/static/images/warbler-hero.jpg'


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

        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 1111
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2_id = 2222
        self.u2.id = self.u2_id
        self.u3 = User.signup("hij", "test3@test.com", "password", None)
        self.u3_id = 3333
        self.u3.id = self.u3_id
        self.u4 = User.signup("testing", "test4@test.com", "password", None)

        db.session.commit()

        self.u2.following.append(self.u3)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return

    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))
            self.assertIn("@hij", str(resp.data))
            self.assertIn("@testing", str(resp.data))

    def test_signup(self):
        """Tests that we can signup a user"""
        with self.client as c:
            resp = c.post("/signup", data={
                'username': 'Billy',
                'password': 'billy758',
                'email': 'billy@gmail.com',
                'image_url': None
            })

            new_user = User.query.filter_by(username='Billy').first()
            self.assertEqual(new_user.username, 'Billy')
            self.assertTrue(new_user.password.startswith('$2b$'))
            self.assertEqual(new_user.email, 'billy@gmail.com')
            self.assertEqual(new_user.image_url, default_image)
            self.assertEqual(new_user.header_image_url, default_header_image)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_signup_redirect(self):
        """After signup, are we redirected to homepage that displays our new user?"""

        with self.client as c:
            resp = c.post("/signup", data={
                'username': 'Billy',
                'password': 'billy758',
                'email': 'billy@gmail.com',
                'image_url': None
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('<p>@Billy</p>', html)

    def test_login(self):
        """Tests that we can login a user"""

        with self.client as c:
            resp = c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(session[CURR_USER_KEY], user.id)

    def test_login_redirect(self):
        """After login are we redirected to homepage"""

        with self.client as c:
            resp = c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('<p>@testuser</p>', html)

    def test_logout(self):
        """Tests that a user can logout"""

        with self.client as c:
            c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(session[CURR_USER_KEY], user.id)

            resp = c.get('logout')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/login')

            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(session.get(CURR_USER_KEY), None)

    def test_logout_redirect(self):
        """After logout are we redirected to homepage"""

        with self.client as c:
            c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(session[CURR_USER_KEY], user.id)

            resp = c.get('/logout', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('Logout Succesful', html)


    def test_signup_bad_username(self):
        """Tests that we can't signup with a non-unique username"""

        with self.client as c:
            resp = c.post("/signup", data={
                'username': 'testuser',
                'password': 'billy758',
                'email': 'billy@gmail.com',
                'image_url': None
            })

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('Username or email already taken', html)   

    def test_signup_bad_email(self):
        """Tests that we can't signup with a non-unique email"""

        with self.client as c:
            resp = c.post("/signup", data={
                'username': 'billybob',
                'password': 'billy758',
                'email': 'test@test.com',
                'image_url': None
            })

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('Username or email already taken', html)       

    def test_signup_bad_password(self):
        """Tests that we can't signup with a password less than 6 characters"""

        with self.client as c:
            resp = c.post("/signup", data={
                'username': 'billybob',
                'password': '123',
                'email': 'billybob@test.com',
                'image_url': None
            })

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('Field must be at least 6 characters long', html)   

    def test_login_bad_credentials(self):
        """Tests that we cant login with bad credentials"""

        with self.client as c:
            resp = c.post("/login", data={
                'username': '123456',
                'password': 'abcdef'
            })

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('Invalid credentials', html)                       


    # login as testuser, see if we can see user 2 following 3 and vice-versa
    def test_following_authorization(self):
        """When logged in can we access other users following pages"""

        with self.client as c:
            resp = c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(session[CURR_USER_KEY], user.id)

            resp = c.get('/users/2222/following')

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('hij', html)

    def test_follower_authorization(self):    
        """When logged in can we access other users followers pages"""    

        with self.client as c:
            resp = c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(session[CURR_USER_KEY], user.id)

            resp = c.get('/users/3333/followers')

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('efg', html)

    def test_logged_out_following_auth(self):
        """When logged out can you access another users following page"""   

        with self.client as c:
            resp = c.get('/users/3333/following')     

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_logged_out_following_auth_redirect(self):
        """Are logged out users redirected to home-anon.html?"""   

        with self.client as c:
            resp = c.get('/users/3333/following', follow_redirects=True)     

            self.assertEqual(resp.status_code, 200)
             
            html = resp.get_data(as_text=True)
            self.assertIn('Sign up now to get your own personalized timeline!', html)    

    def test_logged_out_followers_auth(self):
        """When logged out can you access another users followers page"""   

        with self.client as c:
            resp = c.get('/users/3333/followers')     

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_logged_out_followers_auth_redirect(self):
        """Are logged out users redirected to home-anon.html?"""   

        with self.client as c:
            resp = c.get('/users/3333/followers', follow_redirects=True)     

            self.assertEqual(resp.status_code, 200)
             
            html = resp.get_data(as_text=True)
            self.assertIn('Sign up now to get your own personalized timeline!', html)          

    def setup_likes(self):
        m1 = Message(text="trending warble", user_id=self.testuser_id)
        m2 = Message(text="Eating some lunch", user_id=self.testuser_id)
        m3 = Message(id=9876, text="likable warble", user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=9876)

        db.session.add(l1)
        db.session.commit()

    def test_view_likes(self):
        """When logged in, can we view our own likes""" 

        self.setup_likes()
        user = User.query.filter_by(id=1234).first()

        with self.client as c:
            resp = c.get(f'/users/{user.id}/likes')

            self.assertEqual(resp.status_code, 200)
             
            html = resp.get_data(as_text=True)
            self.assertIn(f'<a href="/users/{user.id}/likes">{len(user.likes)}</a>', html)
            

    def test_logged_in_add_like(self):
        """When logged in, can we add likes"""

        m = Message(id=1111, text="The earth is round", user_id=1111)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            
            user = User.query.filter_by(id=1234).first()

            self.assertEqual(len(user.likes), 0)
            self.assertEqual(len(Likes.query.all()), 0)

            resp = c.post('/users/like', json = {
                'msg_id': 1111
            })
            user = User.query.filter_by(id=1234).first() 
            self.assertEqual(len(user.likes), 1)
            self.assertEqual(len(Likes.query.all()), 1)
            self.assertEqual(resp.json['result'], 'like added')

    def test_logged_in_remove_like(self):
        """When logged in, can we add likes"""

        m = Message(id=1111, text="The earth is round", user_id=1111)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })

            
            user = User.query.filter_by(id=1234).first()

            self.assertEqual(len(user.likes), 0)
            self.assertEqual(len(Likes.query.all()), 0)

            # add like
            resp = c.post('/users/like', json = {
                'msg_id': 1111
            })
            user = User.query.filter_by(id=1234).first() 
            self.assertEqual(len(user.likes), 1)
            self.assertEqual(len(Likes.query.all()), 1)
            self.assertEqual(resp.json['result'], 'like added')

            # remove the like
            resp = c.post('/users/like', json = {
                'msg_id': 1111
            })
            user = User.query.filter_by(id=1234).first() 
            self.assertEqual(len(user.likes), 0)
            self.assertEqual(len(Likes.query.all()), 0)
            self.assertEqual(resp.json['result'], 'like removed')

    def test_logged_out_add_like(self):
        """When logged out, are we prevented from adding likes"""

        m = Message(id=1111, text="The earth is round", user_id=1111)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            
            user = User.query.filter_by(id=1234).first()

            self.assertEqual(len(user.likes), 0)
            self.assertEqual(len(Likes.query.all()), 0)

            resp = c.post('/users/like', json = {
                'msg_id': 1111
            }, follow_redirects=True)

            # like wasn't added
            user = User.query.filter_by(id=1234).first() 
            self.assertEqual(len(user.likes), 0)
            self.assertEqual(len(Likes.query.all()), 0)

            self.assertEqual(resp.status_code, 200)
             
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized', html)   

    def test_like_own_message(self):
        """When logged in, can we like our own message"""    

        m = Message(id=1111, text="The earth is round", user_id=1234)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            c.post("/login", data={
                'username': 'testuser',
                'password': 'testuser'
            })
            
            user = User.query.filter_by(id=1234).first()

            self.assertEqual(len(user.likes), 0)
            self.assertEqual(len(Likes.query.all()), 0)

            resp = c.post('/users/like', json = {
                'msg_id': 1111
            })

            user = User.query.filter_by(id=1234).first() 
            self.assertEqual(len(user.likes), 0)
            self.assertEqual(len(Likes.query.all()), 0)
            self.assertEqual(resp.json['result'], 'Cant like own message')         







             




   

















