"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py



import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

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

def create_user():
    u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
    u.id = 3333    

    db.session.add(u)
    db.session.commit()

    return u

class UserModelTestCase(TestCase):
    """Test methods for User."""

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

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res    

    def test_user_model(self):
        """Does basic model work?"""

        u = create_user()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does repr work?"""

        self.assertEqual(repr(self.u1), '<User #1111: testuser1, email1@test.com>')

    def test_follow(self):
        """Tests that we can follow a user"""

        self.u1.following.append(self.u2)
        db.session.commit()    

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

    def test_is_following(self):
        """Tests that is_following method works"""

        self.u1.following.append(self.u2)
        db.session.commit()    

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        """Tests that is_followed_by method works"""

        self.u1.following.append(self.u2)
        db.session.commit()   

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_unfollow(self):
        """Tests that we can unfollow a user"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u2.followers), 1)

        self.u1.following.remove(self.u2)   
        db.session.commit()

        self.assertEqual(len(self.u1.following), 0)
        self.assertEqual(len(self.u2.followers), 0)

    def test_create_user(self):
        """Tests that we can create a user when inputting correct credentials"""

        User.signup('test_signup', 'sign@email.com', 'pass1', None)   
        db.session.commit() 

        test_user = User.query.filter_by(username='test_signup').first()
    
        self.assertEqual((test_user.username), 'test_signup')
        self.assertEqual((test_user.email), 'sign@email.com')
        self.assertNotEqual((test_user.password), 'pass1')
        self.assertTrue(test_user.password.startswith('$2b$'))


    def test_no_password(self):
        """user signup without a password"""
        self.assertRaises(ValueError, User.signup, 'test_signup', 'sign@email.com', None, None)

    def test_no_email(self):
        """user signup without email"""
        User.signup('test_signup', None, 'pass1', None)
        self.assertRaises(exc.IntegrityError, db.session.commit)

    def test_no_username(self):
        """user signup without username"""    
        User.signup(None, 'testemail@email.com', 'pass1', None)
        self.assertRaises(exc.IntegrityError, db.session.commit)

    def test_non_unique_username(self):
        """user signup without unique username"""

        User.signup('testuser1', 'testemail@email.com', 'pass1', None)
        self.assertRaises(exc.IntegrityError, db.session.commit)

    def test_non_unique_email(self):
        """user signup without unique username"""

        User.signup('testuser3', 'email1@test.com', 'pass1', None)
        self.assertRaises(exc.IntegrityError, db.session.commit)

    def test_invalid_password(self):
        """user signup with invalid password"""
   
        self.assertRaises(TypeError, User.signup, 'testuser3', 'test@email.com', 123, None)

    def test_authenticate(self):
        """authentication with correct credentials"""

        test_user = User.authenticate('testuser1', 'password1')
        self.assertTrue(isinstance(test_user, User))

    def test_auth_without_username(self):
        """authentication with bad username"""    

        self.assertFalse(User.authenticate('bad_username', 'password1'))

    def test_auth_without_password(self):
        """authentication with bad username"""    

        self.assertFalse(User.authenticate('testuser1', 'bad_password'))

    def test_edit_user(self):
        """Tests that we can edit a user"""

        self.assertEqual(self.u1.username, 'testuser1')
        self.assertEqual(self.u1.email, 'email1@test.com')
        self.assertEqual(self.u1.image_url, '/static/images/default-pic.png')
        self.assertEqual(self.u1.header_image_url, '/static/images/warbler-hero.jpg')
        self.assertEqual(self.u1.location, None)
        self.assertEqual(self.u1.bio, None)

        self.u1.edit_user('new_name', 'new_email@email.com', 'https://newpic.jpg', 'https://newpic2.jpg', 'new_loc', 'new_bio' )   

        self.assertEqual(self.u1.username, 'new_name')
        self.assertEqual(self.u1.email, 'new_email@email.com')
        self.assertEqual(self.u1.image_url, 'https://newpic.jpg')
        self.assertEqual(self.u1.header_image_url, 'https://newpic2.jpg')
        self.assertEqual(self.u1.location, 'new_loc')
        self.assertEqual(self.u1.bio, 'new_bio')

    def test_delete_user(self):
        """Tests that we can delete a user"""

        test_user = User.query.filter_by(id=1111).first()
        self.assertEqual(test_user.username, 'testuser1')
        self.assertEqual(test_user.id, 1111)

        db.session.delete(test_user)
        db.session.commit()
        
        self.assertEqual(User.query.filter_by(id=1111).first(), None)
        

    def test_user_messages(self):
        """Tests that posted messages can be seen by User.messages"""    

        msg = Message(text='test msg')
        self.u1.messages.append(msg)
    
        db.session.commit()
        self.assertEqual(len(self.u1.messages), 1)

    def test_user_likes(self):
        """Tests that likes can be viewed by User.likes"""  

        msg = Message(text='test msg')
        self.u1.messages.append(msg)
    
        db.session.commit()

        self.u1.likes.append(msg)
        db.session.commit()

        self.assertEqual(len(self.u1.likes), 1)











