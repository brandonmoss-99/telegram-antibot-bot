import time, json
from configHandler import configHandler
from tMsgSender import tMsgSender
from uData import uData

class tNewCallbackQuery:
	def __init__(self, message, configHandler, uData, tMsgSender):
		self.callbackQuery = message
		self.configHandler = configHandler
		self.uData = uData
		self.tMsgSender = tMsgSender
		self.getInfo()
		self.processQuery()

	def getInfo(self):
		self.query_id = self.callbackQuery['id']
		self.query_from = self.callbackQuery['from']
		self.query_chat_instance = self.callbackQuery['chat_instance']
		self.query_message = self.callbackQuery['message']

		if 'data' in self.callbackQuery:
			self.query_data = self.callbackQuery['data']

	def processQuery(self):
		# if the person who joined is the one to push the button, 
		# and not somebody else who can also see it
		if str(self.query_from['id']) + str(self.query_message['chat']['id']) + 'Success' == self.query_data:
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			self.tMsgSender.sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerSuccess'])
			try:
				userKey = self.query_from['id'] + self.query_message['chat']['id']
				# update newUsers to mark user as having passed validation, and
				# fill in the time of validation for permission managment/validatedTimeToKick
				self.uData.setData(userKey, 'passedValidation', True)
				self.uData.setData(userKey, 'timePassedValidation', int(time.time()))

				# send new message. If that succeeds, add it to current messages 
				# shown in chat, then try and delete the last message sent
				if self.uData.getData(userKey, 'username') != None:
					validatedMessage = "Yay, @" + self.uData.getData(userKey, 'username') + "%20 has passed validation%21%0A%0ATo ensure you aren%27t just a clever bot that can press buttons, you%27ll be restricted for around another%20" + str(self.configHandler.getCustomGroupConfig(self.query_message['chat']['id'])['timeToRestrict']) + "%20seconds!"
					newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", self.query_message['chat']['id'], "text", validatedMessage, "entities", "[{'type':'mention', 'offset':5, 'length':" + str(len(self.uData.getData(userKey, 'username'))) + "}]"])
				else:
					validatedMessage = "Yay, " + self.query_from['firstName'] + "%20 has passed validation%21%0A%0ATo ensure you aren%27t just a clever bot that can press buttons, you%27ll be restricted for around another%20" + str(self.configHandler.getCustomGroupConfig(self.query_message['chat']['id'])['timeToRestrict']) + "%20seconds!"
					newTextMessageRequest = self.tMsgSender.sendRequest(["sendMessage", "chat_id", self.query_message['chat']['id'], "text", validatedMessage])

				if newTextMessageRequest[0] == True:
					self.uData.appendData(userKey, 'welcomeMsgid', json.loads(newTextMessageRequest[2])['result']['message_id'])
					deleteRequest = self.tMsgSender.sendRequest(["deleteMessage", "chat_id", self.query_message['chat']['id'], "message_id", self.uData.popData(userKey, 'welcomeMsgid', len(self.uData.getData(userKey, 'welcomeMsgid'))-2)])
					if deleteRequest[0] == False:
						print("timestamp:", int(time.time()), "Failed to delete message:", deleteRequest[2])


			except Exception as e:
				print("timestamp:", int(time.time()), "Couldn't edit user", self.query_from['id'], "dictionary entry: ", str(e))
		# if the IDs don't match up
		else:
			# have to respond with an answerCallbackQuery, otherwise the button stays on loading wheel
			self.tMsgSender.sendRequest(["answerCallbackQuery", "callback_query_id", str(self.query_id) + 'answerFail'])