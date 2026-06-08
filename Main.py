import random
import json
import os
import time
import logging
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== ТОКЕН ==========
BOT_TOKEN = "8512686337:AAGEJpIRU-rUFbSofacjR-6X3UrC9GXBGPg"

# ========== КОНФИГ ==========
ADMIN_ID = 8039111975
SUPPORT = "@aztec_bet_support"
CASINO_NAME = "AZTEC BET"
TON_WALLET = "UQCvOIAt2X1PHfquND-LxzVYg0Gl3a_IExORwwPjowI3Nkb8"
MIN_BET = Decimal('0.1')
MIN_DEPOSIT = Decimal('1')
MIN_WITHDRAW = Decimal('1')
REFERRAL_REGISTER_BONUS = Decimal('0.1')
REFERRAL_DEPOSIT_PERCENT = Decimal('0.05')

# ========== ЛОГИ ==========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ДАННЫЕ ==========
users = {}
withdraw_requests = {}
DATA_FILE = "aztec_bet_data.json"
REQUESTS_FILE = "aztec_bet_requests.json"

def round_ton(amount):
    return float(Decimal(str(amount)).quantize(Decimal('0.0001'), rounding=ROUND_DOWN))

def load_data():
    global users, withdraw_requests
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                users = json.load(f)
                for uid in users:
                    users[uid]['balance'] = float(users[uid].get('balance', 0))
                    users[uid]['total_bet'] = float(users[uid].get('total_bet', 0))
                    users[uid]['total_win'] = float(users[uid].get('total_win', 0))
                    users[uid]['lang'] = users[uid].get('lang', 'ru')
        if os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "r") as f:
                withdraw_requests = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(users, f, indent=2)
        with open(REQUESTS_FILE, "w") as f:
            json.dump(withdraw_requests, f, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")

load_data()

# ========== ПЕРЕВОДЫ ==========
TEXTS = {
    'ru': {
        'welcome': "🎰 ДОБРО ПОЖАЛОВАТЬ В {} 🎰\n\nПРИВЕТ, {}!\n💰 БАЛАНС: {} TON",
        'balance': "💰 БАЛАНС: {} TON",
        'stats': "📊 СТАТИСТИКА\n\nСТАВОК: {}\nПОСТАВЛЕНО: {} TON\nВЫИГРАНО: {} TON",
        'deposit': "💎 ПОПОЛНЕНИЕ\n\nКОШЕЛЁК: {}\nМИНИМУМ: {} TON\nВ КОММЕНТАРИИ ВАШ ID: {}",
        'withdraw': "💸 ВЫВОД\n\n/withdraw [СУММА] [АДРЕС]",
        'support': "📞 ПОДДЕРЖКА: {}",
        'referral': "🤝 РЕФЕРАЛЫ\n\nПРИГЛАШЁННЫХ: {}\nЗАРАБОТАНО: {} TON\n\nССЫЛКА: t.me/{}?start={}",
        'min_bet_error': "❌ МИНИМУМ {} TON",
        'no_money': "❌ НЕДОСТАТОЧНО СРЕДСТВ",
        'win': "🎉 ПОБЕДА! +{} TON",
        'lose': "😢 ПРОИГРЫШ! -{} TON",
        'draw': "😐 НИЧЬЯ",
        'choose_bet': "ВЫБЕРИТЕ СТАВКУ:",
        'choose_side': "ВЫБЕРИТЕ СТОРОНУ:",
        'choose_number': "ВЫБЕРИТЕ ЧИСЛО (1-10):",
        'choose_sum': "ВЫБЕРИТЕ СУММУ (2-12):",
        'choose_choice': "ВЫБЕРИТЕ:",
        'enter_custom_bet': "💎 ВВЕДИТЕ СУММУ СТАВКИ (минимум 0.1 TON):",
        'coin': "🪙 МОНЕТКА (x2)",
        'number': "🔢 УГАДАЙ ЧИСЛО (x3)",
        'dice_sum': "🎲 КОСТИ (СУММА) (x3)",
        'dice_over': "🎲 КОСТИ (БОЛЬШЕ/МЕНЬШЕ 7) (x2)",
        'dice_even': "🎲 КОСТИ (ЧЁТ/НЕЧЕТ) (x2)",
        'slot': "🎰 СЛОТЫ",
        'roulette': "🎡 РУЛЕТКА",
        'rps': "✂️ КАМЕНЬ-НОЖНИЦЫ-БУМАГА (x2)",
        'back': "⬅️ Назад",
        'games': "🎮 ИГРЫ",
        'demo': "🎮 ДЕМО-РЕЖИМ",
        'heads': "🪨 ОРЕЛ",
        'tails': "📄 РЕШКА",
        'rock': "🪨 КАМЕНЬ",
        'scissors': "✂️ НОЖНИЦЫ",
        'paper': "📄 БУМАГА",
        'red': "🔴 КРАСНОЕ (x2)",
        'black': "⚫ ЧЁРНОЕ (x2)",
        'number_bet': "🔢 ЧИСЛО (x36)",
        'slot_result': "🎰 СЛОТЫ\n\n{} {} {}\n{}",
        'roulette_result': "🎡 РУЛЕТКА\n\nВЫПАЛО: {}\n{}",
        'rps_result': "✂️ КНБ\n\nВЫ: {}  БОТ: {}\n{}",
        'dice_result': "🎲 КОСТИ\n\n{} + {} = {}\n{}",
    },
    'en': {
        'welcome': "🎰 WELCOME TO {} 🎰\n\nHELLO, {}!\n💰 BALANCE: {} TON",
        'balance': "💰 BALANCE: {} TON",
        'stats': "📊 STATISTICS\n\nBETS: {}\nBETTED: {} TON\nWON: {} TON",
        'deposit': "💎 DEPOSIT\n\nWALLET: {}\nMINIMUM: {} TON\nIN COMMENT YOUR ID: {}",
        'withdraw': "💸 WITHDRAW\n\n/withdraw [AMOUNT] [ADDRESS]",
        'support': "📞 SUPPORT: {}",
        'referral': "🤝 REFERRALS\n\nREFERRALS: {}\nEARNED: {} TON\n\nLINK: t.me/{}?start={}",
        'min_bet_error': "❌ MINIMUM {} TON",
        'no_money': "❌ INSUFFICIENT FUNDS",
        'win': "🎉 WIN! +{} TON",
        'lose': "😢 LOSS! -{} TON",
        'draw': "😐 DRAW",
        'choose_bet': "CHOOSE BET:",
        'choose_side': "CHOOSE SIDE:",
        'choose_number': "CHOOSE NUMBER (1-10):",
        'choose_sum': "CHOOSE SUM (2-12):",
        'choose_choice': "CHOOSE:",
        'enter_custom_bet': "💎 ENTER BET AMOUNT (minimum 0.1 TON):",
        'coin': "🪙 COIN FLIP (x2)",
        'number': "🔢 GUESS NUMBER (x3)",
        'dice_sum': "🎲 DICE (SUM) (x3)",
        'dice_over': "🎲 DICE (OVER/UNDER 7) (x2)",
        'dice_even': "🎲 DICE (EVEN/ODD) (x2)",
        'slot': "🎰 SLOTS",
        'roulette': "🎡 ROULETTE",
        'rps': "✂️ ROCK-PAPER-SCISSORS (x2)",
        'back': "⬅️ Back",
        'games': "🎮 GAMES",
        'demo': "🎮 DEMO MODE",
        'heads': "🪨 HEADS",
        'tails': "📄 TAILS",
        'rock': "🪨 ROCK",
        'scissors': "✂️ SCISSORS",
        'paper': "📄 PAPER",
        'red': "🔴 RED (x2)",
        'black': "⚫ BLACK (x2)",
        'number_bet': "🔢 NUMBER (x36)",
        'slot_result': "🎰 SLOTS\n\n{} {} {}\n{}",
        'roulette_result': "🎡 ROULETTE\n\nRESULT: {}\n{}",
        'rps_result': "✂️ RPS\n\nYOU: {}  BOT: {}\n{}",
        'dice_result': "🎲 DICE\n\n{} + {} = {}\n{}",
    }
}

def get_text(uid, key, *args):
    lang = users.get(uid, {}).get('lang', 'ru')
    text = TEXTS.get(lang, TEXTS['ru']).get(key, key)
    if args:
        return text.format(*args)
    return text

# ========== КНОПКИ СТАВОК ==========
def get_bet_buttons(uid):
    return [
        [InlineKeyboardButton("0.1 TON", callback_data="bet_0.1")],
        [InlineKeyboardButton("1 TON", callback_data="bet_1")],
        [InlineKeyboardButton("5 TON", callback_data="bet_5")],
        [InlineKeyboardButton("10 TON", callback_data="bet_10")],
        [InlineKeyboardButton(get_text(uid, 'enter_custom_bet').replace("💎 ВВЕДИТЕ СУММУ СТАВКИ", "✏️ ДРУГАЯ"), callback_data="bet_custom")],
        [InlineKeyboardButton(get_text(uid, 'back'), callback_data="back")]
    ]

def main_menu(uid):
    keyboard = [
        [InlineKeyboardButton(get_text(uid, 'balance'), callback_data="balance")],
        [InlineKeyboardButton(get_text(uid, 'stats'), callback_data="stats")],
        [InlineKeyboardButton(get_text(uid, 'deposit'), callback_data="deposit")],
        [InlineKeyboardButton(get_text(uid, 'games'), callback_data="games_menu")],
        [InlineKeyboardButton(get_text(uid, 'withdraw'), callback_data="withdraw_menu")],
        [InlineKeyboardButton(get_text(uid, 'demo'), callback_data="demo_mode")],
        [InlineKeyboardButton(get_text(uid, 'referral'), callback_data="referral")],
        [InlineKeyboardButton(get_text(uid, 'support'), callback_data="support")],
        [InlineKeyboardButton("🌐 English / Русский", callback_data="change_lang")]
    ]
    return InlineKeyboardMarkup(keyboard)

def games_menu(uid):
    keyboard = [
        [InlineKeyboardButton(get_text(uid, 'coin'), callback_data="game_coin")],
        [InlineKeyboardButton(get_text(uid, 'number'), callback_data="game_number")],
        [InlineKeyboardButton(get_text(uid, 'dice_sum'), callback_data="game_dice_sum")],
        [InlineKeyboardButton(get_text(uid, 'dice_over'), callback_data="game_dice_over")],
        [InlineKeyboardButton(get_text(uid, 'dice_even'), callback_data="game_dice_even")],
        [InlineKeyboardButton(get_text(uid, 'slot'), callback_data="game_slot")],
        [InlineKeyboardButton(get_text(uid, 'roulette'), callback_data="game_roulette")],
        [InlineKeyboardButton(get_text(uid, 'rps'), callback_data="game_rps")],
        [InlineKeyboardButton(get_text(uid, 'back'), callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def demo_menu(uid):
    keyboard = [
        [InlineKeyboardButton(get_text(uid, 'coin'), callback_data="demo_coin")],
        [InlineKeyboardButton(get_text(uid, 'number'), callback_data="demo_number")],
        [InlineKeyboardButton(get_text(uid, 'dice_sum'), callback_data="demo_dice_sum")],
        [InlineKeyboardButton(get_text(uid, 'dice_over'), callback_data="demo_dice_over")],
        [InlineKeyboardButton(get_text(uid, 'dice_even'), callback_data="demo_dice_even")],
        [InlineKeyboardButton(get_text(uid, 'back'), callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        uid = str(query.from_user.id)
        message = query.message
    else:
        uid = str(update.effective_user.id)
        message = update.message
    
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    await message.reply_text("🌐 ВЫБЕРИТЕ ЯЗЫК / CHOOSE LANGUAGE:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    lang = query.data.split("_")[1]
    await ensure_user_exists(uid)
    users[uid]['lang'] = lang
    save_data()
    
    await query.message.edit_text(
        get_text(uid, 'welcome', CASINO_NAME, query.from_user.first_name or "Player", round_ton(users[uid]['balance'])),
        reply_markup=main_menu(uid)
    )

async def ensure_user_exists(uid):
    if uid not in users:
        users[uid] = {"balance": 0, "total_bet": 0, "total_win": 0, "spins": 0, "referrer": None, "referrals": [], "total_ref_earnings": 0, "total_deposit": 0, "lang": "ru"}
        save_data()

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name or "Player"
    ref = context.args[0] if context.args else None
    await ensure_user_exists(uid)
    
    if ref and ref != uid and ref in users and not users[uid].get("referrer"):
        users[uid]["referrer"] = ref
        users[ref]["referrals"] = users[ref].get("referrals", []) + [uid]
        users[uid]["balance"] += float(REFERRAL_REGISTER_BONUS)
        save_data()
        await update.message.reply_text(f"🎉 +{REFERRAL_REGISTER_BONUS} TON")
    
    if users[uid].get('lang'):
        await update.message.reply_text(
            get_text(uid, 'welcome', CASINO_NAME, name, round_ton(users[uid]['balance'])),
            reply_markup=main_menu(uid)
        )
    else:
        await lang_choice(update, context)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await update.message.reply_text(get_text(uid, 'balance', round_ton(users[uid]['balance'])), reply_markup=main_menu(uid))

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await update.message.reply_text(
        get_text(uid, 'stats', users[uid]['spins'], round_ton(users[uid]['total_bet']), round_ton(users[uid]['total_win'])),
        reply_markup=main_menu(uid)
    )

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await update.message.reply_text(
        get_text(uid, 'deposit', TON_WALLET, MIN_DEPOSIT, uid),
        reply_markup=main_menu(uid)
    )

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await update.message.reply_text(get_text(uid, 'support', SUPPORT), reply_markup=main_menu(uid))

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    bot = (await context.bot.get_me()).username
    await update.message.reply_text(
        get_text(uid, 'referral', len(users[uid].get('referrals', [])), round_ton(users[uid].get('total_ref_earnings', 0)), bot, uid),
        reply_markup=main_menu(uid)
    )

# ========== ОБРАБОТКА СТАВОК ==========
BET_BUTTONS_LIST = [
    ("bet_0.1", 0.1),
    ("bet_1", 1),
    ("bet_5", 5),
    ("bet_10", 10),
]

async def handle_bet_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    data = query.data
    
    for cb, value in BET_BUTTONS_LIST:
        if data == cb:
            context.user_data['bet_amount'] = value
            await process_game_after_bet(update, context, query, value)
            return
    
    if data == "bet_custom":
        context.user_data['awaiting_custom_bet'] = True
        await query.message.edit_text(get_text(uid, 'enter_custom_bet'), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(uid, 'back'), callback_data="back")]]))

async def process_game_after_bet(update, update_context, query, bet):
    uid = str(query.from_user.id)
    game = update_context.user_data.get('current_game')
    
    if bet < float(MIN_BET):
        await query.message.edit_text(get_text(uid, 'min_bet_error', MIN_BET), reply_markup=games_menu(uid))
        return
    if users[uid]["balance"] < bet:
        await query.message.edit_text(get_text(uid, 'no_money'), reply_markup=games_menu(uid))
        return
    
    update_context.user_data['bet_amount'] = bet
    
    if game == 'coin':
        keyboard = [
            [InlineKeyboardButton(get_text(uid, 'heads'), callback_data="coin_heads")],
            [InlineKeyboardButton(get_text(uid, 'tails'), callback_data="coin_tails")],
            [InlineKeyboardButton(get_text(uid, 'back'), callback_data="games_menu")]
        ]
        await query.message.edit_text(f"{get_text(uid, 'coin')}\n\n{get_text(uid, 'choose_side')}", reply_markup=InlineKeyboardMarkup(keyboard))
    elif game == 'number':
        keyboard = []
        row = []
        for i in range(1, 11):
            row.append(InlineKeyboardButton(str(i), callback_data=f"num_{i}"))
            if len(row) == 5:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(get_text(uid, 'back'), callback_data="games_menu")])
        await query.message.edit_text(f"{get_text(uid, 'number')}\n\n{get_text(uid, 'choose_number')}", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_custom_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    try:
        bet = float(update.message.text)
        if bet <= 0:
            raise ValueError
    except:
        await update.message.reply_text(get_text(uid, 'min_bet_error', MIN_BET))
        return
    
    context.user_data['bet_amount'] = bet
    game = context.user_data.get('current_game')
    
    if bet < float(MIN_BET):
        await update.message.reply_text(get_text(uid, 'min_bet_error', MIN_BET))
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(get_text(uid, 'no_money'))
        return
    
    if game == 'coin':
        keyboard = [
            [InlineKeyboardButton(get_text(uid, 'heads'), callback_data="coin_heads")],
            [InlineKeyboardButton(get_text(uid, 'tails'), callback_data="coin_tails")],
            [InlineKeyboardButton(get_text(uid, 'back'), callback_data="games_menu")]
        ]
        await update.message.reply_text(f"{get_text(uid, 'coin')}\n\n{get_text(uid, 'choose_side')}", reply_markup=InlineKeyboardMarkup(keyboard))
    elif game == 'number':
        keyboard = []
        row = []
        for i in range(1, 11):
            row.append(InlineKeyboardButton(str(i), callback_data=f"num_{i}"))
            if len(row) == 5:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(get_text(uid, 'back'), callback_data="games_menu")])
        await update.message.reply_text(f"{get_text(uid, 'number')}\n\n{get_text(uid, 'choose_number')}", reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data['awaiting_custom_bet'] = False

async def coin_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    choice = "орел" if "heads" in query.data else "решка"
    bet = context.user_data.get('bet_amount', 0)
    
    result = random.choice(["орел", "решка"])
    if choice == result:
        win = bet * 2
        msg = get_text(uid, 'win', round_ton(win))
    else:
        win = -bet
        msg = get_text(uid, 'lose', round_ton(bet))
    
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    
    await query.message.edit_text(
        f"🪙 {get_text(uid, 'coin')}\n\n{get_text(uid, 'choose_side')}\n\nВАШ ВЫБОР: {choice}\nВЫПАЛО: {result}\n{msg}\n\n💰 {get_text(uid, 'balance', round_ton(users[uid]['balance']))}",
        reply_markup=main_menu(uid)
    )

async def number_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    guess = int(query.data.split("_")[1])
    bet = context.user_data.get('bet_amount', 0)
    
    number = random.randint(1, 10)
    if guess == number:
        win = bet * 3
        msg = get_text(uid, 'win', round_ton(win))
    else:
        win = -bet
        msg = get_text(uid, 'lose', round_ton(bet))
    
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    
    await query.message.edit_text(
        f"🔢 {get_text(uid, 'number')}\n\nВАШЕ ЧИСЛО: {guess}\nВЫПАЛО: {number}\n{msg}\n\n💰 {get_text(uid, 'balance', round_ton(users[uid]['balance']))}",
        reply_markup=main_menu(uid)
    )

# ========== ИГРЫ МЕНЮ ==========
async def game_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    context.user_data['current_game'] = 'coin'
    await query.message.edit_text(get_text(uid, 'coin'), reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))

async def game_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    context.user_data['current_game'] = 'number'
    await query.message.edit_text(get_text(uid, 'number'), reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))

