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
import webapp2, os, jinja2, re, hashing, json, logging, time
from signup import *
from login import Login
from google.appengine.ext import db
from google.appengine.api import memcache

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

q_time = {"top": [], "article": [], "": [0]}
def query_time(on_query = False, key = ""):
	global q_time
	if on_query and key != "":
		q_time[key].append(time.time())
	elif not on_query and q_time[key]:
		logging.error("*******QTIME*******")
		logging.error(q_time[key])
		return q_time[key][-1]

def get_top_articles(update = False):
	key = "top"
	entries = memcache.get(key)
	if entries == None or update:
		logging.error("DB QUERY")
		query_time(True, key)
		entries = db.GqlQuery("SELECT * FROM Entry ORDER BY created DESC LIMIT 10")
		memcache.set(key, entries)
	return entries

class MainPage(Handler):
    def get(self):
    	entries = get_top_articles()
    	user_cookie = self.request.cookies.get('user')
    	last_query = query_time(False, "top")
    	if last_query:
    		last_query = int(time.time() - last_query)
    	else:
    		last_query = 0
        self.render("index.html", entries = entries, query_time = last_query)


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
			get_top_articles(update=True)
			last_entry = entry.get_by_id(entry.key().id())
			self.redirect('/blog/' + str(entry.key().id()))
		else:
			self.render("newpost.html", title=title, content=content, newpost_error=newpost_error)

def get_article(article_id):
	key = str(article_id)
	entity = memcache.get(key)
	if entity == None:
		logging.error("*****ART DB QUERY******")
		query_time(True, "article")
		entity = Entry.get_by_id(article_id)
		memcache.set(key, entity)	
	return entity

class ArticleHandler(Handler):
	def get(self, *args):
		article_id = self.request.url
		blog_pos = article_id.find('/blog/')
		article_id = int(article_id[blog_pos + 6:])
		entity = get_article(article_id)
		last_query = query_time(False, "article")
		if last_query:
			last_query = int(time.time() - last_query)
		else:
			last_query = 0

		self.render("article.html", article_id = article_id, entity = entity, query_time = last_query)

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

class JsonHandler(Handler):
	def gen_article_json(self, content=None, created=None, subject=None):
		json_s = json.dumps({
							"content": content,
							"created": created,
							"subject": subject
							})
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json_s)

	def gen_main_json(self, entries):
		json_list = []
		for entry in entries:
			json_list.append({
							"content": entry.content,
							"created": str(entry.created),
							"subject": entry.title
							})
		json_s = json.dumps(json_list)
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json_s)

class JsonArticleHandler(JsonHandler):
	def get(self, *args):
		article_id = re.findall(r'\d+', str(args))
		entity = Entry.get_by_id(int(article_id[0]))
		json_dict = {"content": entity.content, "created": str(entity.created), "subject": entity.title}
		self.gen_article_json(**json_dict)

class JsonMainPageHandler(JsonHandler):
	def get(self):
		entries = db.GqlQuery("SELECT * FROM Entry")
		self.gen_main_json(entries)

class FlushHandler(Handler):
	def get(self):
		memcache.flush_all()
		self.redirect('/blog')


		
app = webapp2.WSGIApplication([
     ('/blog/?', MainPage),
     ('/blog/newpost/?', NewpostHandler),
     ((r'/blog/(\d+)'), ArticleHandler),
     ('/blog/signup/?', SignupHandler),
     ('/blog/welcome/?', WelcomeHandler),
     ('/blog/login/?', LoginHandler),
     ('/blog/logout/?', LogoutHandler),
     ((r'/blog/(\d+).json'), JsonArticleHandler),
     ('/blog.json', JsonMainPageHandler),
     ('/blog/flush/?', FlushHandler)
], debug=True)
