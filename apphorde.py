#!/usr/bin/env python
import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.web
from tornado.options import define, options
import tornado.options
import os.path
from pymongo import Connection
from pymongo.objectid import ObjectId
import re
import random
import string

define("port", default=8888, type=int, help="port to listen on")

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/", HomeHandler),
			(r"/thanks", BetaHandler)
		]
		settings = {
			"static_path": os.path.join(os.path.dirname(__file__), "static"),
			"template_path": os.path.join(os.path.dirname(__file__), "templates"),
			"debug": True,
		}
		tornado.web.Application.__init__(self, handlers, **settings)
		
		self.db = Connection().apphorde
		
class BaseHandler(tornado.web.RequestHandler):
	@property
	def db(self):
		return self.application.db

class HomeHandler(BaseHandler):
	def get(self):
		self.render("index.html", ref=self.get_argument("ref", None), error=self.get_argument("error", None))
		
class BetaHandler(BaseHandler):
	def post(self):
		email = self.get_argument("email", None)
		ref = self.get_argument("ref", None)
		if email and re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$", email):
			if self.db.beta_emails.find({'email': email}).count() == 0:
				if ref:
					self.db.beta_emails.update({'ref': ref}, {'$inc': {'count': 1}})
					ref = None
				while not ref or self.db.beta_emails.find({'ref': ref}, {'ref': 1}).count() != 0:
					ref = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
				email_id = self.db.beta_emails.insert({'email': email, 'ref': ref, 'count': 0})
			else:
				ref = self.db.beta_emails.find_one({'email': email}, {'ref': 1})['ref']
			self.render("thanks.html", ref=ref)
		else:
			if ref:
				self.redirect('/?ref=' + ref + '&error=1')
			else:
				self.redirect("/?error=1")
			
if __name__ == "__main__":
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()