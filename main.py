import os
import webapp2
import jinja2
import hashlib
import re
import random
import string
import json
import datetime
import cgi
import urllib
import csv
from google.appengine.api import mail
from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import search
from google.appengine.ext import blobstore

template_dir = os.path.join(os.path.dirname(__file__), 'html')
jinja_env = jinja2.Environment(autoescape = True,
                               loader = jinja2.FileSystemLoader(template_dir))

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_html(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def email(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_html(template, **kw))
    def valid_cookie(self):
        cookie = self.request.cookies.get('name')
        if cookie:
            user_id = cookie.split('|')[0]
            if user_id.isdigit():
                user = Users.get_by_id(int(user_id))
                if user and valid_id(cookie, user.pw_hash):
                    return user
        else: None
    def set_cookie(self, user_id, pw_hash):
        cookie = make_id_hash(user_id, pw_hash)
        self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % cookie)            
    
# Google App Engine DataStore
class Tazks(ndb.Model):
    category = ndb.StringProperty (required = True)
    title = ndb.StringProperty (required = True)
    discription = ndb.StringProperty (indexed = True)
    photo = ndb.BlobProperty (indexed = False)
    def render(self):
        return render_str("tazks.html", t = self)

class Price(ndb.Model):
    tazk = ndb.KeyProperty (indexed = True, required = True)
    handy = ndb.KeyProperty (indexed = True, required = True)
    discription = ndb.StringProperty (indexed = True)
    price = ndb.FloatProperty (indexed = True)
    per = ndb.StringProperty (indexed = False)
    photo = ndb.BlobProperty (indexed = False)
    overall = ndb.FloatProperty (indexed = True)
    
class Rating(ndb.Model):
    total = ndb.IntegerProperty (indexed = False)
    number = ndb.IntegerProperty (indexed = False)
    average = ndb.FloatProperty (indexed = False)
    
class Rate(ndb.Model):
    professional = ndb.IntegerProperty (indexed = False)
    quality = ndb.IntegerProperty (indexed = False)
    overall = ndb.IntegerProperty (indexed = True)
    review = ndb.StringProperty (indexed = False)
    comment = ndb.StringProperty (indexed = False)
    created = ndb.DateTimeProperty (auto_now_add = True)

class Messages(ndb.Model):
    message = ndb.StringProperty (required = True)
    created = ndb.DateTimeProperty (auto_now_add = True)

class Address(ndb.Model):
    type = ndb.StringProperty (indexed = True)
    street = ndb.StringProperty (indexed = False)
    city = ndb.StringProperty (indexed = False)
    state = ndb.StringProperty (indexed = False)
    zipcode = ndb.StringProperty (indexed = False)
    country = ndb.StringProperty (indexed = False)
    geo = ndb.GeoPtProperty (indexed = True)
    
class Jobs(ndb.Model):
    client = ndb.KeyProperty (indexed = True)
    client_rating = ndb.StructuredProperty (Rate, indexed = False)
    address = ndb.StringProperty (indexed = False)
    handyman = ndb.KeyProperty (indexed = True)
    handy_rating = ndb.StructuredProperty (Rate, indexed = False)
    messages = ndb.StructuredProperty (Messages, repeated = True)
    scheduled = ndb.DateTimeProperty (indexed = False, auto_now = True)
    completed = ndb.DateTimeProperty (indexed = True, auto_now = True)
    labor = ndb.FloatProperty (indexed = False)
    supplies = ndb.FloatProperty (indexed = False)
    discount = ndb.FloatProperty (indexed = False)
    tax = ndb.FloatProperty (indexed = False)
    earning = ndb.FloatProperty (indexed = False)
    tip = ndb.FloatProperty (indexed = False)
        
