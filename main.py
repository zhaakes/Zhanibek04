import os
import config
import telebot
#from bitcoinrpc.authproxy import AuthServiceProxy

bot = telebot.TeleBot(config.token)
#rpc_connection = AuthServiceProxy(f"http://{config.rpc_user}:{config.rpc_password}@{config.rpc_host}:{config.rpc_port}")

@bot.message_handler(commands=['start', 'getnewaddress', 'getbalance', 'walletinfo', 'listaddresses', 'switchaddress', 'getaddressinfo', 'send'])
def handle_command(message):
    if message.text.startswith('/start'):
        send_welcome(message)
    elif message.text.startswith('/getnewaddress'):
        get_new_address(message)
    elif message.text.startswith('/getbalance'):
        get_balance(message)
    elif message.text.startswith('/walletinfo'):
        wallet_info(message)
    elif message.text.startswith('/listaddresses'):
        list_addresses(message)
    elif message.text.startswith('/switchaddress'):
        switch_address(message)
    elif message.text.startswith('/getaddressinfo'):
        get_address_info(message)
    elif message.text.startwith('/send'):
         send_coins(message)
    else:
        bot.send_message(message.chat.id, "Unknown command. Available commands: /getnewaddress, /getbalance, /walletinfo, /listaddresses, /switchaddress, /getaddressinfo, /send")


# Начальное приветствие
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! I am a command bot. Select one of the following commands:\n/getnewaddress - Get a new address\n/getbalance - Get balance\n/walletinfo - Get wallet information\n/listaddresses - List all addresses\n/switchaddress - Switch to another address (Usage: /switchaddress <address>) \n/getaddressinfo - Get address information (Usage: /getaddressinfo <address>)\n/send - Send coins (Usage: /send <sender_address> <recipient_address> <amount>)")

# Получить новый адрес
@bot.message_handler(commands=['getnewaddress'])
def get_new_address(message):
    new_address = os.popen("~/kzcash-cli getnewaddress").read()
    bot.send_message(message.chat.id, f"New address generated: {new_address}")

# Получить баланс
@bot.message_handler(commands=['getbalance'])
def get_balance(message):
    balance = os.popen("~/kzcash-cli getbalance").read()
    bot.send_message(message.chat.id, f"Current balance: {balance}")

# Получить информацию о кошельке
@bot.message_handler(commands=['walletinfo'])
def wallet_info(message):
    info = os.popen("~/kzcash-cli getwalletinfo").read()
    bot.send_message(message.chat.id, f"Wallet info: {info}")

# Перечислить все адреса в кошельке
@bot.message_handler(commands=['listaddresses'])
def list_addresses(message):
    addresses = os.popen("~/kzcash-cli listreceivedbyaddress 0 true")  # Получаем все адреса
    bot.send_message(message.chat.id, f"Addresses in wallet: {', '.join(addresses)}")

# Переключиться на другой адрес
@bot.message_handler(commands=['switchaddress'])
def switch_address(message):
    try:
        address = message.text.split()[1]  # Получаем адрес из сообщения
        # Проверяем, существует ли адрес
        check_address = os.popen(f"~/kzcash-cli getbalance {address}").read()
        if check_address.strip() == "":
            raise Exception("Address does not exist")
        # Если адрес существует, сообщаем об этом
        bot.send_message(message.chat.id, f"Switched to address: {address}")
    except IndexError:
        bot.send_message(message.chat.id, "Please provide the address. Usage: /switchaddress <address>")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# Получения информацию о новом адресе
@bot.message_handler(commands=['getaddressinfo'])
def get_address_info(message):
    try:
        address = message.text.split()[1]  # Получаем адрес из сообщения
        address_info = os.popen(f"~/kzcash-cli getreceivedbyaddress {address}").read()
        bot.send_message(message.chat.id, f"Address info for {address}:\n{address_info}")
    except IndexError:
        bot.send_message(message.chat.id, "Please provide the address. Usage: /getaddressinfo <address>")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@bot.message_handler(commands=['send'])
def send_coins(message):
    try:
        parts = message.text.split()  # Разбиваем сообщение на части
        if len(parts) != 4:
            raise ValueError("Incorrect command format. Use: /send <sender_address> <recipient_address> <amount>")

        sender_address, recipient_address, amount = parts[1], parts[2], parts[3]
        amount = float(amount)  # Преобразуем строку в число
        # Здесь должна быть логика проверки адресов и суммы

        # Создаем raw транзакцию без подписи
        create_command = f"~/kzcash-cli createrawtransaction '[{{\"{sender_address}\":{amount}}}]' '{{\"{recipient_address}\":{amount}}}'"
        raw_transaction = subprocess.run(create_command, shell=True, capture_output=True, text=True).stdout.strip()

        # Добавляем комиссию к транзакции
        fund_command = f"~/kzcash-cli fundrawtransaction \"{raw_transaction}\" '{{\"feeRate\":0.001}}'"
        funded_transaction = subprocess.run(fund_command, shell=True, capture_output=True, text=True).stdout.strip()

        # Подписываем транзакцию и отправляем
        sign_command = f"~/kzcash-cli signrawtransactionwithwallet \"{funded_transaction['hex']}\""
        signed_transaction = subprocess.run(sign_command, shell=True, capture_output=True, text=True).stdout.strip()

        send_command = f"~/kzcash-cli sendrawtransaction \"{signed_transaction['hex']}\""
        result = subprocess.run(send_command, shell=True, capture_output=True, text=True)
        
        bot.send_message(message.chat.id, f"Coins sent successfully: {result.stdout.strip()}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error sending coins: {str(e)}")

# Обработчик неизвестных команд
@bot.message_handler(func=lambda message: True)
def repeat_all_messages(message):
    bot.send_message(message.chat.id, "Unknown command. Available commands: /getnewaddress, /getbalance, /walletinfo, /listaddresses, /switchaddress, /getaddressinfo, /send")

if __name__ == '__main__':
    bot.polling(none_stop=True)
