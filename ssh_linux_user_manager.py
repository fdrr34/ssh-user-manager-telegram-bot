import uuid
import pyodbc
import paramiko
import re
import datetime
import time
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)
from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

# Create an SSH client

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Define conversation states
NAME, PASSWORD, EXPIRE_DATE, MAX_USERS, DEL_USER, CHECK_TOKEN, CHOOSE_ADDUSER_SERVER, CHOOSE_DELUSER_SERVER, CHOOSE_LISTUSER_SERVER, GET_PRICE, SALE_TYPE, NAME_SERVER, IP_SERVER, PORT_SERVER, CHOOSE_DEL_SERVER, CONFIRM_DEL_SERVER = range(
    16)

count = 0
servers = []

#
# START start
#


def start(update, context):
    text = "Hello, I'm ssh bot user maker :)\nPlease enter token: "
    send_message(context, update.effective_chat.id, True, text)

    return CHECK_TOKEN


def check_token(update, context):
    token = update.message.text

    if token == "b$%\sdvsdvzxcv#^\dvsdvvsv&$*eghn;Pf":

        keyboard = getKeyboard(1)
        text = 'Welcome dear admin :)'
        send_message(context, update.message.chat_id, False, text, keyboard)

        return ConversationHandler.END
    else:
        text = 'you entered wrong token :(\n Enter /start to start again'
        send_message(context, update.message.chat_id, True, text)

        return start(update, context)

#
# END start
#

#
# START add user
#


def add_user(update, context):
    keyboard = getKeyboard(2)
    text = "Choose server between servers of below or send servers name:"
    send_message(context, update.effective_chat.id, False, text, keyboard)

    return CHOOSE_ADDUSER_SERVER


def choose_adduser_server(update, context):
    context.user_data['server'] = update.message.text
    filtered_server = [
        conn for conn in servers if conn["name"] == context.user_data['server']]

    if len(filtered_server) > 0:

        context.user_data['ip'] = filtered_server[0]['ip']
        context.user_data['port'] = str(filtered_server[0]['port'])
        ssh.connect(filtered_server[0]['ip'], port=filtered_server[0]['port'],
                    username=filtered_server[0]['username'], password=filtered_server[0]['password'])

        keyboard = getKeyboard(4)
        text = "Please choose the sale type:"
        send_message(context, update.effective_chat.id, False, text, keyboard)

        return SALE_TYPE
    else:
        text = "!! Please a Choose server between servers of below or send servers name:"
        send_message(context, update.effective_chat.id, True, text)

        return add_user(update, context)
    
def sale_type(update, context):
    context.user_data['sale_type'] = update.message.text

    if update.message.text == 'revival':
        context.user_data['sale_type'] = 1
    else:
        context.user_data['sale_type'] = 0

    keyboard = getKeyboard(3)
    text = "Tips:\n* username most be lowwercase.\n* date most be in format year-month-day like 2023-04-26\n* please enter english numbers :)\nGood luck"
    send_message(context, update.effective_chat.id, False, text, keyboard)
    text = "Please enter user name:\nusername most be without cammel case :)"
    send_message(context, update.effective_chat.id, True, text)

    return NAME

def name(update, context):
    context.user_data['name'] = update.message.text
    output = get_list_users()

    if any(x.isupper() for x in update.message.text):
        text = "!! Please enter a user name without cammelcase :("
        send_message(context, update.effective_chat.id, True, text)

        return NAME
    elif (context.user_data['name'] in output) and (context.user_data['sale_type'] == 0):
        text = "!! The entered username has already been created on the server :("
        send_message(context, update.effective_chat.id, True, text)

        return NAME
    else:
        ssh.exec_command(
            'sudo adduser --disabled-password --gecos "" ' + context.user_data['name'])

        text = "Please enter a password:"
        send_message(context, update.effective_chat.id, True, text)

        return PASSWORD


def password(update, context):
    context.user_data['password'] = update.message.text

    if len(context.user_data['password']) < 8:
        text = "!! Password length most be bigger than 8 characters :("
        send_message(context, update.effective_chat.id, True, text)

        return PASSWORD
    else:
        current_date = get_current_date()
        text = "Please enter the expire date:\n  For example " + current_date
        send_message(context, update.effective_chat.id, True, text)

        ssh.exec_command('sudo echo "' + context.user_data['name'] +
                         ':'+context.user_data['password']+'" | chpasswd')
        ssh.exec_command('service ssh restart')

        return EXPIRE_DATE


def expire_date(update, context):
    context.user_data['expire_date'] = update.message.text

    if is_valid_date(update.message.text):
        text = "Please enter the price:"
        send_message(context, update.effective_chat.id, True, text)

        ssh.exec_command('sudo chage -E '+context.user_data['expire_date'] +
                         ' '+context.user_data['name'])

        return GET_PRICE
    else:
        current_date = get_current_date()
        text = "!! Please enter the right value:\n like "+current_date+" year-month-day"
        send_message(context, update.effective_chat.id, True, text)

        return EXPIRE_DATE