class Users(ndb.Model):
    active = ndb.BooleanProperty (default = False)
    activate = ndb.StringProperty (required = True)
    created = ndb.DateTimeProperty (auto_now_add = True)
    email = ndb.StringProperty (required = True)
    pw_hash = ndb.StringProperty (required = True)
    first_name = ndb.StringProperty (required = True)
    last_name = ndb.StringProperty (required = True)
    sex = ndb.StringProperty (indexed = False, choices=['','male', 'female'], default = '')
    photo = ndb.BlobProperty (indexed = False)
    addresses = ndb.StructuredProperty (Address, repeated = True)
    number = ndb.StringProperty (indexed = False, default = '')
    enable_text = ndb.StringProperty (indexed = False, default = 'off')
    dob = ndb.DateProperty (indexed = False)
    id_photo = ndb.BlobProperty (indexed = False)
    id_exp = ndb.DateProperty (indexed = False)
    id_verified = ndb.BooleanProperty (indexed = False, default = False)
    @classmethod
    def by_email(cls, email):
        u = Users.query(Users.email == email).get()
        return u

    #Handyman
    handy = ndb.BooleanProperty (default = False)
    radius = ndb.IntegerProperty (default = 25)
    services = ndb.KeyProperty (indexed = True, repeated = True)
    background = ndb.BooleanProperty (default = False)
    licensed = ndb.BooleanProperty (default = False)
    license = ndb.StringProperty (repeated = True, indexed = False)
    insured = ndb.BooleanProperty (default = False)
    handy_rating = ndb.StructuredProperty (Rating, indexed = False)
    invoices = ndb.KeyProperty (repeated = True, indexed = True)
    earnings = ndb.FloatProperty (indexed = False)
    
    #Client
    client_rating = ndb.StructuredProperty (Rating, indexed = False)
    receipts = ndb.KeyProperty (repeated = True, indexed = True)
    spending = ndb.FloatProperty (indexed = False)

class Photos(ndb.Model):
    photo = ndb.BlobProperty (required = True)
    
class Upload(Handler):
    def get(self):
        self.write('<form enctype="multipart/form-data" method="POST"><input type="radio" name="type" value="photo">Photo<input type="radio" name="type" value="worksheet">Worksheet<br>Upload File: <input type="file" name="file"><br><input type="submit" name="submit" value="Upload"></form>')
    def post(self):
        t = self.request.get('type')
        f = self.request.get('file')
        if t == 'photo':
            new = Photos(photo=f)
            new.put()
            self.write('Done!')
        else:
            csv_f = csv.reader(f.split('\n'), delimiter=',')
            self.write('<h2>File contains:<h2>')
            for row in csv_f:
                category, title, cost = row
                self.write('%s: %s - %s <br>' % (category, title, cost))
                tazk = Tazks(category=category, title=title, cost=cost)
                tazk.put()
    
# Securing Passwords
support = "TAZKS Support <tazks.llc@gmail.com>"
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))
def make_pw_hash(activate, pw, salt = ""):
    if salt == "":
        salt = make_salt()
    h = hashlib.sha256(activate + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)
