#!/usr/bin/env python2.7

import json
import os
import bleach
import random
import string
import requests
import httplib2

from functools import wraps
from flask import (Flask,
                   render_template,
                   make_response,
                   request,
                   redirect,
                   url_for,
                   flash,
                   jsonify,
                   session as login_session)

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Item, User

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from PIL import Image

# ORM database
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

# Config and constants
CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# DECORATORS
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash('You are not allowed to access there')
            return redirect(url_for('showLogin'))
    return decorated_function


# JSON ENDPOINTS
@app.route('/catalog/JSON/')
def showCatalogJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


@app.route('/catalog/<string:category_name>/items/JSON')
def showItemsJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=category)
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def showItemJSON(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         category=category).one()
    return jsonify(Item=[item.serialize])


# APPLICATION ROUTES

# Fetch category sidebar and the last 10 items added to the database
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Category).all()
    latest_items = session.query(Item).order_by(desc(Item.id)).limit(10)
    return render_template('main.html',
                           categories=categories,
                           latest_items=latest_items)


# Fetch items of a given category as well as the categories for the sidebar
# again and pass it to the category view.
@app.route('/catalog/<string:category_name>/items/')
def showItems(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=category)
    return render_template('category.html',
                           categories=categories, category=category,
                           items=items)


# Fetch item information and creator information and pass it to the item view.
@app.route('/catalog/<string:category_name>/<string:item_name>/')
def showItem(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         category=category).one()
    creator = getUserInfo(item.user_id)
    return render_template('item.html', item=item, creator=creator)


# Create an anti-forgery state token and pass it to the login view.
@app.route('/catalog/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Handle oauth requests and set up an outh flow to exchange an access token
# for credentials.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps("Failed to upgrade the "
                                            "authorization code."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 50)
        response.headers['Content-Type'] = 'application/json'
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID does not match the given User ID."),
            401)
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("Current user is already "
                                            "connected."), 200)
        response.headers['Content-Type'] = 'application/json'

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Create a new user in the database if it doesn't exist already.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    response = make_response(
        json.dumps("Successfully logged in, redirecting..."), 201)
    response.headers['Content-Type'] = 'application/json'
    return response


# Revoke the current access token effectively logging out the user.
# Clean up the session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % (
          login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return (redirect(url_for('showCatalog')))
    else:
        return (redirect(url_for('showCatalog')))


# Insert a new item into the db.
@app.route('/catalog/<string:category_name>/new/', methods=["GET", "POST"])
@login_required
def newItem(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    if(request.method == 'POST'):
        # Sanitize user input
        name = bleach.clean(request.form['name'], tags=[], strip=True)
        description = bleach.clean(request.form['description'],
                                   tags=[], strip=True)
        # Very rudimentary csrf protection
        if not csrf_protect():
            return "CSRF detected"
        # If an image is attached, upload it to the server.
        if request.files['image']:
            file = request.files['image']
            image = upload_image(file, name)
        else:
            image = None
        item = Item(name=name, description=description, category=category,
                    user_id=login_session['user_id'], filename=image)
        session.add(item)
        session.commit()
        return(redirect(url_for('showItem',
                                category_name=item.category.name,
                                item_name=item.name)))
    else:
        return render_template('newitem.html', category=category)


@app.route('/catalog/<string:item_name>/edit/', methods=["GET", "POST"])
#@csrf_protected
@login_required
def editItem(item_name):
    # Update a given item from the db.
    item = session.query(Item).filter_by(name=item_name).one()
    if not isUserOwner(item):
        flash("You do not own this item.")
        return redirect(url_for('showCatalog'))
        
    if(request.method == 'POST'):
        # Sanitize user input
        name = bleach.clean(request.form['name'], tags=[], strip=True)
        description = bleach.clean(request.form['description'],
                                   tags=[], strip=True)
        if not csrf_protect():
             return "CSRF detected"

        # If an image is attached, replace the current image with it.
        if request.files['image']:
            file = request.files['image']
            if item.filename:
                delete_image(item.filename)
            image = upload_image(file, name)
            item.filename = image
        category = session.query(Category).get(request.form['category'])
        item.name = name
        item.description = description
        item.category = category

        session.add(item)
        session.commit()
        return(redirect(url_for('showItem',
                                category_name=item.category.name,
                                item_name=item.name)))
    else:
        categories = session.query(Category).all()
        return render_template('edititem.html', item=item,
                               categories=categories)


@app.route('/catalog/<string:item_name>/delete/', methods=["GET", "POST"])
@login_required
def deleteItem(item_name):
    # Delete a given item from the db.
    item = session.query(Item).filter_by(name=item_name).one()
    if not isUserOwner(item):
        flash("You do not own this item.")
        return redirect(url_for('showCatalog'))

    if(request.method == 'POST'):
        if not csrf_protect():
            return "CSRF detected"

        # If an image was attached to this item, delete it from the server.
        if item.filename:
            delete_image(item.filename)
        category_name = item.category.name
        session.delete(item)
        session.commit()
        return(redirect(url_for('showItems', category_name=category_name)))
    else:
        return render_template('deleteitem.html', item=item)


@app.route('/catalog/<string:item_name>/deleteImage/', methods=["GET", "POST"])
@login_required
def deleteItemImage(item_name):
    # Delete a given item from the db.
    item = session.query(Item).filter_by(name=item_name).one()
    if not isUserOwner(item):
        flash("You do not own this item.")
        return redirect(url_for('showCatalog'))

    if(request.method == 'POST'):
        if not csrf_protect():
            return "CSRF detected"

        delete_image(item.filename)
        item.filename = None
        session.add(item)
        session.commit()
        category_name = item.category.name
        return(redirect(url_for('showItem', category_name=category_name, item_name=item.name)))
    else:
        return render_template('deleteitemimage.html', item=item)


# HELPER FUNCTIONS
def createUser(login_session):
    # Add a new user to the db.
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email):
    # Exchange the user email for a user id from the db.
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


def getUserInfo(user_id):
    # Exhange the user id for user info from the db.
    user = session.query(User).filter_by(id=user_id).one()
    return user


def isUserOwner(item):
    owner = session.query(Item).filter_by(
                                          user_id=login_session['user_id'],
                                          id=item.id
                                          ).first()
    if owner:
        return True
    return False


def generate_csrf_token():
    # Generate a csrf token and store it in the session.
    if 'csrf_token' not in login_session:
        login_session['csrf_token'] = ''.join(random.choice(
                                              string.ascii_uppercase +
                                              string.digits) for x
                                              in xrange(32))
    return login_session['csrf_token']


def csrf_protect():
    # Check if current csrf token is valid.
    token = login_session.pop('csrf_token', None)
    if not token or token != request.form.get('csrf_token'):
        return False
    else:
        return True


def upload_image(file, item_name):
    # Upload an image to server.
    # Check for file integrity and file type.
    try:
        ext = file.filename.split('.')[-1]
        filename = item_name+"."+ext
        f = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        img = Image.open(file)
        img.verify()
    except IOError, SyntaxError:
        print "Bad file: %s" % filename
        return None
    file.save(f)
    return filename


def delete_image(filename):
    # Delete image from the server.
    f = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.remove(f)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.jinja_env.globals['csrf_token'] = generate_csrf_token
    app.jinja_env.globals['client_id'] = CLIENT_ID
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
