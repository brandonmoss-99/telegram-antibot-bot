import requests, json, random, sys, getopt, time, os, copy, datetime
from urllib import parse
from tMsgSender import tMsgSender
from tMsgFetcher import tMsgFetcher
from uData import uData
from configHandler import configHandler
from tCommandHandler import tCommandHandler
from tMsgHandler import tMsgHandler
from tBotCommandInfo import tBotCommandInfo
from tCallbackQueryHandler import tCallbackQueryHandler
from newUserProcessor import newUserProcessor

def getHelp():
	print("\nList of options:\n\n" +
		"-(t)oken of bot to control\n" +
		"--help to show this help message\n\n")
	sys.exit(0)


def handleWrongChat():
	print("timestamp:", int(time.time()), "New msg from a non-whitelisted", msg['message']['chat']['type'], "ID: ", msg['message']['chat']['id'])
	tMsgSender.sendRequest(["sendMessage", "chat_id", msg['message']['chat']['id'], "text", "Hi there%21%0A%0AI appreciate the add to your group, however right now I only work on specific groups%21"])
	tMsgSender.sendRequest(["leaveChat", "chat_id", msg['message']['chat']['id']])


def readIntFileToList(path):
	if os.path.isfile(path):
		try:
			with open(path, "r") as f:
				# read each line in file, stripping any trailing chars ('/n') and casting to int
				lines = [int(line.rstrip()) for line in f]
			return [True, lines]
		except Exception as e:
			print("Error whilst handling", path, ":", str(e))
			return [False, []]
	else:
		return [False, []]


if __name__ == '__main__':
	# initial token value
	token = ""
	argv = sys.argv[1:]

	# try getting supported parameters and args from command line
	try:
		opts, args = getopt.getopt(argv, "t:",
			["token=", "help"])
	except:
		print("Error parsing options")
		getHelp()

	for opt, arg in opts:
		if opt in ['-t', '--token']:
			try:
				# connect to Telegram API with their getMe test method for checking API works
				testResponse = requests.get("https://api.telegram.org/bot%s/getMe" % (str(arg)))
				# set the token to be used if we get a 2xx response code back
				if testResponse.ok:
					token = str(arg)
				else:
					print("Error validating your token!")
					getHelp()
			except:
				print("Error trying to validate your token!")
				getHelp()
		if opt in ['--help']:
			getHelp()
	print("--------------------------------------\nProgram started at UNIX time:", int(time.time()), "\n")

	# create tMsgSender first, needed for other actions
	tMsgSender = tMsgSender(token)

	# get info about bot from Telegram
	botInfo = json.loads(tMsgSender.sendRequest(["getMe"])[2])['result']
	bot_id = botInfo['id']
	bot_username = botInfo['username']

	# create other needed objects
	tMsgFetcher = tMsgFetcher(token, pollTimeout)
	uData = uData()
	configHandler = configHandler('../config.txt')
	tBotCommandInfo = tBotCommandInfo()
	tMsgHandler = tMsgHandler(token, bot_id, bot_username, configHandler, uData, tMsgSender, tBotCommandInfo)
	tCallbackQueryHandler = tCallbackQueryHandler(token)
	newUserProcessor = newUserProcessor(configHandler, uData, tMsgSender)

	# load configurations
	print(configHandler.loadConfig()[1])
	botConfLoad = configHandler.loadBotConfig()
	defaultConfLoad = configHandler.loadDefaultGroupConfig()
	customConfLoad = configHandler.loadGroupConfigs()
	# if the bot, default group or custom group configs can't be found
	# stop program, needs to be fixed
	if not botConfLoad[0] or not defaultConfLoad[0] or not customConfLoad[0]:
		print("Bot config: ", botConfLoad[1], "Default config: ", defaultConfLoad[1], "Custom group config: ", customConfLoad[1])
		sys.exit(0)


	# turn botCommands into the type of list telegram requires for setMyCommands method
	botCommandsAsList = tBotCommandInfo.getCommandItemsAsList()
	botCommandsForTelegram = '[{"command":"' + botCommandsAsList[0][1]['name'] + '", "description":"' + botCommandsAsList[0][1]['description'] + '"}'
	for command in botCommandsAsList:
		botCommandsForTelegram = botCommandsForTelegram + ', {"command":"' + command[1]['name'] + '", "description":"' + command[1]['description'] + '"}'
	botCommandsForTelegram = botCommandsForTelegram + ']'
	commandRequest = tMsgSender.sendRequest(["setMyCommands", "commands", botCommandsForTelegram])

	# Chat IDs to work with. Don't want just anyone adding the bot and sucking up the host's resources!
	whiteListRead = readIntFileToList(whiteListFile)
	if whiteListRead[0] == True:
		usingWhitelistRestrictions = True
		whitelistedChatIDs = whiteListRead[1]
		print("Using whitelist restrictions")
	else:
		usingWhitelistRestrictions = False
		print("Whitelist file not found/processing failed, disabling whitelist restrictions")

	# loop, run until program is quit
	while True:
		# fetch all the new messages from Telegram servers
		if tMsgFetcher.fetchMessages() == True:
			# for each message in the list of new messages
			for i in range(tMsgFetcher.getMessagesLength()):
				# get the message
				msg = tMsgFetcher.getMessage(i)
				# check the message type and hand message off to handler
				if 'message' in msg and msg['message']['chat']['type'] in ['group', 'supergroup']:
					# if we're using a whitelist to restrict chats we deal with
					if usingWhitelistRestrictions == True:
						# if a message comes from a whitelisted chat, deal with it, otherwise
						# send a message and remove the bot from the chat the message came from
						if msg['message']['chat']['id'] in whitelistedChatIDs:
							tMsgHandler.handleMessage(msg)
						else:
							handleWrongChat()
					# if we're not using a whitelist to restrict chats, 
					# handle message without checking chat origin
					else:
						tMsgHandler.handleMessage(msg)

				# callback query is from tapping a button sent with message
				elif 'callback_query' in msg:
					tCallbackQueryHandler.handleCallbackQuery(msg)

				# update the message offset, so it is 'forgotten' by telegram servers
				# and not returned again on next fetch for new messages, as we've
				# (hopefully) dealt with the message now
				msgOffset = msg['update_id'] + 1

			newUserProcessor.processNewUserList()
		else:
			# failed to fetch new messages, wait for random number of seconds then try again
			# (may reduce strain on telegram servers when requests are randomly distributed if
			# they go down, instead of happening at fixed rate along with many other bots etc)
			time.sleep(random.randint(20, 60))

