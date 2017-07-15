from google.appengine.ext import ndb
import webapp2
import json
import random
import string
import logging

def getRandomId():
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(6)])

def checkForExistingSlipNumber(number):
    query_all_slips = [get_slip_query.to_dict() for get_slip_query in Slip.query()]
    existingNumber = False
    for dic in query_all_slips:
        if dic['number'] == number:
            existingNumber = True
    return existingNumber

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
    #creates a boat
    def post(self):

        #assign default values
        user_provided_name = None
        user_provided_craft_type = None
        user_provided_length = None

        if self.request.body:
            boat_request = json.loads(self.request.body)

            #check for included fields in the request body
            if 'name' in boat_request:
                user_provided_name = boat_request['name']
            if 'craft_type' in boat_request:
                user_provided_craft_type = boat_request['craft_type']
            if 'length' in boat_request:
                user_provided_length = boat_request['length']

        #create the new boat
        new_boat = Boat(id_num=getRandomId(), name=user_provided_name, craft_type=user_provided_craft_type, length=user_provided_length)
        newKey = new_boat.put()
        boat_dict = new_boat.to_dict()
        boat_dict['self'] = new_boat.key.urlsafe()
        self.response.write(json.dumps(boat_dict))

    #if an id is provided, return that boat. Else, return all boats.
    def get(self, id=None):
        if id:
            b = ndb.Key(urlsafe=id).get()
            b_dict = b.to_dict()
            b_dict['self'] = id
            self.response.write(json.dumps(b_dict))
        else:
            boat_query = [get_boat_query.to_dict() for get_boat_query in Boat.query()]
            self.response.write(json.dumps(boat_query))
    #modify a boat
    def patch(self, id=None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            request_body = json.loads(self.request.body)
            if 'name' in request_body:
                boat.name = request_body['name']
            if 'type' in request_body:
                boat.craft_type = request_body['type']
            if 'length' in request_body:
                try:
                    boat.length = request_body['length']
                except TypeError:
                    self.abort(403, "Length is not an integer")
            boat.put()
            boat_dict = boat.to_dict()
            self.response.write(json.dumps(boat_dict))
        else:
            self.abort(400)
    #delete a boat
    def delete(self, id=None):
        boat = ndb.Key(urlsafe=id).get()
        #if the boat is in a slip, find the slip and update the info
        if boat.at_sea == False:
            slip_query = Slip.query()
            for slip in slip_query.fetch():
                if slip.current_boat == id:
                    slip.current_boat = None
                    slip.arrival_date = None
                    slip.put()
        ndb.Key(urlsafe=id).delete()

class Slip(ndb.Model):
    id_num = ndb.StringProperty(required=True)
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date =ndb.StringProperty()

class SlipHandler(webapp2.RequestHandler):
    #create a slip
    def post(self):
        if self.request.body:
            slip_request = json.loads(self.request.body)
            #check that the body contains a number attribute
            if 'number' in slip_request:

                if checkForExistingSlipNumber(slip_request['number']) == True:
                    self.abort(403, "Slip number already in use.")

                new_slip = Slip(id_num=getRandomId(), number=slip_request['number'])
                new_slip.put();
                slip_dict = new_slip.to_dict()
                slip_dict['self'] = new_slip.key.urlsafe()
                self.response.write(json.dumps(slip_dict))
            else:
                self.abort(400)
        else:
            self.abort(400, "Expected request body.")

    #get a single slip or all slips
    def get(self, id=None):
        if id:
            s = ndb.Key(urlsafe=id).get()
            s_dict = s.to_dict()
            s_dict['self'] = id
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
                        self.abort(403, "Number is already in use.")
                    else:
                        try:
                            slip.number = request_body['number']
                            slip.put()
                            slip_dict = slip.to_dict()
                            self.response.write(json.dumps(slip_dict))
                        except:
                            self.abort(400, "Number is not an integer.")
                else:
                    self.abort(400)
            #no number provided. Generate new number
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
                slip_dict = slip.to_dict()
                self.response.write(json.dumps(slip_dict))
        else:
            self.abort(400)
    #replace a boat in a slip with another boat
    def put(self, slip_id=None):
        if slip_id:
            slip = ndb.Key(urlsafe=slip_id).get()
            if self.request.body:
                request_body = json.loads(self.request.body)

                #current slip must be occupied for this request
                if slip.current_boat == None:
                    self.abort(403)
                else:
                    #change the current boat in slip to at_sea = True
                    boat = ndb.Key(urlsafe=slip.current_boat).get()
                    boat.at_sea = True
                    boat.put()

                #make sure new boat is at sea
                replacement_boat = ndb.Key(urlsafe=request_body['boat']).get()
                if replacement_boat.at_sea == False:
                    self.abort(403)
                else:
                    replacement_boat.at_sea = False
                    replacement_boat.put()

                #assign new boat to slip
                slip.current_boat = request_body['boat']
                slip.arrival_date = request_body['date']
                slip.put()

                slip_dict = slip.to_dict()
                boat_dict = replacement_boat.to_dict()
                self.response.write(json.dumps([slip_dict, boat_dict]))
            else:
                self.abort(400, "Expected request body.")
        else:
            self.abort(400)
    #delete a slip
    def delete(self, slip_id=None):
        if slip_id:
            slip = ndb.Key(urlsafe=slip_id).get()

            #if there is a boat in the slip handle it first
            if slip.current_boat != None:
                #get the boat and set it to "at sea"
                boat = ndb.Key(urlsafe=slip.current_boat).get()
                boat.at_sea = True
                boat.put()

        #delete the slip
        ndb.Key(urlsafe=slip_id).delete()

class BoatAtSlipHandler(webapp2.RequestHandler):
    #gets a boat at a slip
    def get(self, slip_id=None):
        if slip_id:
            slip = ndb.Key(urlsafe=slip_id).get()
            slip_boat = slip.current_boat
            #if slip is empty, just send the slip details
            if slip_boat == None:
                slip_dict = slip.to_dict()
                self.response.write(json.dumps(slip_dict))
            else:
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
                    self.abort(403, "Slip is occupied.")


                #check that requested boat at_sea == True
                if boat.at_sea == False:
                    self.abort(403, "Boat is already docked at a slip.")

                slip.current_boat = request_body['boat']
                slip.arrival_date = request_body['date']
                slip.put()
                slip_dict = slip.to_dict()

                #update boat at_sea = False
                boat.at_sea = False
                boat.put()
                boat_dict = boat.to_dict()
                self.response.write(json.dumps([slip_dict, boat_dict]))
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

                    #prepare and send a response
                    slip_dict = slip.to_dict()
                    boat_dict = boat.to_dict()
                    self.response.write(json.dumps([slip_dict, boat_dict]))
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
    ('/boat/(.*)', BoatHandler),
    ('/slip/boat/details/(.*)', BoatAtSlipHandler),
    ('/slip/boat/(.*)', BoatAtSlipHandler),
    ('/slip', SlipHandler),
    ('/slip/(.*)', SlipHandler),
    ('/slip/(.*)', SlipHandler),
], debug=True)
# [END app]
