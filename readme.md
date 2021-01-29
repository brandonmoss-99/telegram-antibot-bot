# telegram-antibot-bot

A telegram bot script written in Python for handling new users joining Telegram groups. This bot aims to reduce the number of 'spam/scam' bots joining with multiple simple layers to make it easier for a genuine user to get into the group, instead of 1 complex CAPTCHA style layer, which some bots can already bypass with human/AI CAPTCHA solving services

### Layers
The layers are as follows when a user joins a group with the bot in, with admin privilages:

1. All user permissions are restricted. An "I'm not a robot!" button is shown in chat to press in a given length of time
	* If the user fails to press the button in the given time, they are kicked
2. The user must then wait a length of time with no permissions (to prevent smart bots pressing the button and immediately sending spam/scam)
3. The user is given permission to send text messages. The user is then prompted to send a plaintext message in a given length of time
	* If the user fails to send a plaintext message in the given time, they are kicked
	* If the user sends a message with what telegram detects as a URL, Email, Phone Number or Bot Command, the message is deleted and they are banned (if telegram doesn't detect it, there's less chance of a 1-click interaction/preview, so less risk there)
	* If the user sends a forwarded text message or location or contact, it is deleted and they are banned
4. The user has the default permissions given back to them (send messages/media messages/polls/other messages, can add polls and can invite other users)
5. All messages sent from user for given length of time are monitored
	* If the user sends a message containing a URL, Email, Phone Number or Bot Command, sends a forwarded message of any type (photo/video etc) or a location or contact within the given length of time following their first plaintext message, all their messages since joining are deleted, and they are banned

### Configuration & Commands
A config file (config.txt) should exist in order for the bot to function. An example config, exampleConfig.txt is included, which can be modified and renamed. This config file is loaded up when the bot starts, and contains/can contain per-group properties can be changed and added via bot commands.

The following data is stored in the config file:
- Bot config data:
    - Initial message offset for telegram message fetching via long polling
    - Time delay to wait for a long polling response before requesting another
    - Location of the whitelist file to use (relative to the bot.py file)
- Default/custom group properties:
    - The group id
    - The banned entities for a 1st text message send (URL, email, phone number etc)
    - Seconds to wait for user to press 'I'm not a robot!' button before kicking
    - Seconds to restrict a user after pressing the 'I'm not a robot!' button
    - Seconds to wait for user to send their 1st message after their restriction before kicking
    - Seconds to monitor new user's messages after sending 1st message for anything prohibited
    - Seconds to wait after success/failed user join before deleting bot messages from chat

The following properties can be modified via in-group commands:
- Seconds to wait for user to press 'I'm not a robot!' button before kicking
- Seconds to restrict a user after pressing the 'I'm not a robot!' button
- Seconds to wait for user to send their 1st message after their restriction before kicking
- Seconds to monitor new user's messages after sending 1st message for anything prohibited
- Seconds to wait after success/failed user join before deleting bot messages from chat


### Whitelist
To prevent just anyone adding the bot to their own group (and sucking up your server resources/bandwidth), the bot also makes use of a group whitelist, in the form of a text file (whitelist.txt by default, can be changed in the config file if required):
- If whitelist.txt is present, the bot will switch over to whitelist mode. If it recieves an incoming message from a group not in its whitelist (including the message when it is added to the group), it will send a message to that group saying it doesn't support being added to any group, and leaves it
- If whitelist.txt is not present (or it fails to process whitelist.txt), the bot will switch over to non-whitelist mode. It will handle incoming joins/messages from any group it's been added to

The only current way to add a group to your whitelist is manually adding the group ID to whitelist.txt. Each new group should be placed on its own line. When the bot is added to a group not in its whitelist (when in whitelist mode), it should print the group ID it was added into to standard output, which can then be added to whitelist.txt

Currently, the bot must be restarted to apply any new changes to the whitelist


## Dependencies
 - [Python 3.8+](https://www.python.org/downloads/) - May work with earlier versions, but I haven't tested it on older than Python 3.8.5
 - [Requests](https://requests.readthedocs.io/en/master/)

 Or see requirements.txt

## Usage

To run the script, call it, passing in your Telegram bot token:

```bash
$ python3 bot.py [OPTIONS]...
```

See also `python3 bot.py --help`.

### Options

Required:

`-t` or `--token`: Telegram Bot token to use for connection to the API.

## Compatibility
I've been running this bot successfully on MacOS 10.14.6, and Ubuntu 20.04.1 LTS. I haven't tested its functionality on Windows
