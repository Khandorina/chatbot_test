import requests
import time
import json
import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import sqlite3

with open('tyumen.json', 'r', encoding='utf-8') as f:  # открыли файл с данными
    restoraunts = (json.load(f))  # загнали все, что получилось в переменную

TOKEN = '5607855177:AAHrahFY-63KV0132jKAMnmCU04dM4I2oCA'
URL = 'https://api.telegram.org/bot'

def get_updates(offset=0):
    result = requests.get(f'{URL}{TOKEN}/getUpdates?offset={offset}').json()
    return result['result']

def send_message(chat_id, text):
    requests.get(f'{URL}{TOKEN}/sendMessage?chat_id={chat_id}&text={text}')

def reply_keyboard(chat_id, text):
    reply_markup ={ "keyboard": [["Оценить ресторан"], [{"request_location":True, "text":"Найти ресторан"}]], "resize_keyboard": True, "one_time_keyboard": True}
    data = {'chat_id': chat_id, 'text': text, 'reply_markup': json.dumps(reply_markup)}
    requests.post(f'{URL}{TOKEN}/sendMessage', data=data)

def send_photo_file(chat_id, img):
    files = {'photo': open(img, 'rb')}
    requests.post(f'{URL}{TOKEN}/sendPhoto?chat_id={chat_id}', files=files)


def find_rests(user_id, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = {}".format(user_id))
    r = cursor.fetchall() # print(r): [(1091335251, '57.15024', '65.58873', '1 км', 'европейская', '$$$')]
    cursor.close()

    #Вот тут должен вызываться метод который вернет рестораны по умному алгоритму
    #вида return restorani(r[0],r[1],r[2],r[3],r[4],r[5])
    #или return restorani(r)
    return "Рестораны: нету"

def check_message(m,db):
    chat_id = m['message']['chat']['id']
    user_id = m['message']['from']['id']
    message = m['message'].get('text')
    if (user_location := m['message'].get('location')):
        print(user_location)
        user_try_insert(db, user_id)
        cursor = db.cursor()
        print("UPDATE users SET lon = {}, lat = {} WHERE user_id = {}".format(user_location['longitude'], user_location['latitude'], user_id))
        cursor.execute("UPDATE users SET lon = {}, lat = {} WHERE user_id = {}".format(user_location['longitude'], user_location['latitude'], user_id))
        db.commit()
        cursor.close()

        reply_markup ={ "keyboard": [["1 км","2 км","5 км"]], "resize_keyboard": True, "one_time_keyboard": True}
        data = {'chat_id': chat_id, 'text': "Как близко ищем ресторан?", 'reply_markup': json.dumps(reply_markup)}
        requests.post(f'{URL}{TOKEN}/sendMessage', data=data)
    elif message.lower() in ['1 км','2 км','5 км']:
        user_try_insert(db, user_id)
        cursor = db.cursor()
        cursor.execute("UPDATE users SET dist = '{}' WHERE user_id = {}".format(message.lower(), user_id))
        db.commit()
        cursor.close()

        reply_markup ={ "keyboard": [['$','$$','$$$', '$$$$']], "resize_keyboard": True, "one_time_keyboard": True}
        data = {'chat_id': chat_id, 'text': "Какой ценовой категории?", 'reply_markup': json.dumps(reply_markup)}
        requests.post(f'{URL}{TOKEN}/sendMessage', data=data)
    elif message.lower() in ['$','$$','$$$', '$$$$']:
        user_try_insert(db, user_id)
        cursor = db.cursor()
        cursor.execute("UPDATE users SET price = '{}' WHERE user_id = {}".format(message.lower(), user_id))
        db.commit()
        cursor.close()

        reply_markup ={ "keyboard": [["европейская","чешская"],["вегетарианцев","кафе"],["перекусы","восточноевропейская"],["грузинская","итальянская"],["японская"]], "resize_keyboard": True, "one_time_keyboard": True}
        data = {'chat_id': chat_id, 'text': "Какую кухню ищем?", 'reply_markup': json.dumps(reply_markup)}
        requests.post(f'{URL}{TOKEN}/sendMessage', data=data)
    elif message.lower() in ['европейская','чешская','вегетарианцев','кафе','перекусы','восточноевропейская','грузинская','итальянская','японская']:
        user_try_insert(db, user_id)
        cursor = db.cursor()
        cursor.execute("UPDATE users SET kitchen = '{}' WHERE user_id = {}".format(message.lower(), user_id))
        db.commit()
        cursor.close()

        rests = find_rests(user_id, db)
        send_message(chat_id,rests)

    else:
        reply_markup ={ "keyboard": [["Оценить ресторан"], [{"request_location":True, "text":"Найти ресторан"}]], "resize_keyboard": True, "one_time_keyboard": True}
        data = {'chat_id': chat_id, 'text': 'Доступные комманды', 'reply_markup': json.dumps(reply_markup)}
        requests.post(f'{URL}{TOKEN}/sendMessage', data=data)


def user_try_insert(db, user_id):
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users ('user_id') VALUES ({});".format(user_id))
        db.commit()
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    cursor.close()


def run():
    sqlite_connection = connect_to_sqlite('sqlite_python.db')

    while True:
        time.sleep(1)
        get = get_updates()
        if len(get) != 0:
            update_id = get[-1]['update_id']  # Присваиваем ID последнего отправленного сообщения боту
            while True:
                time.sleep(2)
                messages = get_updates(update_id) # Получаем обновления
                for message in messages:
                    if update_id < message['update_id']:# Если в обновлении есть ID больше чем ID последнего сообщения, значит пришло новое сообщение
                        update_id = message['update_id']# Присваиваем ID последнего отправленного сообщения боту
                        check_message(message, sqlite_connection) # Отвечаем


def connect_to_sqlite(dbname):
    try:
        sqlite_connection = sqlite3.connect(dbname)
        cursor = sqlite_connection.cursor()
        print("База данных создана и успешно подключена к SQLite")
        sqlite_select_query = "select sqlite_version();"
        cursor.execute(sqlite_select_query)
        record = cursor.fetchall()
        print("Версия базы данных SQLite: ", record)
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    return sqlite_connection


if __name__ == '__main__':
    run()
