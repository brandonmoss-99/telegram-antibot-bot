from configHandler import configHandler

class tCommandHandler:

	def __init__(self, configHandler):
		self.configHandler = configHandler

	def runCommand(self, command, param):
		self.command = command
		self.param = param
		# use the command passed in to choose the function to run
		# return False if a function for that command name isn't found
		commandToRun = getattr(self, self.command, False)
		if commandToRun != False:
			return commandToRun(self.param)
		else:
			return [False, "Couldn't find function", self.command]

	def runCommandGroupData(self, command, param, groupConfig):
		self.command = command
		self.param = param
		self.groupConfig = groupConfig
		# use the command passed in to choose the function to run
		# return False if a function for that command name isn't found
		commandToRun = getattr(self, self.command, False)
		if commandToRun != False:
			return commandToRun(self.param, self.groupConfig)
		else:
			return [False, "Couldn't find function", self.command]

	# set unvalidatedTimeToKick
	def setunvalttk(self, param, groupConfig):
		try:
			self.groupConfig['unValidatedTimeToKick'] = self.param
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set unvalidated time to kick to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set unvalidated time to kick to " + str(param) + " seconds", str(e)]

	# set validatedTimeToKick
	def setvalttk(self, param, groupConfig):
		try:
			self.groupConfig['validatedTimeToKick'] = self.param
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set validated time to kick to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set validated time to kick to " + str(param) + " seconds", str(e)]

	# set timeToRestrict
	def setrestricttime(self, param, groupConfig):
		try:
			self.groupConfig['timeToRestrict'] = self.param
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set button tap restriction time to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set button tap restriction time to " + str(param) + " seconds", str(e)]

	# set timeToDelete
	def setdeletetime(self, param, groupConfig):
		try:
			self.groupConfig['timeToDelete'] = self.param
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set time to delete my messages to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set time to delete my messages to " + str(param) + " seconds", str(e)]

	# set timeToRestrictForwards
	def setfrstmsgrtime(self, param, groupConfig):
		try:
			self.groupConfig['timeToRestrictForwards'] = self.param
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully set time to monitor new user's messages for anything prohibited after their first message to " + str(param) + " seconds"]
		except Exception as e:
			return [False, "Failed to set time to monitor new user's messages for anything prohibited after their first message to " + str(param) + " seconds", str(e)]

	def disable(self, param, groupConfig):
		try:
			self.groupConfig['active'] = False
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully disabled the bot from responding to new events"]
		except Exception as e:
			return [False, "Failed to disable the bot from responding to new events ", str(e)]

	def enable(self, param, groupConfig):
		try:
			self.groupConfig['active'] = True
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			return [True, "Successfully enabled the bot to respond to new events"]
		except Exception as e:
			return [False, "Failed to enable the bot to respond to new events ", str(e)]

	# Use with caution! A lockdown will auto-ban every new user joining until disabled!
	def lockdown(self, param, groupConfig):
		try:
			self.groupConfig['inLockdown'] = True
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			# if the bot is not responding to new events when a lockdown
			# command is sent, re-enable the bot to respond
			if self.groupConfig['active'] == False:
				enableCommand = self.enable(None, self.groupConfig)
				# if bot was successfully re-enabled, enter lockdown
				if enableCommand[0] == True:
					return [True, "\U0001F6A8 !!! LOCKDOWN ENABLED !!! \U0001F6A8 %0A%0ABot was automatically re-enabled to respond! %0A%0AAll new users will be insta-banned until disabled!"]
				else:
					return [False, "Lockdown failed! Couldn't automatically re-enable the bot! ", str(e)]
			else:
				return [True, "\U0001F6A8 !!! LOCKDOWN ENABLED !!! \U0001F6A8 %0A%0AAll new users will be insta-banned until disabled!"]
		except Exception as e:
			return [False, "Lockdown failed! Admin to manually disable global group permissions! ", str(e)]

	def disablelockdown(self, param, groupConfig):
		try:
			self.groupConfig['inLockdown'] = False
			self.configHandler.setCustomGroupConfig(self.groupConfig)
			return [True, "Lockdown successfully disabled"]
		except Exception as e:
			return [False, "Lockdown failed to disable! ", str(e)]
