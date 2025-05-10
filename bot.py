
import logging
import requests
import easyocr
import certifi
import urllib3
import warnings
from PIL import Image
from io import BytesIO
import re
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning)

reader = easyocr.Reader(['en'], gpu=False)

TELEGRAM_TOKEN = '7995484683:AAFGHDWAiR13DhTr_Eh6LQ8eF_-YzdySO7k'
CIDMS_API_KEY = 'RZ6yFCBmF3DP2jeDNt8VByoW4ItOjlFk'
CIDMS_API_URL = 'https://storekey247.com/api/partner/check-cidms/'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def extract_installation_id(image: Image.Image) -> str | None:
    image = image.convert("RGB")
    np_image = np.array(image)
    results = reader.readtext(np_image)
    text = "\n".join([item[1] for item in results])

    with open("ocr_log.txt", "w", encoding="utf-8") as f:
        f.write(text)

    matches = re.findall(r'\d{6,}', text)
    if len(matches) >= 9:
        return ''.join(matches[:9])
    elif len(matches) >= 1:
        return ''.join(matches)
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Send your Installation ID or a screenshot and I'll return the CID.")

async def get_cid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    iid = update.message.text.strip()
    await process_installation_id(iid, update)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    file = await photo.download_as_bytearray()
    image = Image.open(BytesIO(file))
    image.save("processed_image.png")
    iid = extract_installation_id(image)
    if iid:
        await update.message.reply_text("🧾 Installation ID extracted. Retrieving CID...")
        await process_installation_id(iid, update)
    else:
        await update.message.reply_text("❌ Could not detect Installation ID in the image.")

async def process_installation_id(iid: str, update: Update):
    url = f"{CIDMS_API_URL}{iid}?api_key={CIDMS_API_KEY}"
    try:
        response = requests.get(url, verify=False)
        data = response.json()
        if data.get("status") == "success" and data.get("data", {}).get("have_cid") == 1:
            cid = data["data"]["confirmationid"]
            await update.message.reply_text(f"✅ Confirmation ID:\n{cid}")
        elif data.get("status") == "pending":
            await update.message.reply_text("⏳ Your request is being processed. Try again in a few seconds.")
        else:
            await update.message.reply_text(f"❌ Error: {data.get('message', 'Unknown error occurred')}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error occurred: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_cid))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == '__main__':
    main()
