import os, json

class configHandler:
	def __init__(self, configFilePath):
		self.configFilePath = configFilePath
		self.configDefaultGroupData = None
		self.configGroupsData = None
		self.configData = None
		self.configBotData = {}

	def loadConfig(self):
		with open(self.configFilePath, 'r') as configFile:
			try:
				self.configData = json.load(configFile)
				return [True, "Config loaded successfully"]
			except Exception as e:
				return [False, "Error parsing the config file: " + str(e)]

	def loadBotConfig(self):
		varsToLoad = ["msgOffset", "pollTimeout", "whiteListFile"]
		if 'config' in self.configData:
			try:
				for var in varsToLoad:
					self.configBotData[var] = self.configData['config']['bot'][var]
				return [True, "Bot config loaded successfully"]
			except Exception as e:
				return [False, "Error loading bot variables from config file: " + str(e)]
		else:
			return [False, "Error, config section doesn't exist in the file!"]

	def loadDefaultGroupConfig(self):
		if 'config' in self.configData and 'groups' in self.configData['config']:
			try:
				self.configDefaultGroupData = self.configData['config']['groups']['default']
				return [True, "Default group config loaded successfully"]
			except Exception as e:
				return [False, "Error loading default group config from file: " + str(e)]
		else:
			return [False, "Error, config/group/default section doesn't exist in the file!"]

	def loadGroupConfigs(self):
		if 'config' in self.configData and 'groups' in self.configData['config']:
			try:
				self.configGroupsData = self.configData['config']['groups']['custom']
				return [True, "Default group config loaded successfully"]
			except Exception as e:
				return [False, "Error loading custom group configs from file: " + str(e)]
		else:
			return [False, "Error, config/group/custom section doesn't exist in the file!"]

	def getCustomGroupConfig(self, groupId):
		# if the groupId requested exists in config data
		# return that group data, otherwise return the
		# default group config data
		if str(groupId) in self.configGroupsData:
			return self.configGroupsData[str(groupId)]
		else:
			return self.configDefaultGroupData

	def setCustomGroupConfig(self, groupConfigToChange):
		# if the group to change config already exists,
		# replace it with new groupConfig
		#if groupConfigToChange['id'] in self.configGroupsData:
		self.configGroupsData[groupConfigToChange['id']] = groupConfigToChange
		self.writeConfig()

	def writeConfig(self):
		with open('config.txt', 'w') as configFile:
			try:
				json.dump(self.configData, configFile, indent=4)
			except Exception as e:
				print("Failed to write file!")
