import logging
import schedule
from threading import Thread
from time import sleep
from secrets import API_TOKEN

import telegram.bot as tb
from telegram import Update
from telegram.ext import (Updater,
                          CommandHandler,
                          CallbackContext,
                          MessageHandler,
                          Filters)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define API Token
TOKEN = API_TOKEN

# ADMINS = [Remo]
ADMINS = [1443234158]


def scheduleChecker() -> None:
    while True:
        schedule.run_pending()
        sleep(.25)


# Function to know if snapbot is working
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('[RemoBot] RemoBot has started successfully')


# Initialize list to hold all messages.  Cannot be in the function otherwise
#   the list would be reset every time the function is called (i.e. every
#   time there is a message sent to the chat)
messages = []


# storeChat() appends each message sent to a list, then sends the message to stdout
def storeChat(update: Update, context: CallbackContext) -> None:
    # Append message to list of messages
    messages.append(update.message)

    # Try...except necessary in case message sent was a photo, video, or GIF
    #   (it would be a NoneType, not string, if that were the case)
    try:
        print(str(update.message.from_user.first_name) + ': ' + update.message.text)
    except TypeError:
        print(str(update.message.from_user.first_name) + ': [Sent a photo, video, or GIF]')


# cleanChatCommand() is the cleanChat() for when /purge is called in the chat.
#   This way, update and context can be passed to it
def cleanChatCommand(update: Update, context: CallbackContext) -> None:
    global messages

    initialMessageLength = str(len(messages))
    # If user is an admin...
    if update.effective_user.id in ADMINS:
        # ...iterate through messages
        for message in messages:
            if message.message_id not in pinnedMessages:
                try:
                    # Delete message, then send to the chat and stdout that the messages
                    #   were deleted
                    context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
                except:
                    pass

        print('[RemoBot] ' + initialMessageLength + ' messages in the last 24 hours successfully deleted')

    messages = []


# cleanChatTimed() is the cleanChat() for when the scheduler runs cleanChat().
#   this way, no update or context need to be passed
def cleanChatTimed() -> None:
    global messages

    # Initialize bot
    bot = tb.Bot(TOKEN)

    initialMessageLength = str(len(messages) - len(pinnedMessages))

    # Iterate through messages
    for message in messages:
        if message.message_id not in pinnedMessages:
            try:
                # Delete message, then send to the chat and stdout that the messages
                #   were deleted
                bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
            except:
                pass

    print('[RemoBot] ' + initialMessageLength + ' messages in the last 24 hours successfully deleted')

    messages = []


pinnedMessages = []


def makePinList(update: Update, context: CallbackContext) -> None:
    pinnedMessages.append(update.message.pinned_message.message_id)


# TODO:
#       Thread message timers so only one message gets deleted at its
#         24 hour mark
def main():
    # Initialize Updater
    updater = Updater(TOKEN, use_context=True)

    # Every 24 hours, clean the chat.  The thread is necessary so that
    #   jobs can happen simultaneously
    schedule.every().day.at('06:00').do(cleanChatTimed)
    Thread(target=scheduleChecker).start()

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Listen for whenever a message is sent to the chat
    storeChatHandler = MessageHandler(Filters.text & (~Filters.command) |
                                      Filters.photo |
                                      Filters.video |
                                      Filters.document.gif |
                                      Filters.sticker |
                                      Filters.poll, storeChat)

    pinnedMessageHandler = MessageHandler(Filters.status_update.pinned_message, makePinList)

    dispatcher.add_handler(pinnedMessageHandler)
    dispatcher.add_handler(storeChatHandler)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("purge", cleanChatCommand, run_async=True))

    # Start the bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
