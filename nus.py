# Handlers for logged in pages

import cgi
import datetime
import urllib
import webapp2
import jinja2
import os

from google.appengine.ext import db
from google.appengine.api import users

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates"))

# Datastore definition
class Profile(db.Model):
  """Models an individual with an name, sex, email, fb_link, linkedin_link, \
  orbital_level, orbital_country, preference, and date. The email, which \
  should be unique is used as key. """
  name = db.StringProperty()
  sex = db.StringProperty()
  email = db.StringProperty()
  fb_link = db.StringProperty()
  linkedin_link = db.StringProperty()
  Boctok = db.BooleanProperty()
  Gemini = db.BooleanProperty()
  Apollo11 = db.BooleanProperty()
  Apollo11Mentoring = db.BooleanProperty()
  orbital_country = db.StringProperty()
  preference = db.StringProperty(multiline=True)
  admin = db.BooleanProperty()
  date = db.DateTimeProperty(auto_now_add=True)

# These classes generates pages from templates
class MainPage(webapp2.RequestHandler):
  """ Front page for those logged in """
  def get(self):
    user = users.get_current_user()
    if user:  # signed in already
      template_values = {
        'home': self.request.host_url,
        'user_mail': users.get_current_user().email(),
        'logout': users.create_logout_url(self.request.host_url),
        } 
      template = jinja_environment.get_template('front.html')
      self.response.out.write(template.render(template_values))
    else:
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))

class NUSPolicy(webapp2.RequestHandler):
  """ Handler for privacy policy page."""
  def get(self):
    user = users.get_current_user()
    if user: # if logged in 
      template_values = {
        'home': self.request.host_url,
        'user_mail': users.get_current_user().email(),
        'logout': users.create_logout_url(self.request.host_url),
        } 
      template = jinja_environment.get_template('privacy.html')
      self.response.out.write(template.render(template_values))    
    else: # not logged in 
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))

class Login(webapp2.RequestHandler):
  """ Checks whether profile already exists, if not create profile """
  def get(self):
    user = users.get_current_user()
    if user:  # signed in already
      template_values = {
        'home': self.request.host_url,
        'user_mail': users.get_current_user().email(),
        'logout': users.create_logout_url(self.request.host_url),
        } 
      # Check whether profile exists
      db_key =  db.Key.from_path('Profile',users.get_current_user().email())
      profile = db.get(db_key)

      if profile == None:
        template = jinja_environment.get_template('getprofile.html')
      else:
        template = jinja_environment.get_template('front.html')
      self.response.out.write(template.render(template_values))
    else:
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))

class EditProfile(webapp2.RequestHandler):
  """ Retrieves profile and prefill the form for editing """
  def get(self):
    user = users.get_current_user()
    if user:  # signed in already

      # Retrieves profile
      db_key =  db.Key.from_path('Profile',users.get_current_user().email())
      profile = db.get(db_key)

      if profile != None:
        male_checked = female_checked = Boctok_checked = Gemini_checked = Apollo11_checked = Apollo11Mentoring_checked = "";
        
        # For filling in radio button for sex
        if profile.sex == 'Male':
          male_checked = 'checked'
        else:
          female_checked = 'checked'
          
        # For filling in radio button for Orbital level
        if profile.Boctok:
          Boctok_checked = 'checked'
        if profile.Gemini:
          Gemini_checked = 'checked'
        if profile.Apollo11:
          Apollo11_checked = 'checked'
        if profile.Apollo11Mentoring:
          Apollo11Mentoring_checked = 'checked'
      
        template_values = {
          'profile': profile,
          'male_checked': male_checked,
          'female_checked': female_checked,
          'Boctok_checked': Boctok_checked,
          'Gemini_checked': Gemini_checked,
          'Apollo11_checked': Apollo11_checked,
          'Apollo11Mentoring_checked': Apollo11Mentoring_checked,
          'preference': cgi.escape(profile.preference),  # html escaping
          'home': self.request.host_url,
          'user_mail': users.get_current_user().email(),
          'logout': users.create_logout_url(self.request.host_url),
          } 
        template = jinja_environment.get_template('editprofile.html')
        self.response.out.write(template.render(template_values))
      else:
        self.redirect('/login')
    else:
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))

class Search(webapp2.RequestHandler):
  """ Creates search form """
  def get(self):
    user = users.get_current_user()
    if user:  # signed in already
      template_values = {
        'home': self.request.host_url,
        'user_mail': users.get_current_user().email(),
        'logout': users.create_logout_url(self.request.host_url),
        } 
      template = jinja_environment.get_template('search.html')
      self.response.out.write(template.render(template_values))
    else:
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))

