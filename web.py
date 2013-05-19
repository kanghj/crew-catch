import cgi

# gae users library
from google.appengine.api import users

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


# facebook app id and app secret
FB_APP_id = "386956621420017"
FB_APP_secret = "1a22965d8111b9e13323202150150aed"
redir_url = "http://www.crewcatcher.appspot.com/home"

fb_scope = "user_likes, friends_likes"

# base handler, for sessions
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

# prints the landing page
class MainPage(BaseHandler):
    def get(self):
        template_values = {
        } 
        template = jinja_environment.get_template('landingpage.html')
        self.response.out.write(template.render(template_values))   


# to login to facebook
class SignIn(BaseHandler):
    def get(self):
        # check to see if user is logged in
        user = None
        if self.session.get('user'):
            user = self.session.get('user')

        if user == None:
            if self.request.get('code') == '':
                self.redirect('https://www.facebook.com/dialog/oauth?client_id=' + FB_APP_id + '&redirect_uri=' + quote(redir_url) + \
                '&scope=' + quote(fb_scope))
            else:
                self.redirect('/failed')
        else:
            self.response.write('you are logged in : ' + user);

# to logout
class LogOut(BaseHandler):
    def get(self):
        if (self.session.get('user')):
            self.session['user'] = None
        self.response.write("\nYou are logged out now.")
        self.redirect('/')


# logged in to facebook, prints the user's name
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


# class to use for testing
class Test(BaseHandler):
    def get(self):
        template_values = {
        } 
        template = jinja_environment.get_template('main.html')
        self.response.out.write(template.render(template_values))   



# prints out the required facebook data for friends' likes in json
class PrintFriendsLikes(BaseHandler):
    def get(self):
        try:
            access_token = self.session.get('user')
        except:
            self.redirect('/')

        #construct the query for fql
        firstquery = ('"myPages":' , '"SELECT page_id FROM page_fan WHERE uid=me()",')
        secondquery = ( '"friends":' , '"SELECT name, uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=me())",')
        thirdquery = ( '"friendsLikes":', '"SELECT uid, page_id FROM page_fan WHERE uid IN (SELECT uid FROM #friends) and page_id IN (SELECT page_id FROM #myPages)",')
        fourthquery = ( '"pages":', '"SELECT page_id, name FROM page WHERE page_id IN (SELECT page_id FROM #friendsLikes)"')
       
        finalquery = '{' + firstquery[0]  + firstquery[1]  + \
                   secondquery[0]  + secondquery[1]  + \
                   thirdquery[0]  + thirdquery[1]  + \
                   fourthquery[0]  + fourthquery[1]  + '}' 

        #self.response.write(finalquery)
        #queryurl = 'https://graph.facebook.com/fql?q=' + quote('{' + firstquery[0]  + firstquery[1]  + \
        #           secondquery[0]  + secondquery[1]  + \
        #           thirdquery[0]  + thirdquery[1]  + \
        #           fourthquery[0]  + fourthquery[1]  + '}' )+ \
        #           '&access_token=' + access_token

        queryurl = 'https://graph.facebook.com/fql?q=' + quote(finalquery) + '&access_token=' + access_token
        #Fetch the Response from Graph API Request 
        api_response = urlfetch.fetch(queryurl)

        #Get the contents of the Response
        json_response = api_response.content

        #Convert the JSON String into a dictionary
        api_answer = json.loads(json_response)

        try:
            self.response.write(api_answer['error'])
            self.response.write('\n' + finalquery)
        except:
            self.response.headers['Content-Type'] = 'application/json' 
            self.response.write(json.dumps(api_answer))


# class to get data from user
class ReceiveData(BaseHandler):
    def post(self):
        lat = self.request.get('lat')
        lng = self.request.get('lng')
        self.response.write(lat + ',' + lng)

# config is a dict containing the key for the sessions
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'key-for-crew-catch!',
}
    

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signin', SignIn),
    ('/logout', LogOut),
    ('/home', Home),
    ('/test', Test),
    ('/getfriendslikes', PrintFriendsLikes),
    ('/setposition', ReceiveData),
  
], config = config, debug=True)        

