from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, PasswordField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class NewLocationForm(FlaskForm):
    description = StringField('Location description',
                           validators=[DataRequired(), Length(min=1, max=80)])
    lookup_address = StringField('Search address')

    coord_latitude = HiddenField('Latitude',validators=[DataRequired()])

    coord_longitude = HiddenField('Longitude', validators=[DataRequired()])

    submit = SubmitField('Create Location')
    
    
class SelectAreaForm(FlaskForm):
    lookup_address = StringField('Enter the name of a street, place or building')
    radius = IntegerField('Search radius (in meter)', 
                          validators=[DataRequired()])

    coord_latitude = HiddenField('Latitude',validators=[DataRequired()])

    coord_longitude = HiddenField('Longitude', validators=[DataRequired()])

    submit = SubmitField('Browse Diary')
    





class AddPosts(FlaskForm):
    content = StringField('Post content', validators=[DataRequired()])
    longitude = StringField('longitude', default='1')
    latitude = StringField('latitude',default='2')
    submit = SubmitField('save')
    
    
    
class RegistrationForm(FlaskForm):
    name = StringField(
        'Name',
        validators=
            [DataRequired(),
            Length(min=2, max=200)
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email()
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired()
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password')
        ]
    )
    submit = SubmitField('Sign up')




class LoginForm(FlaskForm):
    name = StringField(
        'Name',
        validators=[
            DataRequired()
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired()
        ]
    )

    remember = BooleanField('Remember me')

    submit = SubmitField('Login')