class Display(webapp2.RequestHandler):
  """Display the result of search query """
  def post(self):

    sex = self.request.get('sex')
    level = self.request.get('orbital_level')
    country = self.request.get('orbital_country')


    if country == "Anywhere":
      query = "SELECT * FROM Profile WHERE sex = '" + sex + "' AND " + level \
          + " = True ORDER BY date DESC"
    else:
      query = "SELECT * FROM Profile WHERE sex = '" + sex + "' AND " +\
          level + " = True AND orbital_country = '" + country + \
          "' ORDER BY date DESC"
    profiles = db.GqlQuery(query)
    user = users.get_current_user()
    if user:  # signed in already
      template_values = {
        'profiles': profiles,
        'level': level,
        'home': self.request.host_url,
        'user_mail': users.get_current_user().email(),
        'logout': users.create_logout_url(self.request.host_url),
        } 
      template = jinja_environment.get_template('display.html')
      self.response.out.write(template.render(template_values))
    else:
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))

class AdminDisplay(webapp2.RequestHandler):
  """ Creates page to get info for admin. Only user with admin priviledge \
  can access. Admin priviledge after user is registered through editing \
  the entity on the GAE admin dashboard. """
  def get(self):
    user = users.get_current_user()
    if user:  # signed in already
      db_key =  db.Key.from_path('Profile',users.get_current_user().email())
      profile = db.get(db_key) # Retrieve profile
      
      if profile.admin == True:
        profiles = db.GqlQuery("SELECT *"
                               "FROM Profile "
                               "ORDER BY date DESC")
        
        template_values = {
          'profiles': profiles,
          'home': self.request.host_url,
          'user_mail': users.get_current_user().email(),
          'logout': users.create_logout_url(self.request.host_url),
          } 
        template = jinja_environment.get_template('admin.html')
        self.response.out.write(template.render(template_values))
      else:
        self.redirect('/nus')
    else:
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))

# These classes process requests

class CreateProfile(webapp2.RequestHandler):
  """ Process data from user and creates a new profile """
  def post(self):
    if users.get_current_user():
      profile = Profile(key_name=users.get_current_user().email())
      profile.name = self.request.get('user_name')
      profile.email = users.get_current_user().email()
      profile.sex = self.request.get('sex')
      profile.fb_link = self.request.get('fb_link')
      profile.linkedin_link = self.request.get('linkedin_link')
      levels = self.request.get_all('orbital_level')
      profile.Boctok = ('Boctok' in levels)
      profile.Gemini = ('Gemini' in levels)
      profile.Apollo11 = ('Apollo11' in levels)
      profile.Apollo11Mentoring = ('Apollo11Mentoring' in levels)
      profile.orbital_country = self.request.get('orbital_country')
      profile.preference = self.request.get('preference')   
      profile.admin = False
      profile.put()
      self.redirect('/nus')
    else:
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))

class Edit(webapp2.RequestHandler):
  """ Edit the profile then stores it """
  def post(self):
    if users.get_current_user():
      # Get key from database
      db_key =  db.Key.from_path('Profile',users.get_current_user().email())
      profile = db.get(db_key) # Retrieve profile
      
      if self.request.get('delete')=='Yes': # Delete profile
        db.delete(profile)
        self.redirect(users.create_logout_url(self.request.host_url))
      else: # Edit profile
        profile.name = self.request.get('user_name')
        profile.sex = self.request.get('sex')
        profile.fb_link = self.request.get('fb_link')
        profile.linkedin_link = self.request.get('linkedin_link')
        levels = self.request.get_all('orbital_level')
        profile.Boctok = ('Boctok' in levels)
        profile.Gemini = ('Gemini' in levels)
        profile.Apollo11 = ('Apollo11' in levels)
        profile.Apollo11Mentoring = ('Apollo11Mentoring' in levels)
        profile.orbital_country = self.request.get('orbital_country')
        profile.preference = self.request.get('preference')   
        profile.put()
        self.redirect('/nus')
        
      
class Admin(webapp2.RequestHandler):
  """ Process admin request. Only user with admin priviledge can access \
  Admin priviledge after user is registered through editing the entity on\
  the GAE admin dashboard."""
  def post(self):
    user = users.get_current_user()
    if user:  # signed in already
      db_key =  db.Key.from_path('Profile',users.get_current_user().email())
      profile = db.get(db_key) # Retrieve profile
      
      if profile.admin == True:
        all = self.request.get('select_all')
        if all:
          profiles = db.GqlQuery("SELECT *"
                                 "FROM Profile ")
        else:
          selected = self.request.get_all('selected')
          profiles = db.GqlQuery("SELECT *"
                                 "FROM Profile "
                                 "WHERE email in :1",
                                 selected)
          db.delete(profiles)
          self.redirect('/nus')
      else:
        self.redirect('/nus')
    else:
      self.redirect(users.create_login_url(federated_identity='https://openid.nus.edu.sg/'))


app = webapp2.WSGIApplication([('/nus', MainPage),
                               ('/nuspolicy', NUSPolicy),
                               ('/login', Login),
                               ('/profile', CreateProfile),
                               ('/editprofile', EditProfile),
                               ('/search', Search),
                               ('/display', Display),
                               ('/admindisplay', AdminDisplay),
                               ('/edit', Edit),
                               ('/admin', Admin)],
                              debug=True)
