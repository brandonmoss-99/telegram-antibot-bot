import time
from configHandler import configHandler
from uData import uData
from tMsgSender import tMsgSender

class tNewLeftMember:
	def __init__(self, message, configHandler, uData, tMsgSender):
		self.message = message
		self.configHandler = configHandler
		self.uData = uData
		self.tMsgSender = tMsgSender
		self.getInfo()

		# if lockdown is enabled, try deleting the
		# left message to keep the chat clean
		if self.configHandler.getCustomGroupConfig(self.chat['id'])['inLockdown'] == True:
			deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", self.chat['id'], "message_id", self.message_id])
			if deleteRequest[0] == False:
				print("timestamp:", int(time.time()), "Couldn't delete message", self.message_id, "from chat", self.chat['id'],":", deleteRequest[2])

	def getInfo(self):
		# extract always included message data
		self.message_id = self.message['message_id']
		self.date = self.message['date']
		self.chat = self.message['chat']