from google.appengine.ext import db


class Handyman(db.Model):
    email = db.EmailProperty (required = True)
    pw_hash = db.StringProperty(required = True)
    first_name = db.StringProperty
    last_name = db.StringProperty
    photo = db.BlobProperty
    address = db.PostalAddressProperty
    number = db.PhoneNumberProperty (required = True)
    skills = db.StringListProperty #skill | license number | hourly rate
    id_verification = db.BooleanProperty
    background_check = db.BooleanProperty
    professional_rating = db.StringProperty #total points | average | number of reviews
    quality_rating = db.StringProperty #total points | average | number of reviews
    time_rating = db.StringProperty #total points | average | number of reviews
    overall_rating = db.StringProperty #total points | average | number of reviews
    reviews = db.StringListProperty #overall rating | client | date | written review
    job_list = db.StringListProperty
    earnings = db.FloatProperty
    availability = db.DateTimeProperty #days and hours
    
class Client(db.Model):
    email = db.EmailProperty (required = True)
    pw_hash = db.StringProperty(required = True)
    first_name = db.StringProperty
    last_name = db.StringProperty
    photo = db.BlobProperty
    address = db.PostalAddressProperty
    number = db.PhoneNumberProperty (required = True)
    overall_rating = db.StringProperty #total points | average | number of reviews
    reviews = db.StringListProperty #overall rating | handyman | date | written review
    job_list = db.StringListProperty
    spending = db.FloatProperty
    
class Jobs(db.Model):
    discription = db.StringProperty
    client_name = db.StringProperty
    handyman_name = db.StringProperty
    posted = db.DateTimeProperty
    scheduled = db.DateTimeProperty
    started = db.DateTimeProperty
    finished = db.DateTimeProperty
    time = db.FloatProperty
    cost = db.FloatProperty
    client_rating = db.StringProperty #overall review
    handman_rating = db.StringProperty #professional quality time overall review