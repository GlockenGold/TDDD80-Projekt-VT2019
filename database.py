from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_jwt import *
from flask_jwt_extended import *
from werkzeug.security import generate_password_hash
from hashlib import md5


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if 'NAMESPACE' in os.environ and os.environ['NAMESPACE'] == 'heroku':
    db_uri = os.environ['DATABASE_URL']
    debug_flag = False
else:  # when running locally with sqlite
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    db_uri = 'sqlite:///{}'.format(db_path)
    debug_flag = True

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bananer i pyjamas')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
app.config['JWT_BLACKLIST_ENABLED'] = True
jwt = JWTManager(app)

# TODO: Fix DeprecationWarning: The verify parameter is deprecated. Please use options instead.
#  'Please use options instead.', DeprecationWarning


db = SQLAlchemy(app)


followers = db.Table('followers',
                     db.Column('follower_id', db.String(16), db.ForeignKey('user.user_id'), primary_key=True),
                     db.Column('followed_id', db.String(16), db.ForeignKey('user.user_id'), primary_key=True))

liked_posts = db.Table('liked_posts',
                       db.Column('user_id', db.String(16), db.ForeignKey('user.user_id'), primary_key=True),
                       db.Column('post_id', db.String(16), db.ForeignKey('post.post_id'), primary_key=True))

comments = db.Table('comments',
                    db.Column('user_id', db.String(16), db.ForeignKey('user.user_id'), primary_key=True),
                    db.Column('post_id', db.String(16), db.ForeignKey('post.post_id'), primary_key=True),
                    db.Column('comment_id', db.String(16), db.ForeignKey('comment.comment_id'), primary_key=True))


class User(db.Model):
    user_id = db.Column(db.String(16), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    bio = db.Column(db.String(280))

    posts = db.relationship('Post', backref='author', lazy='dynamic')

    comments = db.relationship('Comment', secondary=comments, backref='author', lazy='dynamic')

    liked = db.relationship('Post', secondary=liked_posts, backref='likes')

    followed = db.relationship('User', secondary=followers,
                               primaryjoin=user_id == followers.c.follower_id,
                               secondaryjoin=user_id == followers.c.followed_id,
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')

    def __init__(self, user_id, username, password, weight, gender, email, age, bio):
        self.user_id = user_id
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.weight = weight
        self.gender = gender
        self.email = email
        self.bio = bio

    def like_post(self, post):
        if not self.has_liked_post(post):
            self.liked.append(post)
            db.session.add(self)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            self.liked.remove(post)
            db.session.add(self)

    def has_liked_post(self, post):
        return post in self.liked

    def avatar(self, size=80):
        """ Returns the Gravatar link to the users avatar. size argument determines the size of the avatar in pixels """
        return 'http://www.gravatar.com/avatar/%s?d=mp&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.user_id).count() > 0

    def followed_posts(self):
        return Post.query.join(followers, (followers.c.followed_id == Post.author_id)).filter(
            followers.c.follower_id == self.user_id).order_by(Post.timestamp.desc())

    def to_dict(self):
        return {'user_id': self.user_id,
                'username': self.username,
                'weight': self.weight,
                'gender': self.gender,
                'email': self.email,
                'bio': self.bio,
                'posts': [x.to_dict() for x in self.posts],
                'followed_posts': [x.to_dict() for x in self.followed_posts()],
                'liked_posts': [x.to_dict() for x in self.liked],
                'avatar': self.avatar(),
                'followed': [x.username for x in self.followed if x != self]}


class Post(db.Model):
    post_id = db.Column(db.String(16), primary_key=True)
    timestamp = db.Column(db.DateTime)
    drink_name = db.Column(db.String(32))
    volume = db.Column(db.Float, nullable=False)
    alcohol_percentage = db.Column(db.Float, nullable=False)
    author_id = db.Column(db.String(16), db.ForeignKey('user.user_id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def __init__(self, post_id, drink_name, volume, alcohol_percentage, author_id):
        self.post_id = post_id
        self.timestamp = datetime.utcnow()
        self.drink_name = drink_name
        self.volume = volume
        self.alcohol_percentage = alcohol_percentage
        self.author_id = author_id

    def to_dict(self):
        return {'post_id': self.post_id,
                'timestamp': self.timestamp.isoformat(),
                'drink_name': self.drink_name,
                'volume': self.volume,
                'alcohol_percentage': self.alcohol_percentage,
                'likes': [x.username for x in self.likes],
                'author': User.query.get(self.author_id).username}


class Comment(db.Model):
    comment_id = db.Column(db.String(16), primary_key=True)
    body = db.Column(db.String(140), nullable=False)
    timestamp = db.Column(db.DateTime)
    author_id = db.Column(db.String(16), db.ForeignKey('user.user_id'))
    post_id = db.Column(db.String(16), db.ForeignKey('post.post_id'))

    def __init__(self, comment_id, body, author_id, post_id):
        self.comment_id = comment_id
        self.body = body
        self.timestamp = datetime.utcnow()
        self.author_id = author_id
        self.post_id = post_id

    def to_dict(self):
        return {'comment_id': self.comment_id,
                'body': self.body,
                'timestamp': self.timestamp.isoformat(),
                'author_id': self.author_id,
                'post_id': self.post_id}


class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jti = db.Column(db.String(200), nullable=False, unique=True)


def init_new_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


def init_db():
    db.create_all()


def db_update():
    db.session.commit()