def valid_pw(activate, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(activate, password, salt)
def users_key(group = 'default'):
    return ndb.Key.from_path('users', group)

# Making and validating Cookies
def make_id_hash(user_id, pw):
    salt = pw.split(',')[-1]
    h = hashlib.sha256(user_id + salt).hexdigest()
    return '%s|%s' % (user_id, h)
def valid_id (cookie, pw):
    user_id = cookie.split('|')[0]
    verify = make_id_hash(user_id, pw)
    return verify == cookie

# Start Page
class About(Handler):
    def render_new(self, email="", error=""):
        tazks = Tazks.query()
        self.render('about.html', email=email, error=error, tazks=tazks, base='unlogged.html')
    def get(self):
        self.render_new()
    def post(self):
        email = self.request.get('email').lower()
        password = self.request.get('password')
        user = Users.by_email(email)
        if email and user and user.active and valid_pw(user.activate, password, user.pw_hash):
            self.set_cookie(str(user.key.id()), user.pw_hash)
            self.redirect('/dashboard')
        elif (user.active == False):
            self.redirect('/activate')
        else:
            self.render_new(email, "Invalid email and password.")

# Signs In User
class SignIn(Handler):
    def render_new(self, email="", error=""):
        self.render('signin.html', email=email, error=error, base='unlogged.html')
    def get(self):
        self.render_new()
    def post(self):
        email = self.request.get('email').lower()
        password = self.request.get('password')
        user = Users.by_email(email)
        if email and user and user.active and valid_pw(user.activate, password, user.pw_hash):
            self.set_cookie(str(user.key.id()), user.pw_hash)
            self.redirect('/dashboard')
        elif (user.active == False):
            self.redirect('/activate')
        else:
            self.render_new(email, "Invalid email and password.")

# Signs up New Users 
class SignUp(Handler):
    def render_new(self, first_name = "", last_name = "", email = "", error_email=""):
        self.render('signup.html', first_name=first_name, last_name=last_name, email=email, error_email=error_email, base='unlogged.html')
    def get(self):
        self.render_new()
    def post(self):
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email').lower()
        password = self.request.get('password')
        if Login.by_email(email):
            error_email = "Looks like your twin already registered you."
            self.render_new(first_name, last_name, email, error_email)
        else:
            subject = "Confirm your registration"
            activate = str(random.randint(10000, 99999))
            body = self.email('activate.txt', first_name=first_name, activate=activate)
            mail.send_mail(support, email, subject, body)
            pw_hash = make_pw_hash(activate, password)
            new = Users(first_name=first_name, last_name=last_name, email=email, pw_hash=pw_hash, activate=activate)
            home = Address(type='home', street='', city='', state='', zipcode='', country='USA')
            new.addresses.append(home)
            photo = Photos.get_by_id(6680220333506560)
            photo.photo = images.resize(photo.photo, 250, 350)
            new.photo = photo.photo
            user = new.put()
            self.set_cookie(str(user.id()), pw_hash)
            self.redirect('/activate')

# Activates New Users
class Activate(Handler):
    def render_new(self, email="", error=""):
        self.render('activate.html', email=email, error=error)
    def get(self):
        self.render_new("", "Please check your email for your activation code.")
    def post(self):
        email = self.request.get('email').lower()
        password = self.request.get('password')
        activate = self.request.get('activate')
        user = Users.by_email(email)
        if user and (user.activate == activate) and valid_pw(user.activate, password, user.pw_hash):
            user.active = True
            user.put()
            self.set_cookie(str(user.key.id()), user.pw_hash)
            self.redirect('/dashboard')
        elif user and (user.activate != activate):
            self.render_new(email, "Please enter the activation code from you email.")
        else:
            self.render_new(email, "Invalid email and password.")

# Emails User with Forgotten Password
class Password(Handler):
    def render_new(self, email="", error=""):
        self.render('password.html', email=email, error=error)
    def get(self):
        self.render_new()
    def post(self):
        email = self.request.get('email').lower()
        user = Users.by_email(email)
        if user:
            body = self.email('password.txt', first_name=user.first_name, activate=user.activate)
            subject = "Reset Password"
            mail.send_mail(support, email, subject, body)
            self.redirect('/reset')
        else:
            self.render_new(email, "I didn't find that email.  Could you retype it?")

# Creates New Password with Code sent to Email
class Reset(Handler):
    def render_new(self, email="", error=""):
        self.render('reset.html', email=email, error=error)
    def get(self):
        self.render_new()
    def post(self):
        email = self.request.get('email').lower()
        activate = self.request.get('reset')
        password = self.request.get('password')
        user = Users.by_email(email)
        if user and (activate == user.activate):
            user.activate = str(random.randint(10000, 99999))
            user.pw_hash = make_pw_hash(user.activate, password)
            user.put()
            self.redirect('/dashboard')
        else:
            self.render_new(email, "My records don't match what you entered.  Please enter the email and reset code again.")     

# Dashboard: This should bring me to my welcome page with different things for users to do.
class Dashboard(Handler):
    def get(self):
        user = self.valid_cookie()
        tazks = Tazks.query()
        self.render('dashboard.html', tazks=tazks, base='logged.html')

class Tazk(Handler):
    def get(self):
        user = self.valid_cookie()
        tazk_id = self.request.get('tazk_id')
        tazk = Tazks.get_by_id(int(tazk_id))
        if not tazk:
            self.error(404)
            return
        if user:
            self.render('tazk.html', tazk=tazk, base='logged.html')
        else:
            self.render('tazk.html', tazk=tazk, base='unlogged.html')
        
# Updates Profile: To-Do: geolocation, verify text, reviews, rating stars, javascript not to submit invalid inputs
class Profile(Handler):
    def get(self):
        user = self.valid_cookie()
        self.render('profile.html', user = user)
    def post(self):
        user = self.valid_cookie()
        user.first_name = self.request.get('first_name')
        user.last_name = self.request.get('last_name')
        date_entry = self.request.get('dob')
        if date_entry:
            year, month, day = map(int, date_entry.split('-'))
            user.dob = datetime.date(year, month, day)
        user.sex = self.request.get('sex').lower()
        user.number = self.request.get('phone')
        user.enable_text = self.request.get('enable_text')
        photo = self.request.get('photo')
        street = self.request.get('street')
        city = self.request.get('city')
        state = self.request.get('state')
        zipcode = self.request.get('zipcode')
        new = Address(type='home', street=street, city=city, state=state, zipcode=zipcode, country='USA')
        user.addresses[0] = new
        if photo: 
            photo = images.resize(photo, 250, 350)
            user.photo = photo
        user.put()
        self.redirect('/profile')
                
class Image(webapp2.RequestHandler):
    def get(self):
        user_key = ndb.Key(urlsafe=self.request.get('img_id'))
        user = user_key.get()
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(user.photo)

class Account(Handler):
    def get(self):
        user = self.valid_cookie()
        photo = "/img?img_id=%s" % (user.key.urlsafe())
        self.render('account_invoice.html', photo=photo, email=user.email)
class Payment(Handler):
    def get(self):
        user = self.valid_cookie()
        photo = "/img?img_id=%s" % (user.key.urlsafe())
        self.render('account_payment.html', photo=photo, email=user.email)
class Payout(Handler):
    def get(self):
        user = self.valid_cookie()
        photo = "/img?img_id=%s" % (user.key.urlsafe())
        self.render('account_payout.html', photo=photo, email=user.email)
        
# Changes Email & Password  
class Security(Handler):
    def render_new(self, user, message="", pw_message=""):
        photo = "/img?img_id=%s" % (user.key.urlsafe())
        self.render('account_security.html', photo=photo, email=user.email, message=message, pw_message=pw_message)
    def get(self):
        user = self.valid_cookie()
        self.render_new(user)
    def post(self):
        user = self.valid_cookie()
        update_email = self.request.POST.get('update_email', None)
        change_pw = self.request.POST.get('change_password', None)
        if update_email:
            email = self.request.get('email')
            if Users.by_email(email):
                message = "Email NOT updated: Looks like your twin already registered you."
            else:
# Send Email to old email address of change in email address.
                user.email = email
                user.put()
                message = "Your email has been updated."
            self.render_new(user, message)
        if change_pw:
            old_pw = self.request.get('old')
            new_pw = self.request.get('password')
            if valid_pw(user.activate, old_pw, user.pw_hash):
# Send Email of change in password.
                user.pw_hash = make_pw_hash(user.activate, new_pw)
                user.put()
                self.set_cookie(str(user.key.id()), user.pw_hash)
                pw_message = "Your Password has been changed."
            else:
                pw_message = "Your Old Password does NOT match our records!"
            self.render_new(user, "", pw_message)

# Professionals check their skills
class MyServices(Handler):
    def get(self):
        user = self.valid_cookie()
        services = len(user.services)
        tazks = Tazks.query()
        self.render('service_choose.html', tazks=tazks, services=services)

class Provided(Handler):
    def get(self):
        user = self.valid_cookie()
        self.render('service_provided.html', user = user)
                            
class SetPrice(Handler):
    def get(self):
        user = self.valid_cookie()
        tazk_ids = self.request.get('items')
        if tazk_ids != '':
            tazk_id = tazk_ids.split(',')
            services = []
            for t in tazk_id:
                services.append(Tazks.get_by_id(int(t)))
            self.render('service_price.html', services = services, user = user)
        else: self.redirect('/myservices')
    def post(self):
        user = self.valid_cookie()
        tazk_ids = self.request.get('items')
        prices = self.request.get_all('price')
        discriptions = self.request.get_all('discription')
        photos = self.request.get_all('photo')
        pers = self.request.get_all('per')
        tazk_id = tazk_ids.split(',')
        count = 0;
#        prices = Price.query(Price.handy == user.key)        
        for t in tazk_id:
            old = Tazks.get_by_id(int(t))
            new = Price(tazk=old.key, handy=user.key, discription=discriptions[count], price=float(prices[count]))
            if photos[count]: 
                photos[count] = images.resize(photo, 250, 350)
                new.photo = photos[count]
            else: new.photo = old.photo
            new.put()
            user.services.append(new.key)
            count += 1
        self.write(new)
#        self.redirect('/provided')

class MyJobs(Handler):
    def get(self):
        self.render('myjobs.html')

class InBox(Handler):
    def get(self):
        self.render('inbox.html')
        
class Base(Handler):
    def get(self):
        self.render('base.html', tazks=tazks)

class Update(Handler):
    def get(self):
        tazk_id = self.request.get('tazk_id')
        if tazk_id:
            tazk = Tazks.get_by_id(int(tazk_id))
            self.render('update.html', tazk=tazk)
        else: self.redirect('/new')
    def post(self):
        tazk_id = self.request.get('tazk_id')
        tazk = Tazks.get_by_id(int(tazk_id))
        title = self.request.get('title')
        category = self.request.get('category')
        discription = self.request.get('discription')
        photo = self.request.get('photo')
        tazk.category, tazk.title, tazk.discription = category, title, discription
        if photo: 
            photo = images.resize(photo, 250, 350)
            tazk.photo = photo
        tazk.put()
        self.redirect('/base')

class New(Handler):
    def get(self):
        self.render('new.html')
    def post(self):
        title = self.request.get('title')
        category = self.request.get('category')
        discription = self.request.get('discription')
        photo = self.request.get('photo')
        if photo:
            photo = images.resize(photo, 250, 250)
            new = Tazks(category=category, title=title, photo=photo, discription=discription)
        else: new = Tazks(category=category, title=title)
        tazk = new.put()
        self.redirect('/base')

# Log Out: Need to create link to help me log out.
class LogOut(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'name=; Path=/')            
        self.redirect('/')

app = webapp2.WSGIApplication([('/', About),
                               ('/signin', SignIn),
                               ('/signup', SignUp),
                               ('/activate', Activate),
                               ('/password', Password),
                               ('/reset', Reset),
                               ('/dashboard', Dashboard),
                               ('/inbox', InBox),
                               ('/myjobs', MyJobs),
                               ('/myservices', MyServices),
                               ('/provided', Provided),
                               ('/price', SetPrice),
                               ('/profile', Profile),
                               ('/account', Account),
                               ('/payment', Payment),
                               ('/payout', Payout),
                               ('/security', Security),
                               ('/upload', Upload),
                               ('/base', Base),
                               ('/update', Update),
                               ('/new', New),
                               ('/tazk', Tazk),
                               ('/img', Image),
                               ('/logout', LogOut)],
                              debug = True)