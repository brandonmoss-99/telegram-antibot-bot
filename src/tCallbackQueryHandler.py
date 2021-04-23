from tNewCallbackQuery import tNewCallbackQuery
from configHandler import configHandler
from tMsgSender import tMsgSender
from uData import uData

class callback_queryHandler:
	def __init__(self, token, configHandler, uData, tMsgSender):
		self.token = token
		self.configHandler = configHandler
		self.uData = uData
		self.tMsgSender = tMsgSender

	def handleCallbackQuery(self, message):
		tNewCallbackQuery = tNewCallbackQuery(message['callback_query'], self.configHandler, self.uData, self.tMsgSender)