def get_price(update, context):
    context.user_data['price'] = update.message.text

    text = "Please enter the maximum login of user:"
    send_message(context, update.effective_chat.id, True, text)

    return MAX_USERS


def max_users(update, context):
    context.user_data['max_users'] = update.message.text

    if isinstance(int(context.user_data['max_users']), int):
        context.user_data['creator'] = update.effective_user.username
        ssh.exec_command('sudo echo "'+context.user_data['name']+' hard    maxlogins  ' +
                         context.user_data['max_users']+'" >> /etc/security/limits.conf')
        ssh.close()

        change_on_database(context, 1)

        keyboard = getKeyboard(1)
        text = "User added:\nServer name:" + context.user_data['server']+"\nIP: "+context.user_data['ip'] + "\nPort: "+context.user_data['port']+"\nUserName: " + context.user_data['name'] + \
            "\nPassword: "+context.user_data['password'] + "\nMaximum number of users: " + \
            context.user_data['max_users']+"\nExpire Date: " + \
            context.user_data['expire_date']
        send_message(context, update.effective_chat.id, False, text, keyboard)

        context.user_data.clear()
        return ConversationHandler.END

    else:
        text = "!! please enter number :("
        send_message(context, update.effective_chat.id, True, text)

        return MAX_USERS

#
# END addd user
#

#
# START delete user
#


def delete_user(update, context):
    keyboard = getKeyboard(2)
    text = "Choose server between servers of below or send servers name:"
    send_message(context, update.effective_chat.id, False, text, keyboard)

    return CHOOSE_DELUSER_SERVER


def choose_deluser_server(update, context):
    context.user_data['server'] = update.message.text
    filtered_server = [
        conn for conn in servers if conn["name"] == context.user_data['server']]

    if len(filtered_server) > 0:
        ssh.connect(filtered_server[0]['ip'], port=filtered_server[0]['port'],
                    username=filtered_server[0]['username'], password=filtered_server[0]['password'])
        output = get_list_users()
        outputText = "Active users in this server are:\n" + output
        send_message(context, update.effective_chat.id, True, outputText)

        keyboard = getKeyboard(3)
        text = "Please enter user name:"
        send_message(context, update.effective_chat.id, False, text, keyboard)

        return DEL_USER
    else:
        text = "Please a Choose server between servers of below or send servers name:"
        send_message(context, update.effective_chat.id, True, text)

        return delete_user(update, context)


def del_user(update, context):
    context.user_data['name'] = update.message.text
    output = get_list_users()

    if context.user_data['name'] in output:
        ssh.exec_command('sudo pkill -u ' + context.user_data['name'])
        ssh.exec_command('sudo userdel -r ' + context.user_data['name'])
        ssh.exec_command('service ssh restart')
        ssh.close()
        change_on_database(context, 2)
        keyboard = getKeyboard(1)
        text = 'User '+context.user_data['name']+' has been deleted.'
        send_message(context, update.message.chat_id, False, text, keyboard)

        context.user_data.clear()
        return ConversationHandler.END
    else:
        text = "!! this user it dosent exist :(\nIn this server active users are:"
        send_message(context, update.effective_chat.id, True, text)
        send_message(context, update.effective_chat.id, True, output)

        return delete_user(update, context)

#
# END delete user
#

#
# START list of users
#


def list_users(update, context):
    keyboard = getKeyboard(2)
    text = "Choose server between servers of below or send servers name:"
    send_message(context, update.effective_chat.id, False, text, keyboard)

    return CHOOSE_LISTUSER_SERVER


def choose_listuser_server(update, context):
    context.user_data['server'] = update.message.text
    filtered_server = [
        conn for conn in servers if conn["name"] == context.user_data['server']]

    if len(filtered_server) > 0:
        ssh.connect(filtered_server[0]['ip'], port=filtered_server[0]['port'],
                    username=filtered_server[0]['username'], password=filtered_server[0]['password'])

        output = get_list_users()
        keyboard = getKeyboard(1)
        send_message(context, update.effective_chat.id,
                     False, output, keyboard)
        ssh.close()
        return ConversationHandler.END
    else:
        text = "!! Please a Choose server between servers of below or send servers name:"
        send_message(context, update.effective_chat.id, True, text)
        return list_users(update, context)
#
# END list of users
#

#
# START add to servers
#


def add_servers(update, context):
    keyboard = getKeyboard(3)
    text = "Please send server name:\nname must be without space between it."
    send_message(context, update.effective_chat.id, False, text, keyboard)

    return NAME_SERVER


