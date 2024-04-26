from telebot import TeleBot, types
from requests import get
import json
import pytz
import datetime

bot = TeleBot('Your_api_key')
global initial_message, latitude, longitude, time_zone, location_message, error_message
timezones = {"msk": "Europe/Moscow", "pdg": "Europe/Podgorica", "chl": "Asia/Yekaterinburg"}
cities = {"msk": "Москве", "pdg": "Подгорице", "chl": "Челябинске"}

tz_api_https = "https://api.geotimezone.com/public/timezone"

keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
keyboard1 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
button = types.KeyboardButton(text="Поделиться локацией", request_location=True)
button1 = types.KeyboardButton(text="Перевести новое время", request_location=True)
keyboard.add(button)
keyboard1.add(button1)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global initial_message, keyboard, location_message
    # Create an inline keyboard

    location_message = bot.send_message(message.chat.id, "Пожалуйста, поделитесь своей локацией:", reply_markup=keyboard)


@bot.message_handler(content_types=['location'])
def handle_location(message):
    global initial_message, latitude, longitude, location_message
    latitude = message.location.latitude
    longitude = message.location.longitude
    inline_keyboard = types.InlineKeyboardMarkup()
    # Add a button to the keyboard
    inline_keyboard.add(types.InlineKeyboardButton(text="Подгорице", callback_data="pdg"))

    inline_keyboard.add(types.InlineKeyboardButton(text="Москве", callback_data="msk"))

    inline_keyboard.add(types.InlineKeyboardButton(text="Челябинске", callback_data="chl"))
    initial_message = bot.send_message(message.from_user.id, "Событие произойдёт в:",
                                       reply_markup=inline_keyboard)
    try:
        bot.delete_message(message.chat.id, location_message.message_id)
    except:
        pass
    finally:
        bot.delete_message(message.chat.id, message.message_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global initial_message, time_zone
    time_zone = call.data
    try:
        error_message = ""
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=initial_message.message_id,
                          text=f"Во сколько это будет в {cities[time_zone]}?\n(например 16:35)", reply_markup=None)
        bot.register_next_step_handler(call.message, send_time, time_zone)
    except:
        pass

def send_time(message, time_zone):
    global latitude, longitude, keyboard, error_message
    response = get(tz_api_https+f"?latitude={latitude}&longitude={longitude}").text
    json_data = json.loads(response)
    try:
        bot.delete_message(message.chat.id, error_message.message_id)
    except:
        pass
    try:
        input_time = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, int(message.text.split(":")[0]), int(message.text.split(":")[1]), 0)
        input_timezone = pytz.timezone(timezones[time_zone])
        output_timezone = pytz.timezone(json_data["iana_timezone"])
        input_times = input_timezone.localize(input_time)
        output_time = input_times.astimezone(output_timezone)
        if output_time.date() < datetime.datetime.now().date():
            bot.send_message(message.from_user.id, f'В вашем часовом поясе будет {output_time.strftime("%H:%M")} предыдущего дня', reply_markup=keyboard1)
        elif output_time.date() > datetime.datetime.now().date():
            bot.send_message(message.from_user.id, f'В вашем часовом поясе будет {output_time.strftime("%H:%M")} следующего дня', reply_markup=keyboard1)
        else:
            bot.send_message(message.from_user.id, f'В вашем часовом поясе будет {output_time.strftime("%H:%M")} того-же дня', reply_markup=keyboard1)
    except:
        error_message = bot.send_message(message.from_user.id, "Неверный формат времени.\nВведите время в формате 12:30")
        bot.delete_message(message.chat.id, message.message_id)
        bot.register_next_step_handler(message, send_time, time_zone)

bot.polling()
