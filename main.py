from google.appengine.ext import ndb
import webapp2
import json
import random
import string
import logging

def getRandomId():
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(6)])

class BaseHandler(webapp2.RequestHandler):
    def handle_exception(self, exception, debug):
        # Log the error.
        logging.exception(exception)

        # Set a custom message.
        self.response.write('Forbidden.')

        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
        else:
            self.response.set_status(403)

class Boat(ndb.Model):
    id_num = ndb.StringProperty(required=True)
    name = ndb.StringProperty()
    craft_type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty(default=True)

class BoatHandler(BaseHandler):
    def post(self):
        boat_request = json.loads(self.request.body)
        new_boat = Boat(id_num=getRandomId(), name=boat_request['name'], craft_type=boat_request['craft_type'], length=boat_request['length'])
        newKey = new_boat.put()
        print newKey
        boat_dict = new_boat.to_dict()
        #boat_dict['self'] = '/boat/' + new_boat.key.urlsafe()
        boat_dict['self'] = new_boat.key.urlsafe()
        self.response.write(json.dumps(boat_dict))

    def get(self, id=None):
        if id:
            b = ndb.Key(urlsafe=id).get()
            b_dict = b.to_dict()
            b_dict['self'] = '/boat/' + id
            self.response.write(json.dumps(b_dict))
        else:
            boat_query = [get_boat_query.to_dict() for get_boat_query in Boat.query()]
            self.response.write(json.dumps(boat_query))

    def patch(self, id=None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            request_body = json.loads(self.request.body)
            print type(request_body)
            self.response.write(self.request.body)
            if 'name' in request_body:
                print request_body['name']
                boat.name = request_body['name']
            if 'type' in request_body:
                print request_body['type']
                boat.craft_type = request_body['type']
            if 'length' in request_body:
                print request_body['length']
                try:
                    boat.length = request_body['length']
                except TypeError:
                    self.abort(403, "Length is not an integer")
            boat.put()

class Slip(ndb.Model):
    id_num = ndb.StringProperty(required=True)
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date =ndb.StringProperty()

class SlipHandler(webapp2.RequestHandler):
    def post(self):
        slip_request = json.loads(self.request.body)
        new_slip = Slip(id_num=getRandomId(), number=slip_request['number'])
        new_slip.put();
        slip_dict = new_slip.to_dict()
        #slip_dict['self'] = '/slip/' + new_slip.key.urlsafe()
        slip_dict = new_slip.key.urlsafe()
        self.response.write(json.dumps(slip_dict))

    #get a single slip or all slips
    def get(self, id=None):
        if id:
            s = ndb.Key(urlsafe=id).get()
            s_dict = s.to_dict()
            s_dict['self'] = '/slip/' + id
            self.response.write(json.dumps(s_dict))
        else:
            slip_query = [get_slip_query.to_dict() for get_slip_query in Slip.query()]
            self.response.write(json.dumps(slip_query))

    #update slip number
    def patch(self, slip_id=None):
        if slip_id:
            slip = ndb.Key(urlsafe=slip_id).get()
            all_slips = [get_all_slips.to_dict() for get_all_slips in Slip.query()]
            if self.request.body:
                request_body = json.loads(self.request.body)
                #if the user provided a number check it out and use it
                if 'number' in request_body:
                    existingNumber = False
                    for dic in all_slips:
                        if dic['number'] == request_body['number']:
                            existingNumber = True
                    if existingNumber == True:
                        #print "number is already in use"
                        self.abort(400, "Number is already in use.")
                    else:
                        try:
                            slip.number = request_body['number']
                            slip.put()
                        except:
                            self.abort(400, "Number is not an integer.")
                #otherwise generate a number
                else:
                    self.abort(404)
            else:
                highest_slip_number = 0
                for dic in all_slips:
                    temp = dic['number']
                    if temp > highest_slip_number:
                        highest_slip_number = temp
                print highest_slip_number
                print highest_slip_number + 1
                slip.number = highest_slip_number + 1
                slip.put()

    def put(self, slip_id=None):
        if slip_id:
            slip = ndb.Key(urlsafe=slip_id).get()
            request_body = json.loads(self.request.body)

            #change the current boat in slip to at_sea = True
            boat = ndb.Key(urlsafe=slip.current_boat).get()
            boat.at_sea = True
            boat.put()

            #assign new boat to slip
            slip.current_boat = request_body['boat']
            slip.arrival_date = request_body['date']
            slip.put()

            #set new boat to at_sea = False
            boat = ndb.Key(urlsafe=request_body['boat']).get()
            boat.at_sea = False
            boat.put()

    #def boatAtSlip(self, slip_id=None):
        #if slip_id:
            #slip = ndb.Key(urlsafe=slip_id).get()
            #slip_boat = slip.current_boat
            #boat = ndb.Key(urlsafe=slip_boat).get()
            #boat_dict = boat.to_dict()
            #self.response.write(json.dumps(boat_dict))

class BoatAtSlipHandler(webapp2.RequestHandler):
    #gets a boat at a slip
    def get(self, slip_id=None):
        if slip_id:
            slip = ndb.Key(urlsafe=slip_id).get()
            slip_boat = slip.current_boat
            boat = ndb.Key(urlsafe=slip_boat).get()
            boat_dict = boat.to_dict()
            self.response.write(json.dumps(boat_dict))

    #assigns or removes a boat at a slip
    def patch(self, slip_id=None):
        print "using the right handler"
        if slip_id:
            slip = ndb.Key(urlsafe=slip_id).get()
            #slip_dict = slip.to_dict()

            #if there is a body add the boat to the slip
            if self.request.body:
                request_body = json.loads(self.request.body)
                boat = ndb.Key(urlsafe=request_body['boat']).get()

                #check for a boat in the slip
                if slip.current_boat:
                    print "slip is occupied"
                    self.abort(403, "Slip is occupied.")


                #check that requested boat at_sea == True
                if boat.at_sea == False:
                    self.abort(403, "Boat is already docked at a slip.")

                #print type(request_body)
                #print request_body['boat']
                #print request_body['date']

                #add boat to slip
                #slip_dict['current_boat'] = request_body['boat']
                #slip_dict['arrival_date'] = request_body['date']
                slip.current_boat = request_body['boat']
                slip.arrival_date = request_body['date']
                slip.put()
                #print slip_dict

                #update boat at_sea = False
                #boat_dict = boat.to_dict()
                #boat_dict['at_sea'] = False
                boat.at_sea = False
                boat.put()
                #print boat_dict
                self.response.write(self.request.body)
            #no body sent, remove boat at slip
            else:
                if slip.current_boat:
                    print "slip is occupied"
                    boat = ndb.Key(urlsafe=slip.current_boat).get()
                    boat.at_sea = True
                    slip.current_boat = None
                    slip.arrival_date = None
                    slip.put()
                    boat.put()
                else:
                    #no boat in slip
                    self.abort(400, "Slip is empty")

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        self.response.write("Hello world!")
# [END main_page]

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/boat', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/slip/boat/details/(.*)', BoatAtSlipHandler),
    ('/slip/boat/(.*)', BoatAtSlipHandler),
    ('/slip', SlipHandler),
    ('/slip/(.*)', SlipHandler),
    #webapp2.Route('/slip/(.*)/boat', handler='handlers.SlipHandler', name='slip-boat', handler_method='boatAtSlip'),
    #('/slip/(.*)/boats', SlipHandler),
], debug=True)
# [END app]
