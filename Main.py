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

def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("💎 Пополнить", callback_data="deposit")],
        [InlineKeyboardButton("🎰 Игры", callback_data="games_menu")],
        [InlineKeyboardButton("💸 Вывести", callback_data="withdraw_menu")],
        [InlineKeyboardButton("🎁 Демо", callback_data="demo_mode")],
        [InlineKeyboardButton("🤝 Рефералы", callback_data="referral")],
        [InlineKeyboardButton("📞 Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def games_menu():
    keyboard = [
        [InlineKeyboardButton("🪙 Монетка", callback_data="game_coin")],
        [InlineKeyboardButton("🔢 Угадай число", callback_data="game_number")],
        [InlineKeyboardButton("🎲 Кости", callback_data="game_dice")],
        [InlineKeyboardButton("🎰 Слоты", callback_data="game_slot")],
        [InlineKeyboardButton("🎡 Рулетка", callback_data="game_roulette")],
        [InlineKeyboardButton("✂️ КНБ", callback_data="game_rps")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def demo_menu():
    keyboard = [
        [InlineKeyboardButton("🪙 Монетка", callback_data="demo_coin")],
        [InlineKeyboardButton("🔢 Угадай число", callback_data="demo_number")],
        [InlineKeyboardButton("🎲 Кости", callback_data="demo_dice")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def ensure_user_exists(uid):
    if uid not in users:
        users[uid] = {"balance": 0, "total_bet": 0, "total_win": 0, "spins": 0, "referrer": None, "referrals": [], "total_ref_earnings": 0, "total_deposit": 0}
        save_data()

# ========== МОНЕТКА ==========
async def game_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🪙 МОНЕТКА\n\n/coin [СУММА] [орел/решка]", reply_markup=games_menu())

async def coin_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /coin [СУММА] [орел/решка]")
        return
    try:
        bet = float(context.args[0])
        if bet <= 0:
            await update.message.reply_text("❌ СТАВКА > 0")
            return
    except:
        await update.message.reply_text("❌ НЕВЕРНАЯ СУММА")
        return
    choice = context.args[1].lower()
    if choice not in ["орел", "решка"]:
        await update.message.reply_text("❌ орел или решка")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    result = random.choice(["орел", "решка"])
    if choice == result:
        win = bet * 2
        msg = f"🎉 ПОБЕДА! +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! -{round_ton(bet)} TON"
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🪙 МОНЕТКА\n\nРЕЗУЛЬТАТ: {result}\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

# ========== УГАДАЙ ЧИСЛО ==========
async def game_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🔢 УГАДАЙ ЧИСЛО\n\n/number [СУММА] [1-10]", reply_markup=games_menu())

async def number_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /number [СУММА] [1-10]")
        return
    try:
        bet = float(context.args[0])
        guess = int(context.args[1])
        if bet <= 0 or guess < 1 or guess > 10:
            raise ValueError
    except:
        await update.message.reply_text("❌ НЕВЕРНЫЕ ДАННЫЕ")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    number = random.randint(1, 10)
    if guess == number:
        win = bet * 3
        msg = f"🎉 ПОБЕДА! +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! -{round_ton(bet)} TON"
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🔢 УГАДАЙ ЧИСЛО\n\nВАШЕ: {guess}\nВЫПАЛО: {number}\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

# ========== КОСТИ ==========
async def game_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🎲 КОСТИ\n\n/dice_sum [СУММА] [2-12]\n/dice_over [СУММА] [больше/меньше]\n/dice_even [СУММА] [чет/нечет]", reply_markup=games_menu())

async def dice_sum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /dice_sum [СУММА] [2-12]")
        return
    try:
        bet = float(context.args[0])
        guess = int(context.args[1])
        if bet <= 0 or guess < 2 or guess > 12:
            raise ValueError
    except:
        await update.message.reply_text("❌ НЕВЕРНЫЕ ДАННЫЕ")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    if guess == total:
        win = bet * 3
        msg = f"🎉 ПОБЕДА! +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! -{round_ton(bet)} TON"
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🎲 КОСТИ\n\n{d1}+{d2}={total}\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def dice_over(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /dice_over [СУММА] [больше/меньше]")
        return
    try:
        bet = float(context.args[0])
        choice = context.args[1].lower()
        if bet <= 0 or choice not in ["больше", "меньше"]:
            raise ValueError
    except:
        await update.message.reply_text("❌ НЕВЕРНЫЕ ДАННЫЕ")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    if (choice == "больше" and total > 7) or (choice == "меньше" and total < 7):
        win = bet * 2
        msg = f"🎉 ПОБЕДА! +{round_ton(win)} TON"
    elif total == 7:
        win = 0
        msg = f"😐 НИЧЬЯ! СТАВКА ВОЗВРАЩЕНА"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! -{round_ton(bet)} TON"
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🎲 КОСТИ\n\n{d1}+{d2}={total}\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def dice_even(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /dice_even [СУММА] [чет/нечет]")
        return
    try:
        bet = float(context.args[0])
        choice = context.args[1].lower()
        if bet <= 0 or choice not in ["чет", "нечет"]:
            raise ValueError
    except:
        await update.message.reply_text("❌ НЕВЕРНЫЕ ДАННЫЕ")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    is_even = total % 2 == 0
    if (choice == "чет" and is_even) or (choice == "нечет" and not is_even):
        win = bet * 2
        msg = f"🎉 ПОБЕДА! +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! -{round_ton(bet)} TON"
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🎲 КОСТИ\n\n{d1}+{d2}={total}\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

# ========== СЛОТЫ ==========
SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍉", "💎", "7️⃣", "⭐", "🎰"]

async def game_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🎰 СЛОТЫ\n\n/slot [СУММА]", reply_markup=games_menu())

async def slot_spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 1:
        await update.message.reply_text("❌ /slot [СУММА]")
        return
    try:
        bet = float(context.args[0])
        if bet <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ НЕВЕРНАЯ СУММА")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    
    s1, s2, s3 = random.choice(SLOT_SYMBOLS), random.choice(SLOT_SYMBOLS), random.choice(SLOT_SYMBOLS)
    mult = 0
    if s1 == s2 == s3:
        if s1 in ["7️⃣", "💎", "🎰"]:
            mult = 5
        elif s1 == "🍉":
            mult = 4
        elif s1 in ["🍒", "🍋", "🍊"]:
            mult = 3
        elif s1 == "⭐":
            mult = 2
    if mult > 0:
        win = bet * mult
        msg = f"🎉 ВЫИГРЫШ +{round_ton(win)} TON (x{mult})"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ -{round_ton(bet)} TON"
    
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    
    await update.message.reply_text(f"🎰 СЛОТЫ\n\n{s1} {s2} {s3}\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

# ========== РУЛЕТКА ==========
async def game_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🎡 РУЛЕТКА\n\n/roulette_color [СУММА] [красное/черное]\n/roulette_number [СУММА] [0-36]", reply_markup=games_menu())

async def roulette_color_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /roulette_color [СУММА] [красное/черное]")
        return
    try:
        bet = float(context.args[0])
        color = context.args[1].lower()
        if bet <= 0 or color not in ["красное", "черное"]:
            raise ValueError
    except:
        await update.message.reply_text("❌ НЕВЕРНЫЕ ДАННЫЕ")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    
    red = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    black = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
    
    if random.random() < 0.33:
        if color == "красное":
            num = random.choice(red)
            win = bet * 2
            msg = f"🎉 ПОБЕДА! {num} 🔴 +{round_ton(win)} TON"
        else:
            num = random.choice(black)
            win = bet * 2
            msg = f"🎉 ПОБЕДА! {num} ⚫ +{round_ton(win)} TON"
    else:
        if random.random() < 0.1:
            num = 0
        else:
            num = random.choice(black if color == "красное" else red)
        win = -bet
        msg = f"😢 ПРОИГРЫШ! {num} -{round_ton(bet)} TON"
    
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🎡 РУЛЕТКА\n\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def roulette_number_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /roulette_number [СУММА] [0-36]")
        return
    try:
        bet = float(context.args[0])
        guess = int(context.args[1])
        if bet <= 0 or guess < 0 or guess > 36:
            raise ValueError
    except:
        await update.message.reply_text("❌ НЕВЕРНЫЕ ДАННЫЕ")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    
    num = random.randint(0, 36)
    if guess == num:
        win = bet * 36
        msg = f"🎉 ДЖЕКПОТ! {num} +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! {num} -{round_ton(bet)} TON"
    
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🎡 РУЛЕТКА\n\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

# ========== КАМЕНЬ-НОЖНИЦЫ-БУМАГА ==========
async def game_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("✂️ КАМЕНЬ-НОЖНИЦЫ-БУМАГА\n\n/rps [СУММА]", reply_markup=games_menu())

async def rps_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 1:
        await update.message.reply_text("❌ /rps [СУММА]")
        return
    try:
        bet = float(context.args[0])
        if bet <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ НЕВЕРНАЯ СУММА")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    context.user_data['rps_bet'] = bet
    keyboard = [
        [InlineKeyboardButton("🪨 КАМЕНЬ", callback_data="rps_rock")],
        [InlineKeyboardButton("✂️ НОЖНИЦЫ", callback_data="rps_scissors")],
        [InlineKeyboardButton("📄 БУМАГА", callback_data="rps_paper")],
    ]
    await update.message.reply_text(f"✅ СТАВКА {bet} TON\nВЫБЕРИТЕ:", reply_markup=InlineKeyboardMarkup(keyboard))

async def rps_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    bet = context.user_data.get('rps_bet', 0)
    if bet <= 0:
        await query.message.edit_text("❌ СНАЧАЛА /rps [СУММА]", reply_markup=games_menu())
        return
    player = query.data.split("_")[1]
    choices = {"rock": "🪨", "scissors": "✂️", "paper": "📄"}
    bot = random.choice(["rock", "scissors", "paper"])
    if player == bot:
        win = 0
        msg = "😐 НИЧЬЯ"
    elif (player == "rock" and bot == "scissors") or (player == "scissors" and bot == "paper") or (player == "paper" and bot == "rock"):
        win = bet * 2
        msg = f"🎉 ПОБЕДА +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ -{round_ton(bet)} TON"
    users[uid]["balance"] += win
    users[uid]["total_bet"] += bet
    if win > 0:
        users[uid]["total_win"] += win
    users[uid]["spins"] += 1
    save_data()
    context.user_data['rps_bet'] = 0
    await query.message.edit_text(f"✂️ КНБ\n\nВЫ: {choices[player]}  БОТ: {choices[bot]}\n{msg}\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name
    ref = context.args[0] if context.args else None
    await ensure_user_exists(uid)
    if ref and ref != uid and ref in users and not users[uid].get("referrer"):
        users[uid]["referrer"] = ref
        users[ref]["referrals"] = users[ref].get("referrals", []) + [uid]
        users[uid]["balance"] += float(REFERRAL_REGISTER_BONUS)
        save_data()
        await update.message.reply_text(f"🎉 +{REFERRAL_REGISTER_BONUS} TON ЗА РЕГИСТРАЦИЮ!")
    await update.message.reply_text(f"🎰 ДОБРО ПОЖАЛОВАТЬ {name}!\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON\n\nИГРЫ:\n/coin\n/number\n/dice_sum\n/dice_over\n/dice_even\n/slot\n/roulette_color\n/roulette_number\n/rps\n\n💎 КОШЕЛЁК: {TON_WALLET}\n📝 В КОММЕНТАРИИ ВАШ ID: {uid}", reply_markup=main_menu())

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await update.message.reply_text(f"💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await update.message.reply_text(f"📊 СТАТИСТИКА\n\nСТАВОК: {users[uid]['spins']}\nПОСТАВЛЕНО: {round_ton(users[uid]['total_bet'])} TON\nВЫИГРАНО: {round_ton(users[uid]['total_win'])} TON", reply_markup=main_menu())

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await update.message.reply_text(f"💎 ПОПОЛНЕНИЕ\n\nКОШЕЛЁК: {TON_WALLET}\nМИНИМУМ: {MIN_DEPOSIT} TON\nВ КОММЕНТАРИИ ВАШ ID: {uid}", reply_markup=main_menu())

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /withdraw [СУММА] [АДРЕС]")
        return
    try:
        amount = float(context.args[0])
        if amount <= 0 or amount < MIN_WITHDRAW:
            raise ValueError
        wallet = context.args[1]
        if not validate_ton_wallet(wallet):
            raise ValueError
    except:
        await update.message.reply_text(f"❌ МИНИМУМ {MIN_WITHDRAW} TON")
        return
    if users[uid]["balance"] < amount:
        await update.message.reply_text("❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    users[uid]["balance"] -= amount
    rid = f"{uid}_{int(time.time())}"
    withdraw_requests[rid] = {"user_id": uid, "amount": amount, "wallet": wallet, "status": "pending"}
    save_data()
    await update.message.reply_text(f"✅ ЗАЯВКА №{rid} ПРИНЯТА\n⏱ ДО 72 ЧАСОВ", reply_markup=main_menu())
    await context.bot.send_message(ADMIN_ID, f"📝 ЗАЯВКА {rid}\n👤 {uid}\n💰 {amount} TON\n✅ /approve {rid}\n❌ /decline {rid}")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📞 ПОДДЕРЖКА: {SUPPORT}", reply_markup=main_menu())

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    bot = (await context.bot.get_me()).username
    await update.message.reply_text(f"🤝 РЕФЕРАЛЫ\n\nПРИГЛАШЁННЫХ: {len(users[uid].get('referrals', []))}\nЗАРАБОТАНО: {round_ton(users[uid].get('total_ref_earnings', 0))} TON\n\nССЫЛКА: t.me/{bot}?start={uid}", reply_markup=main_menu())

async def withdraw_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("💸 ВЫВОД\n\n/withdraw [СУММА] [АДРЕС]", reply_markup=main_menu())

async def add_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ НЕТ ДОСТУПА")
        return
    if len(context.args) != 2:
        await update.message.reply_text("❌ /add_deposit [ID] [СУММА]")
        return
    uid, amount = context.args[0], float(context.args[1])
    await ensure_user_exists(uid)
    users[uid]["balance"] += amount
    users[uid]["total_deposit"] = users[uid].get("total_deposit", 0) + amount
    save_data()
    await update.message.reply_text(f"✅ +{amount} TON {uid}")
    await context.bot.send_message(uid, f"✅ ПОПОЛНЕНИЕ {amount} TON")
    ref = users[uid].get("referrer")
    if ref and ref in users:
        bonus = amount * 0.05
        users[ref]["balance"] += bonus
        users[ref]["total_ref_earnings"] = users[ref].get("total_ref_earnings", 0) + bonus
        save_data()
        await context.bot.send_message(ref, f"🎉 РЕФЕРАЛ ПОПОЛНИЛ {amount} TON\n+{bonus} TON")

async def admin_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    for rid, req in withdraw_requests.items():
        if req.get("status") == "pending":
            await update.message.reply_text(f"{rid}\n{req['user_id']}\n{req['amount']} TON\n/approve {rid}\n/decline {rid}")

async def approve_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) != 1:
        return
    rid = context.args[0]
    if rid in withdraw_requests and withdraw_requests[rid]["status"] == "pending":
        withdraw_requests[rid]["status"] = "approved"
        save_data()
        await update.message.reply_text(f"✅ {rid} ОДОБРЕНА")

async def decline_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) != 1:
        return
    rid = context.args[0]
    if rid in withdraw_requests and withdraw_requests[rid]["status"] == "pending":
        uid = withdraw_requests[rid]["user_id"]
        amount = withdraw_requests[rid]["amount"]
        withdraw_requests[rid]["status"] = "declined"
        users[uid]["balance"] += amount
        save_data()
        await update.message.reply_text(f"❌ {rid} ОТКЛОНЕНА")

# ========== ДЕМО ==========
async def demo_coin_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or context.args[0].lower() not in ["орел", "решка"]:
        await update.message.reply_text("❌ /demo_coin [орел/решка]")
        return
    choice = context.args[0].lower()
    result = random.choice(["орел", "решка"])
    msg = "🎉 ПОБЕДА" if choice == result else "😢 ПРОИГРЫШ"
    await update.message.reply_text(f"🪙 ДЕМО: {choice} vs {result}\n{msg}")

async def demo_number_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ /demo_number [1-10]")
        return
    try:
        guess = int(context.args[0])
        if guess < 1 or guess > 10:
            raise ValueError
    except:
        await update.message.reply_text("❌ 1-10")
        return
    num = random.randint(1, 10)
    msg = "🎉 ПОБЕДА" if guess == num else "😢 ПРОИГРЫШ"
    await update.message.reply_text(f"🔢 ДЕМО: {guess} vs {num}\n{msg}")

async def demo_dice_sum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ /demo_dice_sum [2-12]")
        return
    try:
        guess = int(context.args[0])
        if guess < 2 or guess > 12:
            raise ValueError
    except:
        await update.message.reply_text("❌ 2-12")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    msg = "🎉 ПОБЕДА" if guess == total else "😢 ПРОИГРЫШ"
    await update.message.reply_text(f"🎲 ДЕМО: {d1}+{d2}={total}\n{msg}")

async def demo_dice_over(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or context.args[0].lower() not in ["больше", "меньше"]:
        await update.message.reply_text("❌ /demo_dice_over [больше/меньше]")
        return
    choice = context.args[0].lower()
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    if (choice == "больше" and total > 7) or (choice == "меньше" and total < 7):
        msg = "🎉 ПОБЕДА"
    elif total == 7:
        msg = "😐 НИЧЬЯ"
    else:
        msg = "😢 ПРОИГРЫШ"
    await update.message.reply_text(f"🎲 ДЕМО: {d1}+{d2}={total}\n{msg}")

async def demo_dice_even(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or context.args[0].lower() not in ["чет", "нечет"]:
        await update.message.reply_text("❌ /demo_dice_even [чет/нечет]")
        return
    choice = context.args[0].lower()
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    is_even = total % 2 == 0
    if (choice == "чет" and is_even) or (choice == "нечет" and not is_even):
        msg = "🎉 ПОБЕДА"
    else:
        msg = "😢 ПРОИГРЫШ"
    await update.message.reply_text(f"🎲 ДЕМО: {d1}+{d2}={total}\n{msg}")

# ========== CALLBACK ==========
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "balance":
        await balance(update, context)
    elif data == "stats":
        await stats(update, context)
    elif data == "deposit":
        await deposit(update, context)
    elif data == "games_menu":
        await query.message.edit_text("🎮 ИГРЫ", reply_markup=games_menu())
    elif data == "withdraw_menu":
        await withdraw_menu(update, context)
    elif data == "support":
        await support(update, context)
    elif data == "demo_mode":
        await query.message.edit_text("🎮 ДЕМО", reply_markup=demo_menu())
    elif data == "referral":
        await referral(update, context)
    elif data == "game_coin":
        await game_coin(update, context)
    elif data == "game_number":
        await game_number(update, context)
    elif data == "game_dice":
        await game_dice(update, context)
    elif data == "game_slot":
        await game_slot(update, context)
    elif data == "game_roulette":
        await game_roulette(update, context)
    elif data == "game_rps":
        await game_rps(update, context)
    elif data == "demo_coin":
        await query.message.edit_text("🪙 /demo_coin [орел/решка]", reply_markup=demo_menu())
    elif data == "demo_number":
        await query.message.edit_text("🔢 /demo_number [1-10]", reply_markup=demo_menu())
    elif data == "demo_dice":
        await query.message.edit_text("🎲 /demo_dice_sum /demo_dice_over /demo_dice_even", reply_markup=demo_menu())
    elif data.startswith("rps_"):
        await rps_play(update, context)
    elif data == "back":
        await query.message.edit_text("🏠 ГЛАВНОЕ МЕНЮ", reply_markup=main_menu())

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("ref", referral))
    app.add_handler(CommandHandler("coin", coin_bet))
    app.add_handler(CommandHandler("number", number_bet))
    app.add_handler(CommandHandler("dice_sum", dice_sum))
    app.add_handler(CommandHandler("dice_over", dice_over))
    app.add_handler(CommandHandler("dice_even", dice_even))
    app.add_handler(CommandHandler("slot", slot_spin))
    app.add_handler(CommandHandler("roulette_color", roulette_color_bet))
    app.add_handler(CommandHandler("roulette_number", roulette_number_bet))
    app.add_handler(CommandHandler("rps", rps_bet))
    app.add_handler(CommandHandler("demo_coin", demo_coin_bet))
    app.add_handler(CommandHandler("demo_number", demo_number_bet))
    app.add_handler(CommandHandler("demo_dice_sum", demo_dice_sum))
    app.add_handler(CommandHandler("demo_dice_over", demo_dice_over))
    app.add_handler(CommandHandler("demo_dice_even", demo_dice_even))
    app.add_handler(CommandHandler("requests", admin_requests))
    app.add_handler(CommandHandler("approve", approve_request))
    app.add_handler(CommandHandler("decline", decline_request))
    app.add_handler(CommandHandler("add_deposit", add_deposit))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_error_handler(error_handler)
    logger.info(f"✅ {CASINO_NAME} ЗАПУЩЕН")
    app.run_polling()

if __name__ == "__main__":
    main()
