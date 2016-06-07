import webapp2
import hashing
from google.appengine.ext import db

class Login():
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.user_id = {}

	def get_user(self):
		if self.username or self.password:
			name = db.GqlQuery("SELECT * FROM Users WHERE username = :username" , username=self.username)
			u = name.get()
			try:
				if u.username != self.username and u.password != self.password:
					return False
				elif u.username == self.username:
					if hashing.validpw(self.password, str(u.salt), str(u.password)):
						self.user_id["user_id"] = (u.key().id())
						self.user_id["hash_password"] = u.password
						self.user_id["salt"] = u.salt
						return True
					else:
						return	False
			except AttributeError:
				return False

	def set_cookies(self):
		hash_cookie = "%s|%s" % (self.user_id["hash_password"], self.user_id["salt"])
		id_cookie = str(self.user_id["user_id"])
		cookies = (str(hash_cookie), str(id_cookie))
		return cookies
