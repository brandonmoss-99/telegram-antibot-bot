class uData:

	def __init__(self):
		self.newUsers = {}


	def getnewUserKeysList(self):
		"""
		Return a Python list of dictionary keys for the newUsers dictionary

		"""
		return list(self.newUsers.keys())

	def getnewUserKeys(self):
		"""
		Return a Python iterable of dictionary keys for the newUsers dictionary.
		More efficient for a for-loop iterating through all keys, at the cost
		of not being able to access elements in non-linear order (i.e, must go
		through all keys in the order they come, can't go to random key)

		"""
		return self.newUsers.keys()


	def getnewUserData(self, key):
		"""
		Return all values for a given key
		"""
		return self.newUsers[key]

	def userExists(self, key):
		"""
		Check if key exists in newUsers dictionary, and return True/False
		"""
		return True if key in self.newUsers else False

	def getData(self, key, value):
		return self.newUsers[key][value]

	def appendData(self, key, value, data):
		self.newUsers[key][value].append(data)

	def setData(self, key, value, data):
		self.newUsers[key][value] = data


	def addnewUser(self, key, data):
		self.newUsers[key] = data