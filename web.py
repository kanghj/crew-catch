import cgi

# gae users library
from google.appengine.api import users

#gae datastore
from google.appengine.ext import db


from urllib import quote

import webapp2
import jinja2

import json
import os
import math
import datetime


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
redir_url = "http://www.crewcatcher.appspot.com/welcome"

# scope for facebook login
fb_scope = "user_likes, friends_likes"


# Datastore definitions
# modified from the giftbook example project shown during the orbital workshop
class Persons(db.Model):
    """Models a person identified by facebook id"""
    person_id = db.IntegerProperty(required=True)
    organisation = db.StringProperty()
    location = db.GeoPtProperty()
    interests = db.StringListProperty()
    events = db.ListProperty(int)


# Events should store a Person as parent, this Person is the host of the event
class Events(db.Model):
    """Models an event. Identified by events_id"""
    event_name = db.StringProperty(required=True)
    location = db.GeoPtProperty()
    event_datetime = db.DateTimeProperty(required=True)

    description = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)  # this date contains the datetime when the Event was created, not the event's datetime
 


# base handler, for supporting sessions
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
        # Returns a session using memcache
        backend = "memcache"

        return self.session_store.get_session(backend = backend)


# display the landing page
class MainPage(BaseHandler):
    def get(self):
        template_values = {
        } 
        template = jinja_environment.get_template('landingpage.html')
        self.response.out.write(template.render(template_values))   


# to log in using facebook
class SignIn(BaseHandler):
    def get(self):
        # check to see if user is logged in
        user = None
        if self.session.get('access_token'):
            user = self.session.get('access_token')

        if user == None:
            if self.request.get('code') == '':
                self.redirect('https://www.facebook.com/dialog/oauth?client_id=' + FB_APP_id + '&redirect_uri=' + quote(redir_url) + \
                '&scope=' + quote(fb_scope))
            else:
                self.redirect('/failed')
        else:
            self.response.write('you are logged in : fb access_token = ' + user);
            self.response.write('<a href="/profile"> click to go to profile </a> ' )
            self.response.write('<p><a href="/logout"> logout</a> ')

# to log out of facebook
class LogOut(BaseHandler):
    def get(self):
        self.session.pop('user_id')
        self.session.pop('access_token')
        self.session.pop('name')


        self.response.write("\nYou are logged out now.")
        self.redirect('/')


# logged in to facebook, redirects to another page
class Welcome(BaseHandler):
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

        self.session['access_token'] = access_token

        # use the facebook api
        graph_url = u'https://graph.facebook.com'

        # construct the query
        api_string = u'/me'

        api_request_url = graph_url + api_string + u'?access_token=' + access_token

        #Fetch the Response from Graph API Request
        api_response = urlfetch.fetch(api_request_url)

        #Get the contents of the Response
        json_response = api_response.content

        #Convert the JSON String into a dictionary
        api_answer = json.loads(json_response)
        

        # store user id and name in session data 
        user_id = int(api_answer['id'])
        self.session['user_id'] = user_id

        user_name = api_answer['name']
        self.session['name'] = user_name
        

        template_values = {
            'name': api_answer['name']
        } 

        # check to see if user already has a profile
        query = db.GqlQuery("SELECT * " +
                          "FROM Persons " +
                          "WHERE person_id = :1 ",
                          user_id)

        person = query.get()

        # if user does not have a profile, go to newprofile.html
        if (person == None):
            template = jinja_environment.get_template('newprofile.html')
            self.response.out.write(template.render(template_values))   
        else:
            #if user has a profile, go to home
            self.redirect('/home')



# class to use for testing
class Test(BaseHandler):
    def get(self):
        template_values = {
        } 
        template = jinja_environment.get_template('newprofile.html')
        self.response.out.write(template.render(template_values))   


class Home(BaseHandler):
    def get(self):
        template_values = {
        } 
        template = jinja_environment.get_template('home.html')
        self.response.out.write(template.render(template_values))  


