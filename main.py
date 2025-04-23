import telebot
from PIL import Image
from io import BytesIO
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

API_TOKEN = 'your_bot_token'
bot = telebot.TeleBot(API_TOKEN, parse_mode="HTML")
WEBHOOK_HOST = "https://your_domain:8443"
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    yield
    bot.remove_webhook()

app = FastAPI(lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    json_data = await request.json()
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return {"status": "ok"}

# Обработчик изображений, отправленных в виде файла (документа)
@bot.message_handler(content_types=['document'])
def handle_document(message):
    # Проверяем, что файл является изображением
    if message.document.mime_type.startswith('image/'):
        # Скачиваем файл
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Загружаем изображение с помощью Pillow
        image = Image.open(BytesIO(downloaded_file))

        # Преобразуем изображение до размера 512x512 и сохраняем в формате PNG
        image = image.resize((512, 512), Image.LANCZOS)
        output = BytesIO()
        output.name = 'resized_image.png'
        image.save(output, format='PNG')
        output.seek(0)

        # Отправляем обратно в виде файла
        bot.send_document(message.chat.id, output)
    else:
        bot.reply_to(message, "Пожалуйста, отправьте изображение файлом (без сжатия).")

# Обработчик изображений, отправленных в виде фотографии
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_id = message.photo[-1].file_id  # выбираем фото с наивысшим разрешением
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Загружаем изображение с помощью Pillow
    image = Image.open(BytesIO(downloaded_file))

    # Преобразуем изображение до размера 512x512 и сохраняем в формате PNG
    image = image.resize((512, 512), Image.LANCZOS)
    output = BytesIO()
    output.name = 'resized_image.png'
    image.save(output, format='PNG')
    output.seek(0)

    # Отправляем обратно в виде файла
    bot.send_document(message.chat.id, output)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Это бот для быстрой конвертации изображения для бота @Stickers. Отправь мне изображение (с сжатием/без) и я пришлю изображение в формате png размером 512x512 пикселей. Эту картинку можно переслать боту @Stickers для создания стикера.")

@bot.message_handler(commands=['ping'])
def ping(message):
    bot.send_message(message.chat.id, "Pong!")

if __name__ == "__main__":
    import uvicorn
    from sdnotify import SystemdNotifier
    notifier = SystemdNotifier()
    notifier.notify('READY=1')
    uvicorn.run(app, host="0.0.0.0", port=8443, ssl_keyfile="path_to_privkey", ssl_certfile="path_to_fullchain")
