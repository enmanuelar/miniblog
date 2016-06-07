import webapp2, re
import hashing
from google.appengine.ext import db

class Users(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	salt = db.StringProperty(required = True)
	email = db.EmailProperty()

class Signup():
	def __init__(self, username, password, verify, email=None):
		self.username = username
		self.password = password
		self.verify = verify
		self.email = email
		self.params = {"username": self.username, "email": self.email}
		self.error = False

	def put_user(self):
		if self.username and self.password:
			name = db.GqlQuery("SELECT * FROM Users WHERE username = :username" , username=self.username)
			for u in name: 
				if u.username == self.username:
					self.params["username_error"] = "Username already exists"
					self.error = True
					return
			hashed = hashing.hashpw(self.password, salt=None)
			if self.email:
				user = Users(username = self.username, password = hashed[0], salt = hashed[1], email = self.email)
			else:
				user = Users(username = self.username, password = hashed[0], salt = hashed[1])
			user.put()
			user_id = user.key().id()
			return user_id

	def set_cookies(self):
		cookie = str(hashing.hash_cookie(self.username))
		return cookie

	def valid_username(self):
		USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
		return self.username and USER_RE.match(self.username)

	def valid_password(self):
		PASS_RE = re.compile(r"^.{3,20}$")
		return self.password and PASS_RE.match(self.password)

	def valid_verify_password(self):
		VERIFYPASS_RE = re.compile(r"^.{3,20}$")
		return self.verify and VERIFYPASS_RE.match(self.verify)

	def valid_email(self):
		EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
		return not self.email or EMAIL_RE.match(self.email)
		
	def validate(self):
		if not self.valid_username():
			self.params["username_error"] = "Invalid username"
			self.error = True

		if not self.valid_password():
			self.params["password_error"] = "Invalid password"
			self.error = True
		elif self.password != self.verify:
			self.params["verify_error"] = "Password do not match"
			self.error = True

		if not self.valid_email():
			self.params["email_error"] = "Invalid email"
			self.error = True

		return	self.error

	def get_params(self):
		return self.params