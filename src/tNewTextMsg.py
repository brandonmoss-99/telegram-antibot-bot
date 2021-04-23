import time
from configHandler import configHandler
from uData import uData

class tNewTextMsg:
	def __init__(self, message, configHandler, uData):
		self.message = message
		self.configHandler = configHandler
		self.uData = uData
		self.getInfo()
		self.userKey = self.isfrom['id'] + self.chat['id']
		# if the message sent is from a new user in the newUsers dictionary,
		# set their hasSentGoodMessage property to True, to mark them to be
		# deleted from the dictionary
		if self.uData.userExists(self.userKey):
			# add message to newUsers list of messages
			self.uData.appendData(self.userKey, 'sentMessages', self.message_id)
			# if user has sent an entity in their 1st text message, delete their message and mark for kicking
			if ('entities' in self.message) and (self.message['entities'][0]['type'] in self.configHandler.getCustomGroupConfig(self.chat['id'])['bannedEntities']):
				self.uData.setData(self.userKey, 'hasSentBadMessage', True)
			else:
				self.uData.setData(self.userKey, 'hasSentGoodMessage', True)
				# if the user hasn't already sent a message, set their first message time to current unix time
				if self.uData.getData(self.userKey, 'timeSentFirstMessage') == None:
					self.uData.setData(self.userKey, 'timeSentFirstMessage', int(time.time()))

	def getInfo(self):
		# extract always included message data
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		# include optional message data
		self.isfrom = self.message['from']