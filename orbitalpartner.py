# Handlers for pages that do not require log in

import urllib
import webapp2
import jinja2
import os

from google.appengine.api import users

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates"))

class MainPage(webapp2.RequestHandler):
  """ Handler for the front page."""
  def get(self):
    user = users.get_current_user()
    if user:   # if logged in
      self.redirect('/nus') # redirect to logged in front page
    else: # not logged in      
      template_values = { # to be passed to jinja2 template
        'home': self.request.host_url,
        }
      template = jinja_environment.get_template('front.html')
      self.response.out.write(template.render(template_values))
      
class Privacy(webapp2.RequestHandler):
  """ Handler for privacy policy page."""
  def get(self):
    user = users.get_current_user()
    if user: # if logged in 
      self.redirect('/nusprivacy')
    else: # not logged in 
      template_values = {
        'home': self.request.host_url,
        }
      template = jinja_environment.get_template('privacy.html')
      self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([('/', MainPage), ('/policy', Privacy)],
                              debug=True)
