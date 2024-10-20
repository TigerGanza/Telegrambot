import logging
import requests
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import nest_asyncio

# Applica nest_asyncio
nest_asyncio.apply()

# Configurazione del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Imposta l'ID del canale Telegram qui
CHANNEL_ID = -1002496509220  # Sostituisci con l'ID numerico del tuo canale

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ciao! Inviami un link di Amazon per estrarre informazioni!")

async def handle_message(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    link = update.message.text

    # Estrai le informazioni dal link di Amazon
    product_details = extract_amazon_product_details(link)

    # Crea il messaggio da inviare
    product_message = format_product_message(product_details, link)

    # Invia l'immagine e il messaggio all'utente
    if product_details.get("Immagine"):
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=product_details["Immagine"], caption=product_message, parse_mode='Markdown', reply_markup=create_button(link))
    else:
        await update.message.reply_text(product_message, parse_mode='Markdown', reply_markup=create_button(link))

    # Invia l'immagine e il messaggio al canale
    if product_details.get("Immagine"):
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=product_details["Immagine"], caption=product_message, parse_mode='Markdown', reply_markup=create_button(link))
    else:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=product_message, parse_mode='Markdown', reply_markup=create_button(link))

def extract_amazon_product_details(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"Titolo": "Errore nel recupero del prodotto", "Prezzo": "🚫 Errore", "Sconto": "🚫 Errore"}

    # Stampa il contenuto HTML per il debug
    html_content = response.content.decode('utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')

    title_element = soup.find("span", id="productTitle")
    title = title_element.get_text(strip=True) if title_element else "❌ Nome del prodotto non trovato"

    # Estrai il prezzo - più opzioni di ricerca
    price = "💲 Prezzo non trovato"
    
    # Prova con più classi e formati di prezzo
    price_element = soup.find("span", class_="a-price-whole")  # Prezzo principale
    if price_element:
        price_fraction = soup.find("span", class_="a-price-fraction")
        if price_fraction:
            price = f"💲 {price_element.get_text(strip=True)},{price_fraction.get_text(strip=True)} €"
        else:
            price = f"💲 {price_element.get_text(strip=True)} €"

    # Cerca anche in altre classi comuni
    if price == "💲 Prezzo non trovato":
        alternative_price_element = soup.find("span", class_="priceBlockBuyingPriceString")
        if alternative_price_element:
            price = f"💲 {alternative_price_element.get_text(strip=True)}"

    discount_element = soup.find("span", class_="a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage")
    discount = discount_element.get_text(strip=True) if discount_element else "🚫 Sconto non trovato"

    # Estrai l'immagine del prodotto
    image_element = soup.find("img", id="landingImage")
    image_url = image_element['src'] if image_element else None

    return {
        "Titolo": title,
        "Prezzo": price,
        "Sconto": discount,
        "Immagine": image_url
    }

def format_product_message(product_details, link):
    titolo = product_details.get("Titolo", "❌ Nome del prodotto non trovato")
    prezzo = product_details.get("Prezzo", "💲 Prezzo non trovato")
    sconto = product_details.get("Sconto", "🚫 Sconto non trovato")

    message = (
        f"🛒 *{titolo}*\n"
        f"💰 *Prezzo*: {prezzo}\n"
        f"🔻 *Sconto*: {sconto}\n"
        f"👉 Affrettati, offerta da non perdere! 🚀\n"
        f"🔔🔈 Attiva le Notifiche! 🔔🔈\n\n"
        f"👇 *Guarda l’offerta* 👇\n"
        f"{link}"  # Aggiungi il link qui sotto la frase
    )
    return message

def create_button(link):
    """Crea una tastiera inline con un pulsante 'Apri in Amazon'."""
    keyboard = [[InlineKeyboardButton("🔥 Apri l'offerta su Amazon! 🔥", url=link)]]
    return InlineKeyboardMarkup(keyboard)

async def main() -> None:
    # Sostituisci 'YOUR_BOT_TOKEN' con il tuo token reale
    application = ApplicationBuilder().token("7680073196:AAFTjH_GWJaQFYbxcx2E7azqP9hPRzDx9r4").build()  # Inserisci il tuo token qui
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Esegui il bot con run_polling
    await application.run_polling()

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except Exception as e:
        print(f"Si è verificato un errore: {e}")

