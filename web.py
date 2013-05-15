import cgi

from google.appengine.api import users

#Import Quote Function from URL Library
from urllib import quote

import webapp2
import jinja2

import json
import os
import math

#sessions for gae
from webapp2_extras import sessions

#Import Parse_QueryString from URL Parse
from urlparse import parse_qs

#Import URLFetch from Google App Engine API
from google.appengine.api import urlfetch


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+"/templates"))


FB_APP_id = "386956621420017"
FB_APP_secret = "1a22965d8111b9e13323202150150aed"
redir_url = "http://www.crewcatcher.appspot.com/home"

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


class MainPage(BaseHandler):
    def get(self):
        template_values = {
        } 
        template = jinja_environment.get_template('landingpage.html')
        self.response.out.write(template.render(template_values))   


class SignIn(BaseHandler):
    def get(self):
        user = None
        if self.session.get('user'):
            user = self.session.get('user')

        if user == None:
            if self.request.get('code') == '':
                self.redirect('https://www.facebook.com/dialog/oauth?client_id=' + FB_APP_id + '&redirect_uri=' + quote(redir_url) + \
                '&scope=')
            else:
                self.redirect('/failed')
        else:
            self.response.write('you are logged in : ' + user);

class Home(BaseHandler):
    def get(self):
        token_url = 'https://graph.facebook.com/oauth/access_token?client_id=' + \
        FB_APP_id + '&redirect_uri=' + quote(redir_url) + \
        '&client_secret=' + FB_APP_secret + '&code=' + self.request.get('code') 

        token_res = urlfetch.fetch(token_url)
        params = parse_qs(token_res.content)

        access_token = None
        try:
            access_token = params['access_token'][0]
        except:
            self.redirect('/');

        self.session['user'] = access_token

        # use the facebook api
        graph_url = u'https://graph.facebook.com'

        # query
        api_string = u'/me'

        api_request_url = graph_url + api_string + u'?access_token=' + access_token

        #Fetch the Response from Graph API Request
        api_response = urlfetch.fetch(api_request_url)

        #Get the contents of the Response
        json_response = api_response.content

        #Convert the JSON String into a dictionary
        api_answer = json.loads(json_response)

        template_values = {
            'name': api_answer['name']
        } 
        template = jinja_environment.get_template('main.html')
        self.response.out.write(template.render(template_values))   


class Test(BaseHandler):
    def get(self):
        template_values = {
        } 
        template = jinja_environment.get_template('main.html')
        self.response.out.write(template.render(template_values))   


# config is a dict containing the key for the sessions
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'key-for-crew-catch!',
}


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signin', SignIn),
    ('/home', Home),
    ('/test', Test),
  
], config = config, debug=True)        

