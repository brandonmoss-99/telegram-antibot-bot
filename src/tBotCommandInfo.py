class tBotCommandInfo:

	def __init__(self):
		self.botCommandsInfo = {
			"enable":{
				"name":"enable",
				"description":"Enable the bot, respond to new events",
				"paramType":"none"
			},
			"disable":{
				"name":"disable",
				"description":"Disable the bot, ignore new events",
				"paramType":"none"
			},
			"setunvalttk":{
				"name":"setunvalttk",
				"description":"Set how many seconds user has to press button before being kicked",
				"paramType":"posint"
			},
			"setvalttk":{
				"name":"setvalttk",
				"description":"Set how many seconds user has to send something after being validated",
				"paramType":"posint"
			},
			"setrestricttime":{
				"name":"setrestricttime",
				"description":"Set how many seconds a user is restricted for after being validated",
				"paramType":"posint"
			},
			"setdeletetime":{
				"name":"setdeletetime",
				"description":"Set how many seconds until bot messages are automatically deleted (after task is done)",
				"paramType":"posint"
			},
			"setfrstmsgrtime":{
				"name":"setfrstmsgrtime",
				"description":"Set how many seconds to monitor a new users messages for something prohibited after sending their 1st message",
				"paramType":"posint"
			},
			"lockdown":{
				"name":"lockdown",
				"description":"CAUTION: Will auto-ban every new user join until disabled",
				"paramType":"none"
			},
			"disablelockdown":{
				"name":"disablelockdown",
				"description":"Disable lockdown mode",
				"paramType":"none"
			}
		}

	def inCommandList(self, command):
		"""
		Check if given command is in the list of commands, return True/False
		"""
		return True if command in list(self.botCommandsInfo) else False

	def getCommandItemsAsList(self):
		"""
		Return command info items as a list
		"""
		return list(self.botCommandsInfo.items())

	def getCommandData(self, command, data):
		return self.botCommandsInfo[command][data]