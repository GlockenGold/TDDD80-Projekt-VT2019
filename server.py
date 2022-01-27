from db_functions import *
from flask import abort, redirect, url_for, flash, make_response


@app.before_first_request
def create_db():
    init_db()


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return is_token_blacklisted(jti)


@app.route('/', methods=['GET'])
def index():
    return make_response(jsonify("hello world"))


@app.route('/user/<email>', methods=['GET'])
@jwt_required
def user(email):
    return make_response(jsonify(get_user_email(email).to_dict()))


@app.route('/user/search/<string:query>')
@jwt_required
def search_user(query):
    return make_response(jsonify(db_search_user(query)))


@app.route('/post', methods=['POST'])
@jwt_required
def post():
    author_id = get_jwt_identity()
    drink_name = request.json['drink_name']
    volume = request.json['volume']
    alcohol_percentage = request.json['alcohol_percentage']
    return make_response(jsonify(create_post(drink_name, volume, alcohol_percentage, author_id).to_dict()))


@app.route('/post/<post_id>')
def get_post(post_id):
    post = Post.query.filter_by(post_id=post_id).first_or_404()
    return make_response(jsonify(post.to_dict()))


@app.route('/post/<post_id>/<action>')
@jwt_required
def like_action(post_id, action):
    post = Post.query.filter_by(post_id=post_id).first_or_404()
    current_user = get_user_id(get_jwt_identity())
    if action == 'like':
        current_user.like_post(post)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_post(post)
        db.session.commit()
    return make_response(jsonify(post.to_dict()))


@app.route('/post/<post_id>/comment', methods=['POST'])
@jwt_required
def post_comment(post_id):
    body = request.json['body']
    return make_response(jsonify(create_comment(body, get_jwt_identity(), post_id).to_dict()))


@app.route('/post/<post_id>/comment', methods=['GET'])
@jwt_required
def get_comments(post_id):
    return make_response(jsonify(get_post_comments(post_id)))


@app.route('/user/register', methods=['POST'])
def register():
    username = request.json['username']
    password = request.json['password']
    email = request.json['email']
    weight = request.json['weight']
    gender = request.json['gender']
    if is_user_username(username):
        abort(400)
    elif not is_secure_password(password):
        abort(400)
    elif is_user_email(email) or not is_valid_email(email):
        abort(400)
    else:
        return make_response(jsonify(create_user(username, password, email, weight, gender).to_dict()))


@app.route('/user/delete', methods=['POST'])
@jwt_required
def delete():
    user = get_user_id(get_jwt_identity())
    remove_user(user)
    if get_user_id(get_jwt_identity()) is None:
        return make_response(jsonify(200))


@app.route('/user/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    if is_user_email(email):
        if check_password(email, password):
            return make_response(jsonify({'token': create_token(email)}))
        else:
            abort(400)
    else:
        abort(400)


@app.route('/user/logout', methods=['POST'])
@jwt_required
def logout():
    blacklist_token(get_raw_jwt()['jti'])
    return make_response(jsonify(200))


@app.route('/user/follow/<followee_id>', methods=['POST'])
@jwt_required
def follow(followee_id):
    follower = get_user_id(get_jwt_identity())
    followee = get_user_id(followee_id)
    if followee is None:
        flash('User %s not found.' % followee)
        abort(400)
        return redirect(url_for('index'))
    if followee == follower:
        flash('You can\'t follow yourself!')
        abort(400)
        return redirect(url_for('user', user_id=get_jwt_identity()))
    u = follow_user(follower, followee)
    if u is None:
        abort(400)
        return redirect(url_for('user', email=followee.email))
    return make_response(jsonify(followee.to_dict()))


@app.route('/user/unfollow/<followee_id>', methods=['POST'])
@jwt_required
def unfollow(followee_id):
    follower = get_user_id(get_jwt_identity())
    followee = get_user_id(followee_id)
    if followee is None:
        flash('User %s not found.' % followee)
        return redirect(url_for('index'))
    if followee == follower:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', user_id=get_jwt_identity()))
    u = unfollow_user(follower, followee)
    if u is None:
        abort(400)
        return redirect(url_for('user', email=followee.email))
    return make_response(jsonify(followee.to_dict()))


@app.route('/user/following', methods=['GET'])
@jwt_required
def get_followed():
    user_id = get_jwt_identity()
    return make_response(jsonify(get_user_followed(user_id)))


@app.route('/user/followers', methods=['GET'])
@jwt_required
def get_followers():
    user_id = get_jwt_identity()
    return make_response(jsonify(get_user_followers(user_id)))


@app.route('/user/login/refresh', methods=['GET'])
@jwt_required
def refresh_token():
    if is_user_user_id(get_jwt_identity()):
        user = get_user_id(get_jwt_identity())
        blacklist_token(get_raw_jwt()['jti'])
        new_token = create_token(user.email)
        return make_response(jsonify(new_token))
    else:
        abort(400)  # Only happens if a tokens identity is not a user.id.
