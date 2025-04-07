import telebot
from telebot import types
import json
import re
import datetime
import threading
import time

TOKEN = 'YOUR_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

BIRTHDAYS_FILE = "birthdays.json"

def save_user_full(user_id, username, name, birth_date, chat_id):
    try:
        with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"users": []}

    for user in data["users"]:
        if user["user_id"] == user_id:
            user["name"] = name
            user["birth_date"] = birth_date
            user["username"] = username
            if chat_id not in user["chats"]:
                user["chats"].append(chat_id)
            break
    else:
        data["users"].append({
            "user_id": user_id,
            "username": username,
            "name": name,
            "birth_date": birth_date,
            "chats": [chat_id]
        })

    with open(BIRTHDAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete_profile(message, lang='ru'):
    user_id = message.from_user.id
    try:
        with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"users": []}

    original_len = len(data["users"])
    data["users"] = [user for user in data["users"] if user["user_id"] != user_id]

    with open(BIRTHDAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if len(data["users"]) < original_len:
        bot.send_message(message.chat.id,
                         "✅ Ваш профиль был удалён." if lang == 'ru' else "✅ Your profile has been deleted.")
    else:
        bot.send_message(message.chat.id,
                         "ℹ️ Профиль не найден." if lang == 'ru' else "ℹ️ Profile not found.")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🇷🇺 Русский"), types.KeyboardButton("🇬🇧 English"))
    bot.send_message(message.chat.id, "🇷🇺 Выбери язык! / 🇬🇧 Choose the language!", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == '🇷🇺 Русский':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton('Добавить день рождения'),
            types.KeyboardButton('Удалить профиль')
        )
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)

    elif message.text == '🇬🇧 English':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton('Add birthday'),
            types.KeyboardButton('Delete profile')
        )
        bot.send_message(message.chat.id, 'Choose an action:', reply_markup=markup)

    elif message.text == 'Добавить день рождения':
        msg = bot.send_message(message.chat.id, 'Введите данные:\nИмя Фамилия\nДД.ММ.ГГГГ')
        bot.register_next_step_handler(msg, process_birthday_input_ru)

    elif message.text == 'Add birthday':
        msg = bot.send_message(message.chat.id, 'Enter data:\nName Surname\nDD.MM.YYYY')
        bot.register_next_step_handler(msg, process_birthday_input_en)

    elif message.text == 'Удалить профиль':
        delete_profile(message, lang='ru')

    elif message.text == 'Delete profile':
        delete_profile(message, lang='en')

def process_birthday_input_ru(message):
    pattern = r'^([А-ЯЁа-яёA-Za-z]+ [А-ЯЁа-яёA-Za-z]+)\n(\d{2}\.\d{2}\.\d{4})$'
    match = re.match(pattern, message.text.strip())
    if match:
        name = match.group(1)
        birth_date = match.group(2)
        save_user_full(
            user_id=message.from_user.id,
            username=message.from_user.username,
            name=name,
            birth_date=birth_date,
            chat_id=message.chat.id
        )
        bot.send_message(message.chat.id, f'✅ Принято: {name}, {birth_date}')
    else:
        msg = bot.send_message(message.chat.id,
            '❌ Неверный формат!\nПример:\nИван Иванов\n01.01.2000')
        bot.register_next_step_handler(msg, process_birthday_input_ru)

def process_birthday_input_en(message):
    pattern = r'^([A-Za-z]+ [A-Za-z]+)\n(\d{2}\.\d{2}\.\d{4})$'
    match = re.match(pattern, message.text.strip())
    if match:
        name = match.group(1)
        birth_date = match.group(2)
        save_user_full(
            user_id=message.from_user.id,
            username=message.from_user.username,
            name=name,
            birth_date=birth_date,
            chat_id=message.chat.id
        )
        bot.send_message(message.chat.id, f'✅ Accepted: {name}, {birth_date}')
    else:
        msg = bot.send_message(message.chat.id,
            '❌ Invalid format!\nExample:\nJohn Smith\n01.01.2000')
        bot.register_next_step_handler(msg, process_birthday_input_en)

def birthday_checker():
    while True:
        now = datetime.datetime.now()
        today = now.strftime("%d.%m")
        try:
            with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"users": []}

        for user in data["users"]:
            birthdate_str = user["birth_date"]
            if birthdate_str[:5] == today:
                for chat_id in user["chats"]:
                    try:
                        username = user.get("username")
                        if username:
                            mention = f"@{username}"
                        else:
                            mention = f"[{user['name']}](tg://user?id={user['user_id']})"

                        bot.send_message(
                            chat_id,
                            f'🎉 Сегодня день рождения у {mention}! Поздравляем! 🥳',
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        print(f"Ошибка отправки в чат {chat_id}: {e}")
        time.sleep(86400)

t = threading.Thread(target=birthday_checker)
t.daemon = True
t.start()

bot.polling(none_stop=True, interval=0)
