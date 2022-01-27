import json
import os
import tempfile
import unittest


from server import app
import db_functions as data


def test_init_db():
    data.db.drop_all()
    data.db.create_all()
    data.create_user(username="bertil", password="ABCdef123", email="bananer@student.liu.se", weight=60, gender='male',
                     user_id="UL4WE4Q4OSVOYOA1")
    data.db.session.commit()


class ServerTests(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.app = app.test_client()
        with app.app_context():
            data.db.init_app(app)
            test_init_db()

    def test_homepage(self):
        rv = self.app.get('/')
        rv_data = json.loads(rv.data.decode('utf-8'))
        assert rv.status_code == 200
        assert rv_data == "hello world"

    def test_create_user(self):
        payload = {'username': 'klas', 'password': 'ABCdef123', 'email': 'klas@student.liu.se', 'weight': 80,
                   'gender': 'male'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/register", json=payload, headers=headers)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200
        assert data.is_user_username(rv_data["username"])

    def test_create_user_bad_password(self):
        payload = {'username': 'klas', 'password': '123', 'email': 'klas@student.liu.se', 'weight': 80,
                   'gender': 'male'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/register", json=payload, headers=headers)
        assert rv.status_code == 400

    def test_create_user_invalid_username(self):
        payload = {'username': 'bertil', 'password': 'abc', 'email': 'klas@student.liu.se', 'weight': 80,
                   'gender': 'male'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/register", json=payload, headers=headers)
        assert rv.status_code == 400

    def test_login_user(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/login", json=payload, headers=headers)
        assert rv.status_code == 200

    def test_login_user_wrong_pass(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef124'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/login", json=payload, headers=headers)
        assert rv.status_code == 400

    def test_login_user_wrong_user(self):
        payload = {'email': 'bananer2@student.liu.se', 'password': '123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/login", json=payload, headers=headers)
        assert rv.status_code == 400

    def test_user(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.get('/user/bananer@student.liu.se', headers=headers)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200
        assert rv_data == data.get_user_username('bertil').to_dict()

    def test_login_logout(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.post('/user/logout', headers=headers)
        assert rv.status_code == 200

    def test_user_follow(self):
        payload = {'username': 'klas', 'password': 'ABCdef123', 'email': 'klas@student.liu.se', 'weight': 80,
                   'gender': 'male'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/register", json=payload, headers=headers)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200
        assert data.is_user_username(rv_data["username"])

        payload = {'email': 'klas@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.post('/user/follow/UL4WE4Q4OSVOYOA1', headers=headers)
        assert rv.status_code == 200

        rv = self.app.get('/user/klas@student.liu.se', headers=headers)
        rv_data = json.loads(rv.data)

        followers = data.get_user_followers('UL4WE4Q4OSVOYOA1')
        assert rv.status_code == 200
        assert rv_data in followers

    def test_user_unfollow(self):
        payload = {'username': 'klas', 'password': 'ABCdef123', 'email': 'klas@student.liu.se', 'weight': 80,
                   'gender': 'male'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/register", json=payload, headers=headers)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200
        assert data.is_user_username(rv_data["username"])

        payload = {'email': 'klas@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.post('/user/follow/UL4WE4Q4OSVOYOA1', headers=headers)
        assert rv.status_code == 200

        rv = self.app.post('/user/unfollow/UL4WE4Q4OSVOYOA1', headers=headers)
        assert rv.status_code == 200

        rv = self.app.get('/user/klas@student.liu.se', headers=headers)
        rv_data = json.loads(rv.data)

        followers = data.get_user_followers('UL4WE4Q4OSVOYOA1')
        assert rv.status_code == 200
        assert rv_data not in followers

    def test_user_get_following(self):
        payload = {'username': 'klas', 'password': 'ABCdef123', 'email': 'klas@student.liu.se', 'weight': 80,
                   'gender': 'male'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/register", json=payload, headers=headers)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200
        assert data.is_user_username(rv_data["username"])

        payload = {'email': 'klas@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.post('/user/follow/UL4WE4Q4OSVOYOA1', headers=headers)
        assert rv.status_code == 200

        rv = self.app.get('/user/following', headers=headers)
        rv_data = json.loads(rv.data)

        assert rv.status_code == 200
        assert data.get_user_id('UL4WE4Q4OSVOYOA1').to_dict() in rv_data

    def test_user_get_followers(self):
        payload = {'username': 'klas', 'password': 'ABCdef123', 'email': 'klas@student.liu.se', 'weight': 80,
                   'gender': 'male'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/register", json=payload, headers=headers)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200
        assert data.is_user_username(rv_data["username"])

        payload = {'email': 'klas@student.liu.se', 'password': 'ABCdef123'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.post('/user/follow/UL4WE4Q4OSVOYOA1', headers=headers)
        assert rv.status_code == 200

        rv = self.app.post('/user/logout', headers=headers)
        assert rv.status_code == 200

        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.get('/user/followers', headers=headers)
        rv_data = json.loads(rv.data)

        assert rv.status_code == 200
        assert data.get_user_username('klas').to_dict() in rv_data

    def test_remove_user(self):
        payload = {'username': 'klas', 'password': 'ABCdef123', 'email': 'klas@student.liu.se', 'weight': 80,
                   'gender': 'male'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post("/user/register", json=payload, headers=headers)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200
        assert data.is_user_username(rv_data["username"])

        payload = {'email': 'klas@student.liu.se', 'password': 'ABCdef123'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.post('/user/delete', headers=headers)
        assert rv.status_code == 200
        assert data.get_user_username('klas') is None

    def test_refresh_token(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.get('/user/login/refresh', headers=headers)
        assert rv.status_code == 200

    def test_create_post(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        payload = {'drink_name': 'Gränges', 'volume': 33, 'alcohol_percentage': 5.3}
        rv = self.app.post('/post', headers=headers, json=payload)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200
        posts = data.get_posts_by_author_id(data.get_user_username('bertil'))
        assert len([x.to_dict() for x in posts if x.to_dict()['author'] == rv_data['author']]) > 0

    def test_like_post(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        payload = {'drink_name': 'Gränges', 'volume': 33, 'alcohol_percentage': 5.3}
        rv = self.app.post('/post', headers=headers, json=payload)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200

        post_id = rv_data['post_id']
        rv = self.app.get('/post/'+post_id+'/like', headers=headers)
        rv_data = json.loads(rv.data)
        assert 'bertil' in rv_data['likes']
        assert rv.status_code == 200

    def test_unlike_post(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        payload = {'drink_name': 'Gränges', 'volume': 33, 'alcohol_percentage': 5.3}
        rv = self.app.post('/post', headers=headers, json=payload)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200

        post_id = rv_data['post_id']
        rv = self.app.get('/post/'+post_id+'/like', headers=headers)
        rv_data = json.loads(rv.data)
        assert 'bertil' in rv_data['likes']
        assert rv.status_code == 200

        post_id = rv_data['post_id']
        rv = self.app.get('/post/' + post_id + '/unlike', headers=headers)
        rv_data = json.loads(rv.data)
        assert 'bertil' not in rv_data['likes']
        assert rv.status_code == 200

    def test_comment_post(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        payload = {'drink_name': 'Gränges', 'volume': 33, 'alcohol_percentage': 5.3}
        rv = self.app.post('/post', headers=headers, json=payload)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200

        post_id = rv_data['post_id']
        payload = {'body': 'Älska gränkaluring <3'}
        rv = self.app.post('/post/'+post_id+'/comment', json=payload, headers=headers)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200

    def test_get_post_comments(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        payload = {'drink_name': 'Gränges', 'volume': 33, 'alcohol_percentage': 5.3}
        rv = self.app.post('/post', headers=headers, json=payload)
        rv_data = json.loads(rv.data)
        assert rv.status_code == 200

        post_id = rv_data['post_id']
        payload = {'body': 'Älska gränkaluring <3'}
        rv = self.app.post('/post/' + post_id + '/comment', json=payload, headers=headers)
        assert rv.status_code == 200

        rv = self.app.get('/post/'+post_id+'/comment', headers=headers)
        rv_data = json.loads(rv.data)
        comments = [x['body'] for x in rv_data]
        assert rv.status_code == 200
        assert 'Älska gränkaluring <3' in comments

    def test_search_user(self):
        payload = {'email': 'bananer@student.liu.se', 'password': 'ABCdef123'}
        headers = {'Content-Type': 'application/json'}
        rv = self.app.post('/user/login', json=payload, headers=headers)
        token = json.loads(rv.data)
        headers = {'Authorization': 'Bearer ' + token['token'], 'Content-Type': 'application/json'}
        assert rv.status_code == 200

        rv = self.app.get('/user/search/ber', headers=headers)
        rv_data = json.loads(rv.data)
        search_res = [x['username'] for x in rv_data]
        assert 'bertil' in search_res
        assert rv.status_code == 200

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


if __name__ == '__main__':
    unittest.main()