def get_name_server(update, context):
    context.user_data['serverName'] = update.message.text
    text = "Please send ip server:",
    send_message(context, update.effective_chat.id, True, text)

    return IP_SERVER


def get_ip_server(update, context):
    context.user_data['ip'] = update.message.text
    text = "Please send port server:"
    send_message(context, update.effective_chat.id, True, text)

    return PORT_SERVER


def get_port_server(update, context):
    context.user_data['port'] = update.message.text
    saveServers(context)
    keyboard = getKeyboard(1)
    text = "Server: "+context.user_data['serverName']+"\nIp: "+context.user_data['ip'] + \
        "\nPort: "+context.user_data['port']+"\nadded to list of servers."
    send_message(context, update.effective_chat.id, False, text, keyboard)

    context.user_data.clear()
    return ConversationHandler.END

#
# END add to servers
#

#
# START delete servers
#


def delete_servers(update, context):
    keyboard = getKeyboard(2)
    text = "Choose server between servers of below or send servers name:"
    send_message(context, update.effective_chat.id, False, text, keyboard)

    return CHOOSE_DEL_SERVER


def choose_del_server(update, context):
    context.user_data['serverName'] = update.message.text
    filtered_server = [
        conn for conn in servers if conn["name"] == context.user_data['serverName']]
    keyboard = [[KeyboardButton('YES'), KeyboardButton('NO')],]
    text = "Server: "+filtered_server[0]['name']+"\nIp: "+filtered_server[0]['ip'] + \
        "\nPort: "+str(filtered_server[0]['port']) + \
        "\nAre you sure for delete this?"
    send_message(context, update.effective_chat.id, False, text, keyboard)
    return CONFIRM_DEL_SERVER


def confirm_del_server(update, context):
    context.user_data['server'] = update.message.text
    if context.user_data['server'] == "YES":
        deleteServer(context)
        keyboard = getKeyboard(1)
        text = "Server Deleted."
        send_message(context, update.effective_chat.id, False, text, keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    else:
        context.user_data.clear()
        keyboard = getKeyboard(1)
        text = "Operation canceled."
        send_message(context, update.effective_chat.id, False, text, keyboard)
        return ConversationHandler.END

#
# END delete servers
#


#
# START cancel
#


def cancel(update, context):
    context.user_data.clear()
    keyboard = getKeyboard(1)
    ssh.close()
    text = "Operation canceled."
    send_message(context, update.effective_chat.id, False, text, keyboard)
    return ConversationHandler.END

#
# END cancel
#

#
# START private func
#


def is_valid_date(date_string):
    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def get_current_date():
    current_time = time.localtime()
    formatted_date = time.strftime("%Y-%m-%d", current_time)
    return formatted_date


def getKeyboard(keyboardType):
    if int(keyboardType) == 1:
        keyboard = [
            [KeyboardButton('/add_user'), KeyboardButton('/delete_user'), KeyboardButton(
                '/list_users')], [KeyboardButton('/add_server'), KeyboardButton('/delete_server')]
        ]
    elif int(keyboardType) == 2:
        name_servers = [server["name"] for server in servers]
        split_arrays = []
        for i in range(0, len(name_servers), 4):
            subarra = name_servers[i:i+4]
            split_arrays.append(subarra)
        formatted_arrays = []
        for subarray in split_arrays:
            formatted_subarray = [KeyboardButton(name) for name in subarray]
            formatted_arrays.append(formatted_subarray)
        keyboard = formatted_arrays

    elif int(keyboardType) == 3:
        keyboard = [
            [KeyboardButton('/cancel')],
        ]
    elif int(keyboardType) == 4:
        keyboard = [
            [KeyboardButton('new user'), KeyboardButton('revival')],
        ]

    return keyboard


def send_message(context, chatId, justMessage, message, keyboard=getKeyboard(1)):
    if justMessage:
        context.bot.send_message(
            chat_id=chatId,
            text=message
        )
    else:
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True)
        context.bot.send_message(
            chat_id=chatId,
            text=message,
            reply_markup=reply_markup
        )


def get_list_users():
    stdin, stdout, stderr = ssh.exec_command(
        "getent passwd | grep -E '/bin/(bash|sh)'")
    res = stdout.read().decode('utf-8')
    global count
    count = 0
    output = re.sub(r":x:.*?\n", add_number, res)

    return output


def change_on_database(context, changeType):
    # Establish a connection
    try:
        conn = pyodbc.connect(
            'Driver={ODBC Driver 17 for SQL Server};Server=;Database=;UID=;PWD=;')
    except pyodbc.Error as ex:
        print("Error connecting to SQL Server:", ex)

    # Create a cursor
    cursor = conn.cursor()
    if int(changeType) == 1:
        save_On_database(context, conn, cursor)
    if int(changeType) == 2:
        delete_On_database(context, conn, cursor)