async def game_dice_sum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    context.user_data['current_game'] = 'dice_sum'
    await query.message.edit_text(get_text(uid, 'dice_sum'), reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))

async def game_dice_over(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    context.user_data['current_game'] = 'dice_over'
    await query.message.edit_text(get_text(uid, 'dice_over'), reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))

async def game_dice_even(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    context.user_data['current_game'] = 'dice_even'
    await query.message.edit_text(get_text(uid, 'dice_even'), reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))

async def game_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    context.user_data['current_game'] = 'slot'
    await query.message.edit_text(get_text(uid, 'slot'), reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))

async def game_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    context.user_data['current_game'] = 'roulette'
    keyboard = [
        [InlineKeyboardButton(get_text(uid, 'red'), callback_data="roulette_red")],
        [InlineKeyboardButton(get_text(uid, 'black'), callback_data="roulette_black")],
        [InlineKeyboardButton(get_text(uid, 'number_bet'), callback_data="roulette_number")],
        [InlineKeyboardButton(get_text(uid, 'back'), callback_data="games_menu")]
    ]
    await query.message.edit_text(get_text(uid, 'roulette'), reply_markup=InlineKeyboardMarkup(keyboard))

async def game_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    context.user_data['current_game'] = 'rps'
    await query.message.edit_text(get_text(uid, 'rps'), reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))

