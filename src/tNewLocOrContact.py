import time
from configHandler import configHandler
from uData import uData

class tNewLocOrContact:
	def __init__(self, message, configHandler, uData):
		self.message = message
		self.configHandler = configHandler
		self.uData = uData
		self.getInfo()

		# if user has sent forwarded message, check if they're still in newUsers
		# if not sent a message yet, or their first message was sent less than
		# x mins ago, delete their message and mark for kicking
		userKey = self.isfrom['id'] + self.chat['id']
		if self.uData.userExists(userKey):
			if ((self.uData.getData(userKey, 'timeSentFirstMessage') == None) or 
				(int(time.time()) - self.uData.getData(userKey, 'timeSentFirstMessage') <= self.configHandler.getCustomGroupConfig(self.chat['id'])['timeToRestrictForwards']) or
				(int(time.time()) - self.uData.getData(userKey, 'timeSetTextRestrictions') <= self.configHandler.getCustomGroupConfig(self.chat['id'])['validatedTimeToKick'])):
					# add message to newUsers list of messages
					self.uData.appendData(userKey, 'sentMessages', self.message_id)
					self.uData.setData(userKey, 'hasSentBadMessage', True)

	def getInfo(self):
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']
		self.isfrom = self.message['from'] # optional, but only as not sent when msg sent to channel