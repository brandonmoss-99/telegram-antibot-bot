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


	def getAllUserData(self, key):
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
		"""
		Return specified data for a given key
		"""
		return self.newUsers[key][value]

	def appendData(self, key, value, data):
		"""
		Append data to a specified value at a specified Dictionary key
		"""
		self.newUsers[key][value].append(data)

	def popData(self, key, value, itemIndex):
		"""
		Return data popped from index of a specified value at a specified Dictionary key
		"""
		return self.newUsers[key][value].pop(itemIndex)

	def setData(self, key, value, data):
		"""
		Set data on a specified value at a specified Dictionary key
		"""
		self.newUsers[key][value] = data


	def addNewUser(self, key, data):
		"""
		Add new user data to newUsers Dictionary
		"""
		self.newUsers[key] = data

	def deleteNewUser(self, key):
		del self.newUsers[key]