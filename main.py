#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2, os, jinja2, re, hashing
from signup import *
from login import Login
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape = True)


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class Entry(db.Model):
	title = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	date = db.DateProperty(auto_now_add = True)

class MainPage(Handler):
    def get(self):
    	entries = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC LIMIT 10")
    	user_cookie = self.request.cookies.get('user')
        self.render("index.html", entries = entries)


class NewpostHandler(Handler):
	def get(self):
		self.render("newpost.html")
	
	def post(self):
		title = self.request.get("subject")
		content = self.request.get("content")
		newpost_error = "Enter title and content"
		if title and content:
			entry = Entry(title = title, content = content, id="")
			entry.put()
			last_entry = entry.get_by_id(entry.key().id())
			self.redirect('/blog/' + str(entry.key().id()))
		else:
			self.render("newpost.html", title=title, content=content, newpost_error=newpost_error)

class ArticleHandler(Handler):
	def get(self, *args):
		article_id = self.request.url
		blog_pos = article_id.find('/blog/')
		article_id = int(article_id[blog_pos + 6:])
		entries = db.GqlQuery("SELECT * FROM Entry")
		self.render("article.html", article_id = article_id, entries = entries)

class SignupHandler(Handler):
	def get(self):
		self.render("signup.html")
	
	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		verify = self.request.get("verify")
		email = self.request.get("email")
		signup_obj = Signup(username, password, verify, email)
		user_id = str(signup_obj.put_user())
		invalid = signup_obj.validate()

		if not invalid: 
			self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % (signup_obj.set_cookies()))
			self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % (user_id))
			self.redirect('/blog/welcome')
		elif invalid:
			self.render("signup.html", **signup_obj.get_params())

class WelcomeHandler(Handler):
	def get(self):
		user_cookie = self.request.cookies.get('name')
		try:
			user_id = int(self.request.cookies.get('user_id'))
			entity = Users.get_by_id(user_id)
			valid_hash = hashing.check_secure_val(user_cookie, entity.username)
			if valid_hash:
				self.render("welcome.html", user = entity.username)
			else:
				self.redirect('/blog/signup')
		except :
			self.redirect('/blog/signup')

class LoginHandler(Handler):
	def get(self):
		self.render("login.html")

	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		login_obj = Login(username, password)
		if login_obj.get_user():
			cookies = login_obj.set_cookies()
			self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % (cookies[0]))
			self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % (cookies[1]))
			self.redirect("/blog/welcome")
		else:
			self.render("login.html", username=username, login_error="invalid login")

class LogoutHandler(Handler):
	def get(self):
		name_cookie = self.request.cookies.get('name')
		user_id_cookie = self.request.cookies.get('user_id')
		self.response.delete_cookie('name')
		self.response.delete_cookie('user_id')		
		self.redirect("/blog")
		

app = webapp2.WSGIApplication([
     ('/blog', MainPage), ('/blog/newpost', NewpostHandler), ((r'/blog/(\d+)'), ArticleHandler), ('/blog/signup', SignupHandler),
     ('/blog/welcome', WelcomeHandler), ('/blog/login', LoginHandler), ('/blog/logout', LogoutHandler)
], debug=True)