# ========== ОСТАЛЬНЫЕ ИГРЫ (КОРОТКО) ==========
async def roulette_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    bet_type = query.data.split("_")[1]
    
    if bet_type in ["red", "black"]:
        context.user_data['roulette_type'] = bet_type
        await query.message.edit_text(f"{get_text(uid, 'roulette')}\n\n{get_text(uid, 'choose_bet')}", reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))
    else:
        context.user_data['roulette_type'] = 'number'
        await query.message.edit_text(f"{get_text(uid, 'roulette')}\n\n{get_text(uid, 'choose_number')}", reply_markup=InlineKeyboardMarkup(get_bet_buttons(uid)))

# ========== CALLBACK ==========
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "change_lang":
        await lang_choice(update, context)
        return
    elif data.startswith("lang_"):
        await set_language(update, context)
        return
    elif data.startswith("bet_"):
        await handle_bet_selection(update, context)
        return
    elif data.startswith("coin_"):
        await coin_choice(update, context)
        return
    elif data.startswith("num_"):
        await number_choice(update, context)
        return
    elif data.startswith("roulette_"):
        await roulette_choice(update, context)
        return
    elif data == "back":
        uid = str(query.from_user.id)
        await query.message.edit_text(get_text(uid, 'games'), reply_markup=games_menu(uid))
        return
    elif data == "games_menu":
        uid = str(query.from_user.id)
        await query.message.edit_text(get_text(uid, 'games'), reply_markup=games_menu(uid))
        return
    elif data == "demo_mode":
        uid = str(query.from_user.id)
        await query.message.edit_text(get_text(uid, 'demo'), reply_markup=demo_menu(uid))
        return
    elif data == "balance":
        await balance(update, context)
    elif data == "stats":
        await stats(update, context)
    elif data == "deposit":
        await deposit(update, context)
    elif data == "withdraw_menu":
        uid = str(query.from_user.id)
        await query.message.edit_text(get_text(uid, 'withdraw'), reply_markup=main_menu(uid))
    elif data == "support":
        await support(update, context)
    elif data == "referral":
        await referral(update, context)
    elif data == "game_coin":
        await game_coin(update, context)
    elif data == "game_number":
        await game_number(update, context)
    elif data == "game_dice_sum":
        await game_dice_sum(update, context)
    elif data == "game_dice_over":
        await game_dice_over(update, context)
    elif data == "game_dice_even":
        await game_dice_even(update, context)
    elif data == "game_slot":
        await game_slot(update, context)
    elif data == "game_roulette":
        await game_roulette(update, context)
    elif data == "game_rps":
        await game_rps(update, context)
    elif data.startswith("demo_"):
        await query.message.edit_text("🎮 ДЕМО-РЕЖИМ\n\n/help", reply_markup=demo_menu(str(query.from_user.id)))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_custom_bet'):
        await handle_custom_bet(update, context)

# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("ref", referral))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(CommandHandler("withdraw", lambda u, c: None))
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c: None))
    app.add_handler(CommandHandler("decline", lambda u, c: None))
    app.add_handler(CommandHandler("requests", lambda u, c: None))
    
    app.add_handler(CommandHandler("slot", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_color", lambda u, c: None))
    app.add_handler(CommandHandler("roulette_number", lambda u, c: None))
    app.add_handler(CommandHandler("rps", lambda u, c: None))
    app.add_handler(CommandHandler("coin", lambda u, c: None))
    app.add_handler(CommandHandler("number", lambda u, c: None))
    app.add_handler(CommandHandler("dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("demo_coin", lambda u, c: None))
    app.add_handler(CommandHandler("demo_number", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_sum", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_over", lambda u, c: None))
    app.add_handler(CommandHandler("demo_dice_even", lambda u, c: None))
    app.add_handler(CommandHandler("help", lambda u, c: None))
    
    app.add_handler(CommandHandler("add_deposit", lambda u, c: None))
    app.add_handler(CommandHandler("approve", lambda u, c
