from database import *
import random
import string
from werkzeug.security import check_password_hash


def create_user(username, password, email, weight, gender, user_id=None, age=None, bio=None):
    """Creates a user with username, password, email, weight, and gender, and generates an ID"""
    if user_id is None:
        user_id = generate_id(is_user_id)
    new_user = User(username=username, password=password, weight=weight, gender=gender,
                    user_id=user_id, email=email, age=age, bio=bio)
    db.session.add(new_user)
    db.session.commit()
    db.session.add(new_user.follow(new_user))
    db.session.commit()
    return new_user


def create_post(drink_name, volume, alcohol_percentage, author_id, post_id=None):
    """ Creates a post with drink name, body text, volume, alcohol_percentage percentage,
    poster ID, and generates a post ID"""
    # TODO: Funkar ej med relation till author_id, fixa
    if post_id is None:
        post_id = generate_id(is_post_id)
    new_post = Post(post_id=post_id, drink_name=drink_name, volume=volume,
                    alcohol_percentage=alcohol_percentage, author_id=author_id)
    db.session.add(new_post)
    db.session.commit()
    return new_post


def create_comment(body, author_id, post_id, comment_id=None):
    """ Creates a comment with body text, and generates a comment_id"""
    if comment_id is None:
        comment_id = generate_id(is_comment_id)
    new_comment = Comment(comment_id=comment_id, body=body, author_id=author_id, post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    return new_comment


def follow_user(follower, followee):
    u = follower.follow(followee)
    if u is None:
        return None
    db.session.add(u)
    db.session.commit()
    return follower


def unfollow_user(follower, followee):
    u = follower.unfollow(followee)
    if u is None:
        return None
    db.session.add(u)
    db.session.commit()
    return follower


def remove_user(user):
    """ Deletes specified user from the database"""
    db.session.delete(user)
    db.session.commit()


def generate_id(test_for_id):
    """ Creates a new id and avoids duplicate id:s"""
    new_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    while test_for_id(new_id):
        new_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    return new_id


def db_search_user(seq):
    """ Returns a list of all users whose usernames contains the sequence seq"""
    ret = User.query.filter(User.username.contains(seq)).all()
    return [x.to_dict() for x in ret]


def check_password(email, password):
    """ Checks if password matches with the saved password hash"""
    user = get_user_email(email)
    return check_password_hash(user.password_hash, password)


def create_token(email):
    """ Creates access token for user"""
    user = get_user_email(email)
    return create_access_token(user.user_id)


def blacklist_token(jti):
    """ Adds token to blacklist"""
    db.session.add(Blacklist(jti=jti))
    db.session.commit()


# Is-tester

def is_token_blacklisted(jti):
    return Blacklist.query.filter_by(jti=jti).first() is not None


def is_user_username(username):
    """Checks if a user with username exists"""
    return User.query.filter_by(username=username).first() is not None


def is_user_user_id(user_id):
    """Checks if a user with user_id exists"""
    return User.query.filter_by(user_id=user_id).first() is not None


def is_valid_email(email):
    """ Only works for LiU students for now, maybe fix better domain check later?"""
    return email.endswith('@student.liu.se')


def is_user_id(user_id):
    """ Checks if a user id exists"""
    return User.query.get(user_id) is not None


def is_post_id(post_id):
    """ Checks if a post with post_id exists"""
    return Post.query.get(post_id) is not None


def is_comment_id(comment_id):
    """ Checks if a comment with comment_id exists"""
    return Comment.query.get(comment_id) is not None


def is_user_email(email):
    """ Checks if a user email exists"""
    return User.query.filter_by(email=email).first() is not None


def is_secure_password(password):
    """ Checks if password contains uppercase, lowercase, digits, and is longer than 8 characters"""
    conditions = [lambda s: any(x.isupper() for x in s), lambda s: any(x.islower() for x in s),
                  lambda s: any(x.isdigit() for x in s), lambda s: len(s) >= 7]
    if all(condition(password) for condition in conditions):
        return True
    return False


# Getters


def get_user_id(user_id):
    """Finds user with ID user_id"""
    return User.query.get(user_id)


def get_user_username(username):
    """Search for user by username"""
    return User.query.filter_by(username=username).first()


def get_user_email(email):
    """Search for user by email"""
    return User.query.filter_by(email=email).first()


def get_user_followers(user_id):
    """ Returns all followers of user"""
    user = get_user_id(user_id)
    return [x.to_dict() for x in user.followers if not x == user]


def get_user_followed(user_id):
    """ Returns all users followed by user"""
    user = get_user_id(user_id)
    return [x.to_dict() for x in user.followed if not x == user]


def get_post(post_id):
    """ Search for post by post_id"""
    return Post.query.get(post_id=post_id)


def get_posts_by_author_id(user_id):
    """ Search for posts posted by user_id"""
    return Post.query.filter_by(author=user_id).all()


def get_post_comments(post_id):
    """ Gets all comments on post with post_id"""
    ret = [x.to_dict() for x in Comment.query.filter_by(post_id=post_id).all()]
    return ret

# Setters


def set_user_bio(user_id, bio):
    """ Finds a user by user_id and sets the bio"""
    user = get_user_id(user_id)
    user.bio = bio
    db.session.add(user)
    db.session.commit()


def set_user_weight(user_id, weight):
    """ Finds a user by user_id and sets the weight"""
    user = get_user_id(user_id)
    user.weight = weight
    db.session.add(user)
    db.session.commit()

