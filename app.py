import os
import sys
from flask import Flask, request, abort, jsonify, render_template, url_for, flash, redirect, session
from flask_cors import CORS
import traceback
from forms import NewLocationForm, AddPosts, RegistrationForm, LoginForm, SelectAreaForm
from models import setup_db, Location, db_drop_and_create_all, Post, db, User
from sqlalchemy.exc import IntegrityError
import hashlib
from flask_login import login_user, logout_user, login_required, current_user, login_manager, LoginManager
import timeago, datetime


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY

    """ uncomment at the first time running the app. Then comment back so you do not erase db content over and over """
    #db_drop_and_create_all()
    
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'



    @app.route('/test', methods=['GET'])
    def test():
        return render_template(
            'posts.html'
        )

    


    @app.route("/new-location", methods=['GET', 'POST'])
    @login_required
    def new_location():
        form = NewLocationForm()

        if form.validate_on_submit():
            latitude = float(form.coord_latitude.data)
            longitude = float(form.coord_longitude.data)
            description = form.description.data

            location = Location(
                description=description,
                geom=Location.point_representation(latitude=latitude, longitude=longitude)
            )
            location.user_id = current_user.id # <<<< added
            location.insert()

            flash(f'New location created!', 'success')
            return redirect(url_for('map'))

        return render_template(
            'new-location.html',
            form=form,
            map_key=os.getenv('GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_API_KEY_WAS_NOT_SET?!')
        )

    @app.route("/new-post", methods=['GET', 'POST'])
    def new_posts():
        form = AddPosts()

        if form.validate_on_submit():
            
            latitude = float(form.latitude.data)
            longitude = float(form.longitude.data)

            post = Post(
                content=form.content.data,
                geom=Location.point_representation(latitude=latitude, longitude=longitude)
            )
            db.session.add(post)
            db.session.commit()

            flash(f'New post added!', 'success')
            return redirect(url_for('map'))

        return render_template(
            'new-post.html',
            form=form,
            testing='hi there'
        )


    @app.route("/api/store_item")
    def store_item():
        try:
            latitude = float(request.args.get('lat'))
            longitude = float(request.args.get('lng'))
            description = request.args.get('description')
            user_id = int(request.args.get('user_id')) # <<<< added

            location = Location(
                description=description,
                geom=Location.point_representation(latitude=latitude, longitude=longitude),
                user_id=user_id # <<<< added
            )

            location.insert()

            return jsonify(
                {
                    "success": True,
                    "location": location.to_dict()
                }
            ), 200
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            app.logger.error(traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2))
            abort(500)

    @app.route("/api/get_items_in_radius")
    def get_items_in_radius():
        try:
            latitude = float(request.args.get('lat'))
            longitude = float(request.args.get('lng'))
            radius = int(request.args.get('radius'))

            locations = Location.get_items_within_radius(latitude, longitude, radius)
            return jsonify(
                {
                    "success": True,
                    "results": locations
                }
            ), 200
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            app.logger.error(traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2))
            abort(500)

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "server error"
        }), 500
        
            
    @app.route('/about')
    def about():
        return render_template("about.html", user=current_user)

        
    @app.route("/register", methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('create'))
        form = RegistrationForm()
        #if current_user.is_authenticated:
          #  return redirect(url_for('create'))
        if request.method == 'POST': 
            if form.validate_on_submit():
            # hash user password, create user and store it in database
                hashed_password = hashlib.md5(form.password.data.encode()).hexdigest()
                user = User(
                    name=form.name.data,
                    email=form.email.data,
                    password=hashed_password,
                    )

                try:
                    user.insert()
                    flash(f'Hi {form.name.data}! Account created', 'success')
                    return redirect(url_for('login'))
                except IntegrityError as e:
                    flash(f'Could not register! The entered username or email might be already taken', 'error')
                    print('IntegrityError when trying to store new user')
                # db.session.rollback()

        return render_template('registration.html', form=form, user=current_user)
    
    @app.route('/map', methods=['GET'])
    def map():
        return render_template(
            'map.html',
            user=current_user,
            map_key=os.getenv('GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_API_KEY_WAS_NOT_SET?!')
        )
    
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    @app.route("/login", methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        
        if request.method == 'POST': 
            if form.validate_on_submit():
                user = User.query.filter_by(name=form.name.data).first()
                hashed_input_password = hashlib.md5(form.password.data.encode()).hexdigest()
                if user and user.password == hashed_input_password:
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('create'))
                else:
                    flash('Login Unsuccessful. Please check user name and password', 'error')
        return render_template('login.html', title='Login', form=form, user=current_user)

    @app.route("/logout")
    @login_required
    def logout():
        session.pop("post", None)
        logout_user()
        flash(f'You have logged out!', 'success')
        return redirect(url_for('public'))
    
    
    @app.route('/')
    @app.route('/public')
    def public():
        posts = Post.query.order_by(Post.date_posted.desc())
        return render_template("public.html", user=current_user, posts=posts)


    @app.route('/create', methods=['GET', 'POST'])
    @login_required
    def create():
        notes = Post.query.order_by(Post.date_posted.desc()).filter_by(user_id=current_user.id)
        if request.method == 'POST': 
            post = request.form.get('post')#Gets the post from the HTML 
            session["post"] = post
            
            if len(post) < 2:
                flash('Your entry is too short!', category='error') 
            elif len(post) > 240:
                flash('Your entry is too long!', category='error')
            else:
                return redirect(url_for('say_location', user=current_user))

        return render_template("create.html", user=current_user, notes=notes)

   
    @app.route("/say-location", methods=['GET', 'POST'])
    @login_required
    def say_location():
        form = NewLocationForm()
        post = session["post"]
        
        if form.validate_on_submit():
            latitude = float(form.coord_latitude.data)
            longitude = float(form.coord_longitude.data)
            description = form.description.data

            location = Location(
                description=description,
                geom=Location.point_representation(latitude=latitude, longitude=longitude)
            )
            location.user_id = current_user.id
            location.insert()
            
            new_post = Post(
                content=post, 
                user_id=current_user.id, 
                description=description,
                geom=Location.point_representation(latitude=latitude, longitude=longitude)
                )  #providing the schema for the note 
            #db.session.add(new_post) #adding the note to the database 
            #db.session.commit()
            new_post.insert()
        
            flash(f'Your entry gets published!', 'success')
            return redirect(url_for('create'))

        return render_template( 
            'say-location.html',
            form=form,
            user=current_user,
            map_key=os.getenv('GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_API_KEY_WAS_NOT_SET?!')
        )
        
    @app.route("/select-area", methods=['GET', 'POST'])
    def select_area():
        form = SelectAreaForm()
        
        if form.validate_on_submit():
            lat = float(form.coord_latitude.data)
            lng = float(form.coord_longitude.data)
            radius = float(form.radius.data)

            diary = Post.get_items_within_radius(lat, lng, radius)
            session["diary"] = diary
            session["description"] = form.description.data
            
            return redirect(url_for('browse'))
        
        return render_template(
            'select-area.html',
            form=form,
            user=current_user,
            map_key=os.getenv('GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_API_KEY_WAS_NOT_SET?!')
        )        
        
        
    @app.route("/browse", methods=['GET', 'POST'])
    def browse():
        diary = session["diary"]
        description = session["description"]
        
        return render_template("browse.html", user=current_user, diary=diary, description=description)
    
    
    @app.route('/detail', methods=['GET'])
    def detail():
        location_id = float(request.args.get('id'))
        item = Location.query.get(location_id)
        geom1 = item.geom
        
        diary = Post.get_items_with_same_geom(geom1)

        return render_template(
            'detail_geom.html',
            item=item,
            diary=diary,
            user=current_user,
            map_key=os.getenv('GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_API_KEY_WAS_NOT_SET?!')
        )
    
    
    @app.route('/daily', methods=['GET'])
    def daily():
        date = request.args.get('date')
        #diary = Post.get_same_day_items(date)
        #diary = Post.query.get(date)
        diary = Post.query.all()
    
        return render_template(
            'daily.html',
            diary=diary,
            date=date,
            user=current_user,
            map_key=os.getenv('GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_API_KEY_WAS_NOT_SET?!')
        )
    
    
            
    @app.route('/namely', methods=['GET'])
    def namely():
        name = request.args.get('name')
        #diary = Post.get_same_day_items(date)
        #diary = Post.query.get(date)
        diary = Post.query.all()
        
        return render_template(
            'namely.html',
            diary=diary,
            name=name,
            user=current_user,
            map_key=os.getenv('GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_API_KEY_WAS_NOT_SET?!')
        )
        
  
        
    
    @app.route('/timely', methods=['GET'])
    def timely():
        time = request.args.get('time')
        #diary = Post.get_same_day_items(date)
        #diary = Post.query.get(date)
        diary = Post.query.all()
        
        return render_template(
            'timely.html',
            diary=diary,
            time=time,
            user=current_user,
            map_key=os.getenv('GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_API_KEY_WAS_NOT_SET?!')
        )

    @app.template_filter('timeago')
    def fromnow(date):
        return timeago.format(date, datetime.datetime.now())

        
      
     


    return app



app = create_app()
if __name__ == '__main__':
    port = int(os.environ.get("PORT",5000))
    app.run(host='127.0.0.1',port=port,debug=True)
    
    
