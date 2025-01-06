import unittest
from app import app, db, User, Task


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Tear down the test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_user(self):
        """Test user registration."""
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to /login
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)

    def test_login_user(self):
        """Test user login."""
        user = User(username='testuser', password='testpassword')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to /dashboard
        with self.client.session_transaction() as session:
            self.assertEqual(session['user_id'], user.id)

    def test_invalid_login(self):
        """Test invalid login."""
        response = self.client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on /login
        self.assertIn(b'Invalid credentials!', response.data)

    def test_dashboard_access(self):
        """Test access to the dashboard."""
        user = User(username='testuser', password='testpassword')
        db.session.add(user)
        db.session.commit()

        with self.client.session_transaction() as session:
            session['user_id'] = user.id

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)

    def test_create_task(self):
        """Test task creation."""
        user = User(username='testuser', password='testpassword')
        db.session.add(user)
        db.session.commit()

        with self.client.session_transaction() as session:
            session['user_id'] = user.id

        response = self.client.post('/dashboard', data={'title': 'Test Task'})
        self.assertEqual(response.status_code, 200)

        task = Task.query.filter_by(title='Test Task').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.user_id, user.id)

    def test_logout(self):
        """Test user logout."""
        with self.client.session_transaction() as session:
            session['user_id'] = 1

        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)  # Redirect to /login
        with self.client.session_transaction() as session:
            self.assertNotIn('user_id', session)


if __name__ == '__main__':
    unittest.main()