# prints out the required facebook data for similar friends
class PrintSimilarFriends(BaseHandler):
    def get(self):
        try:
            access_token = self.session.get('access_token')
        except:
            self.redirect('/')

        #construct the fql query 

        # pages that the user likes
        firstquery = ('"myPages":' , '"SELECT page_id FROM page_fan WHERE uid=me()"')
        # friends of the user
        secondquery = ( '"friends":' , '"SELECT name, uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=me())"')
        # pages,friend that the user likes, that the user's friends like as well
        thirdquery = ( '"friendsLikes":', '"SELECT uid, page_id FROM page_fan WHERE uid IN (SELECT uid FROM #friends) and page_id IN (SELECT page_id FROM #myPages)"')
        # the pages's names from #friendsLikes
        fourthquery = ( '"pages":', '"SELECT page_id, name FROM page WHERE page_id IN (SELECT page_id FROM #friendsLikes)"')
        # get similar friends' names
        fifthquery = ( '"similarfriend":', '"SELECT name FROM user WHERE uid IN (SELECT uid FROM #friendsLikes)"')

        finalquery = '{' + firstquery[0]  + firstquery[1]  + ',' + \
                   secondquery[0]  + secondquery[1]  + ',' + \
                   thirdquery[0]  + thirdquery[1]  + ',' + \
                   fourthquery[0]  + fourthquery[1]  + ',' + \
                   fifthquery[0] + fifthquery[1] + '}' 

        queryurl = 'https://graph.facebook.com/fql?q=' + quote(finalquery) + '&access_token=' + access_token
       
        #Fetch the Response from Graph API Request 
        api_response = urlfetch.fetch(queryurl)

        #Get the contents of the Response
        json_response = api_response.content

        #Convert the JSON String into a dictionary
        api_answer = json.loads(json_response)

        # if there is error, print out the error for debugging
        # otherwise print the json
        try:
            self.response.write(api_answer['error'])
            self.response.write('\n' + finalquery)
        except:
            similarfriends = {}
            friends = api_answer['data'][4]["fql_result_set"]
            for friendsdata in friends:
                friend = friendsdata["name"]
                try:
                    similarfriends[friend] += 1
                except:
                    similarfriends[friend] = 1

            #todo: make another fql query to get friend's names
            self.response.headers['Content-Type'] = 'application/json' 
            self.response.write(json.dumps(similarfriends))
        


# class to get data from user to fill in profile
class ReceiveData(BaseHandler):
    def post(self):
        try:
            user_id = self.session.get('user_id')
        except:
            self.redirect('/')


        lat = self.request.get('lat')
        lng = self.request.get('lng')
        location = db.GeoPt(lat=lat, lon=lng)

        org = self.request.get('organisation')

        person_id = int(user_id)
        #person_id = 12345 # for testing locally

        # self.response.write(lat + ',' + lng) # for debugging purposes
        person = Persons(person_id = person_id ,
                        organisation = org,
                        location = location )
        person.put()


# displays the user's profile
class Profile(BaseHandler):
    def get(self):
        person_id = None
        try:
            user_id = self.session.get('user_id')
            person_id = int(user_id)
        except:
            self.redirect('/')
        
        #person_id = 12345 # for testing locally

        query = db.GqlQuery("SELECT * " +
                          "FROM Persons " +
                          "WHERE person_id = :1 ",
                          person_id)

        person = query.get()


        template_values = {
            'person' : person
        } 
        template = jinja_environment.get_template('profile.html')
        self.response.out.write(template.render(template_values))   
        

# make a new event
class MakeNewEvent(BaseHandler):
    def post(self):
        try:
            user_id = self.session.get('user_id')
        except:
            self.redirect('/')
        
        person_id = int(user_id)
        #person_id = 12345 # for testing locally

        query = db.GqlQuery("SELECT * " +
                          "FROM Persons " +
                          "WHERE person_id = :1 ",
                          person_id)

        person = query.get()

        if person == None:
            self.redirect('/error&personid=%s' % (person_id,))   # user needs to create a profile first
        else:

          name = self.request.get('eventname')

          month = int(self.request.get('month'))
          day = int(self.request.get('day'))
          hour = int(self.request.get('hour'))
          event_datetime = datetime.datetime(year = datetime.datetime.today().year, month = month, day = day, hour = hour)

          lat = self.request.get('lat')
          lng = self.request.get('lng')
          location = db.GeoPt(lat=lat, lon=lng)

          description = self.request.get('description')
          
          parent_key = person.key()

          event = Events(parent = parent_key,
                        event_name = name,
                        event_datetime = event_datetime,
                        location = location,
                        description = description)

          event.put()

          # update the person to have the new event
          event_key = event.key().id()
          person.events.append(event_key)
          person.put()


# display form to make new event
class NewEvent(BaseHandler):
    def get(self):
        self.session['foo'] = 'bar'

        template_values = {
        } 
        template = jinja_environment.get_template('newevent.html')
        self.response.out.write(template.render(template_values))   


# prints sessions data, for debugging
class SessionData(BaseHandler):
    def get(self):
        try:
            user_id = self.session.get('user_id')
            access_token = self.session.get('access_token')
            person_id = int(user_id)
        except:
            self.redirect('/')
        
        atoken = access_token
        userid = user_id

        self.response.headers['Content-Type'] = 'application/json' 
        self.response.write(atoken)
        self.response.write(userid)




#config is a dict containing the key for the sessions
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'key-for-crew-catch!',
}

# handlers
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signin', SignIn),
    ('/logout', LogOut),
    ('/welcome', Welcome),
    ('/home', Home),
    ('/getsimilarfriends', PrintSimilarFriends),
    ('/test', Test),
    ('/setprofile', ReceiveData),
    ('/profile', Profile),
    ('/makeevent', MakeNewEvent),
    ('/newevent', NewEvent),
    ('/getsessiondata', SessionData),

], config = config, debug=True)        

