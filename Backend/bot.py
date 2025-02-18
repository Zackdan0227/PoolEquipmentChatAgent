from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import requests
from config import BOT_TOKEN, QUERY_API_URL
from agent_manager import AgentManager

agent = AgentManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to the Pool Equipment Search Bot!\n\n"
        "Simply send me any query about pool equipment, "
        "and I'll help you find relevant information."
    )
    await update.message.reply_text(welcome_message)

async def search_equipment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages and search for pool equipment."""
    query = update.message.text
    user = update.effective_user
    print(f"\n👤 User {user.id} ({user.first_name}) sent: '{query}'")
    
    # Send typing indicator
    await update.message.chat.send_action("typing")
    print("💭 Bot is typing...")
    
    # Process query through agent manager
    reply_message = await agent.process_query(query)
    print(f"🤖 Bot response: {reply_message}...")  # First 200 chars
    
    await update.message.reply_text(reply_message, parse_mode='Markdown')

def format_results(results):
    """Format search results for Telegram."""
    if not results:
        return "No results found for your query."

    message = "*🔍 Search Results:*\n"
    for item in results[:5]:  # Show top 5 results
        message += f"🔹 *{item['name']}*\n"
        message += f"🔗 [View Item]({item['url']})\n\n"

    return message

if __name__ == "__main__":
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_equipment))
    
    print("🤖 Starting Telegram bot...")
    application.run_polling()