def save_On_database(context, conn, cursor):
    # Execute the SQL query
    context.user_data['uuid'] = get_uuid_id()
    current_date = get_current_date()
    query = "INSERT INTO [dbo].[UserInfo] ([GuId], [Creator], [PurchaseDate], [ServerName], [Username], [Password], [MaximumUser], [ExpireDate], [Price], [SaleType],[IsDeleted]) VALUES  (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)"
    values = (context.user_data['uuid'], context.user_data['creator'], current_date, context.user_data['server'], context.user_data['name'],
              context.user_data['password'], context.user_data['max_users'], context.user_data['expire_date'], context.user_data['price'],  context.user_data['sale_type'], 0)
    cursor.execute(query, values)
    # Commit the transaction
    conn.commit()
    # Close the cursor and connection
    cursor.close()
    conn.close()


def delete_On_database(context, conn, cursor):
    # Execute the SQL query
    query = """
    UPDATE [dbo].[UserInfo]
        SET IsDeleted = 1 , [DeletedDate] = ?
        WHERE [ServerName] = ? AND [Username] = ?
    """

    # Define the values for the placeholders
    deleted_Date = get_current_date()
    server_name = context.user_data['server']
    username = context.user_data['name']

    # Execute the parameterized query
    cursor.execute(query, deleted_Date, server_name, username)

    # Commit the transaction
    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()


def get_uuid_id():
    return str(uuid.uuid4())


def saveServers(context):
    newData = {
        "name": context.user_data['serverName'],
        "ip": context.user_data['ip'],
        "port": context.user_data['port'],
        "username": "root",
        "password": ""
    }
    servers.append(newData)


def deleteServer(context):
    name_to_delete = context.user_data['serverName']
    to_delete = [obj for obj in servers if obj["name"] == name_to_delete]
    for obj in to_delete:
        servers.remove(obj)


def add_number(match):
    global count	
    count += 1
    return "\n"+str(count)+": "

#
# END
#


def main():
    # Create the conversation handler
    start_handler = ConversationHandler(
        entry_points=[CommandHandler(
            'start', start)],
        states={
            CHECK_TOKEN: [MessageHandler(
                Filters.text & ~Filters.command, check_token)]
        },
        fallbacks=[CommandHandler('cancel', cancel)])

    addUser_handler = ConversationHandler(
        entry_points=[CommandHandler('add_user', add_user)],
        states={
            CHOOSE_ADDUSER_SERVER: [MessageHandler(Filters.text & ~Filters.command, choose_adduser_server)],
            SALE_TYPE: [MessageHandler(Filters.text & ~Filters.command, sale_type)],
            NAME: [MessageHandler(Filters.text & ~Filters.command, name)],
            PASSWORD: [MessageHandler(Filters.text & ~Filters.command, password)],
            EXPIRE_DATE: [MessageHandler(Filters.text & ~Filters.command, expire_date)],
            GET_PRICE: [MessageHandler(Filters.text & ~Filters.command, get_price)],
            MAX_USERS: [MessageHandler(
                Filters.text & ~Filters.command, max_users)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    deleteUser_handler = ConversationHandler(
        entry_points=[CommandHandler('delete_user', delete_user)],
        states={
            CHOOSE_DELUSER_SERVER: [MessageHandler(Filters.text & ~Filters.command, choose_deluser_server)],
            DEL_USER: [MessageHandler(
                Filters.text & ~Filters.command, del_user)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    listUsers_handler = ConversationHandler(
        entry_points=[CommandHandler('list_users', list_users)],
        states={
            CHOOSE_LISTUSER_SERVER: [MessageHandler(
                Filters.text & ~Filters.command, choose_listuser_server)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    addServer_handler = ConversationHandler(
        entry_points=[CommandHandler('add_server', add_servers)],
        states={
            NAME_SERVER: [MessageHandler(
                Filters.text & ~Filters.command, get_name_server)],
            IP_SERVER: [MessageHandler(
                Filters.text & ~Filters.command, get_ip_server)],
            PORT_SERVER: [MessageHandler(
                Filters.text & ~Filters.command, get_port_server)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    delServer_handler = ConversationHandler(
        entry_points=[CommandHandler('delete_server', delete_servers)],
        states={
            CHOOSE_DEL_SERVER: [MessageHandler(
                Filters.text & ~Filters.command, choose_del_server)],
            CONFIRM_DEL_SERVER: [MessageHandler(
                Filters.text & ~Filters.command, confirm_del_server)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Initialize the telegram bot
    updater = Updater(
        token='', use_context=True)
    dispatcher = updater.dispatcher

    # Add conversation handler and start polling for updates
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(addUser_handler)
    dispatcher.add_handler(deleteUser_handler)
    dispatcher.add_handler(listUsers_handler)
    dispatcher.add_handler(addServer_handler)
    dispatcher.add_handler(delServer_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
