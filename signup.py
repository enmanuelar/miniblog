import webapp2, re

class Signup(webapp2.RequestHandler):
	def __init__(self, username, password, verify, email):
		self.username = username
		self.password = password
		self.verify = verify
		self.email = email

	def valid_username(self):
		USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
		return USER_RE.match(self.username)

	def valid_password(self):
		PASS_RE = re.compile(r"^.{3,20}$")
		return PASS_RE.match(self.password)

	def valid_verify_password(self):
		VERIFYPASS_RE = re.compile(r"^.{3,20}$")
		return VERIFYPASS_RE.match(self.verify)

	def valid_email(self):
		EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
		return EMAIL_RE.match(self.email)
	
	def validate(self):
		if self.valid_username() and self.valid_password() and self.valid_verify_password() and (self.password == self.verify):
			self.redirect('/blog')
		else:
			if self.valid_username() == False:
				username_error = "Invalid username"
			else:
				if self.valid_password() == False or self.valid_verify_password() == False:
					password_error = "Invalid password"
				else:
					if self.password != self.verify:
						verify_error = "Password do not match"
					else:
						if self.valid_email == False:
							email_error = "Invalid email"
		
	def post(self):
		username = self.request.get("username")
		password = self.request.get("password")
		verify_password = self.request.get("verify")
		email = self.request.get("email")
		if self.valid_username(username) and self.valid_password(password) and self.valid_verify_password(verify_password) and (self.password == verify_password):
			self.redirect('/welcome?username=' + username)
		else:
			if self.valid_username(username) == False:
				username_error = "Invalid username"
				username_bool = False
			else:
				if self.valid_password == False or self.valid_verify_password == False:
					password_error = "Invalid password"
				else:
					if password != verify_password:
						verify_error = "Password do not match"
					else:
						if email == False:
							email_error = "Invalid email"