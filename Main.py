import asyncio
import random
import os
import json
import time
import logging
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("aztec_bet.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8512686337:AAGWJFTjOO82CVqnN-J6ifSlrLCcPlKCjeU"
ADMIN_ID = 8039111975
SUPPORT = "@aztec_bet_support"
CASINO_NAME = "AZTEC BET"
TON_WALLET = "UQCvOIAt2X1PHfquND-LxzVYg0Gl3a_IExORwwPjowI3Nkb8"
MIN_BET = Decimal('0.1')
MIN_DEPOSIT = Decimal('1')
MIN_WITHDRAW = Decimal('1')
REFERRAL_REGISTER_BONUS = Decimal('0.1')
REFERRAL_DEPOSIT_PERCENT = Decimal('0.05')

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
                loaded_users = json.load(f)
                for uid, data in loaded_users.items():
                    data['balance'] = float(data.get('balance', 0))
                    data['total_bet'] = float(data.get('total_bet', 0))
                    data['total_win'] = float(data.get('total_win', 0))
                    data['total_ref_earnings'] = float(data.get('total_ref_earnings', 0))
                    data['total_deposit'] = float(data.get('total_deposit', 0))
                users = loaded_users
                logger.info(f"Загружено {len(users)} пользователей")
        if os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "r") as f:
                loaded_requests = json.load(f)
                for rid, data in loaded_requests.items():
                    data['amount'] = float(data.get('amount', 0))
                withdraw_requests = loaded_requests
                logger.info(f"Загружено {len(withdraw_requests)} заявок")
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        users = {}
        withdraw_requests = {}

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        with open(REQUESTS_FILE, "w") as f:
            json.dump(withdraw_requests, f, indent=2, ensure_ascii=False)
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
        [InlineKeyboardButton("🎁 Демо-режим", callback_data="demo_mode")],
        [InlineKeyboardButton("🤝 Рефералы", callback_data="referral")],
        [InlineKeyboardButton("📞 Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def games_menu():
    keyboard = [
        [InlineKeyboardButton("🪙 Монетка", callback_data="game_coin")],
        [InlineKeyboardButton("🔢 Угадай число", callback_data="game_number")],
        [InlineKeyboardButton("🎲 Кости", callback_data="game_dice")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def demo_menu():
    keyboard = [
        [InlineKeyboardButton("🪙 Монетка (ДЕМО)", callback_data="demo_coin")],
        [InlineKeyboardButton("🔢 Угадай число (ДЕМО)", callback_data="demo_number")],
        [InlineKeyboardButton("🎲 Кости (ДЕМО)", callback_data="demo_dice")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def ensure_user_exists(uid):
    if uid not in users:
        users[uid] = {
            "balance": 0, "total_bet": 0, "total_win": 0, "spins": 0,
            "free_spin": None, "referrer": None, "referrals": [],
            "total_ref_earnings": 0, "total_deposit": 0,
            "created_at": datetime.now().isoformat(), "last_activity": datetime.now().isoformat()
        }
        save_data()
        logger.info(f"Создан новый пользователь: {uid}")
    else:
        users[uid]["last_activity"] = datetime.now().isoformat()

def validate_ton_wallet(address):
    if not address or len(address) != 48:
        return False
    if not address.startswith("UQ"):
        return False
    return True

async def demo_mode_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await query.message.edit_text("🎮 ДЕМО-РЕЖИМ\n\nИГРАЙТЕ БЕСПЛАТНО!\nБАЛАНС НЕ ИЗМЕНЯЕТСЯ", reply_markup=demo_menu())

async def demo_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🪙 ДЕМО: МОНЕТКА\n\n/demo_coin [орел/решка]\nПРИМЕР: /demo_coin орел", reply_markup=demo_menu())

async def demo_coin_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 1:
        await update.message.reply_text("❌ /demo_coin [орел/решка]")
        return
    choice = context.args[0].lower()
    if choice not in ["орел", "решка"]:
        await update.message.reply_text("❌ орел ИЛИ решка")
        return
    result = random.choice(["орел", "решка"])
    if choice == result:
        msg = f"🎉 ПОБЕДА В ДЕМО! ВЫПАЛ {result}!"
    else:
        msg = f"😢 ПРОИГРЫШ В ДЕМО! ВЫПАЛ {result}..."
    await update.message.reply_text(f"🪙 ДЕМО: МОНЕТКА\n\nВАШ ВЫБОР: {choice}\nРЕЗУЛЬТАТ: {result}\n\n{msg}\n\n💎 ДЕМО-РЕЖИМ: БАЛАНС НЕ ИЗМЕНЯЕТСЯ\n💰 РЕАЛЬНЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def demo_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🔢 ДЕМО: УГАДАЙ ЧИСЛО\n\n/demo_number [1-10]", reply_markup=demo_menu())

async def demo_number_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 1:
        await update.message.reply_text("❌ /demo_number [1-10]")
        return
    try:
        guess = int(context.args[0])
    except:
        await update.message.reply_text("❌ ВВЕДИТЕ ЧИСЛО")
        return
    if guess < 1 or guess > 10:
        await update.message.reply_text("❌ ЧИСЛО ОТ 1 ДО 10")
        return
    number = random.randint(1, 10)
    if guess == number:
        msg = f"🎉 ПОБЕДА В ДЕМО! ЗАГАДАНО {number}!"
    else:
        msg = f"😢 ПРОИГРЫШ В ДЕМО! ЗАГАДАНО {number}..."
    await update.message.reply_text(f"🔢 ДЕМО: УГАДАЙ ЧИСЛО\n\nВАШ ВЫБОР: {guess}\nРЕЗУЛЬТАТ: {number}\n\n{msg}\n\n💎 ДЕМО-РЕЖИМ: БАЛАНС НЕ ИЗМЕНЯЕТСЯ\n💰 РЕАЛЬНЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def demo_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🎲 ДЕМО: КОСТИ\n\n/demo_dice_sum [2-12]\n/demo_dice_over [больше/меньше]\n/demo_dice_even [чет/нечет]", reply_markup=demo_menu())

async def demo_dice_sum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 1:
        await update.message.reply_text("❌ /demo_dice_sum [2-12]")
        return
    try:
        guess = int(context.args[0])
    except:
        await update.message.reply_text("❌ ВВЕДИТЕ ЧИСЛО")
        return
    if guess < 2 or guess > 12:
        await update.message.reply_text("❌ СУММА ОТ 2 ДО 12")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    if guess == total:
        msg = f"🎉 ПОБЕДА В ДЕМО! {d1}+{d2}={total}!"
    else:
        msg = f"😢 ПРОИГРЫШ В ДЕМО! {d1}+{d2}={total}..."
    await update.message.reply_text(f"🎲 ДЕМО: КОСТИ\n\nВАШ ВЫБОР: {guess}\nРЕЗУЛЬТАТ: {total}\n\n{msg}\n\n💎 ДЕМО-РЕЖИМ: БАЛАНС НЕ ИЗМЕНЯЕТСЯ\n💰 РЕАЛЬНЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def demo_dice_over(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 1:
        await update.message.reply_text("❌ /demo_dice_over [больше/меньше]")
        return
    choice = context.args[0].lower()
    if choice not in ["больше", "меньше"]:
        await update.message.reply_text("❌ больше ИЛИ меньше")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    if (choice == "больше" and total > 7) or (choice == "меньше" and total < 7):
        msg = f"🎉 ПОБЕДА В ДЕМО! {d1}+{d2}={total}!"
    elif total == 7:
        msg = f"😐 НИЧЬЯ В ДЕМО! {d1}+{d2}=7"
    else:
        msg = f"😢 ПРОИГРЫШ В ДЕМО! {d1}+{d2}={total}..."
    await update.message.reply_text(f"🎲 ДЕМО: КОСТИ\n\nВАШ ВЫБОР: {choice}\nРЕЗУЛЬТАТ: {total}\n\n{msg}\n\n💎 ДЕМО-РЕЖИМ: БАЛАНС НЕ ИЗМЕНЯЕТСЯ\n💰 РЕАЛЬНЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def demo_dice_even(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 1:
        await update.message.reply_text("❌ /demo_dice_even [чет/нечет]")
        return
    choice = context.args[0].lower()
    if choice not in ["чет", "нечет"]:
        await update.message.reply_text("❌ чет ИЛИ нечет")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    is_even = total % 2 == 0
    if (choice == "чет" and is_even) or (choice == "нечет" and not is_even):
        msg = f"🎉 ПОБЕДА В ДЕМО! {d1}+{d2}={total} ({choice})!"
    else:
        msg = f"😢 ПРОИГРЫШ В ДЕМО! {d1}+{d2}={total}..."
    await update.message.reply_text(f"🎲 ДЕМО: КОСТИ\n\nВАШ ВЫБОР: {choice}\nРЕЗУЛЬТАТ: {total}\n\n{msg}\n\n💎 ДЕМО-РЕЖИМ: БАЛАНС НЕ ИЗМЕНЯЕТСЯ\n💰 РЕАЛЬНЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def game_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🪙 МОНЕТКА\n\n/coin [СУММА] [орел/решка]\nПРИМЕР: /coin 1 орел", reply_markup=games_menu())

async def coin_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /coin [СУММА] [орел/решка]")
        return
    try:
        bet = float(context.args[0])
        if bet < 0:
            await update.message.reply_text("❌ СТАВКА НЕ МОЖЕТ БЫТЬ ОТРИЦАТЕЛЬНОЙ")
            return
    except:
        await update.message.reply_text("❌ НЕВЕРНАЯ СУММА")
        return
    choice = context.args[1].lower()
    if choice not in ["орел", "решка"]:
        await update.message.reply_text("❌ орел ИЛИ решка")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМАЛЬНАЯ СТАВКА {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ! БАЛАНС: {round_ton(users[uid]['balance'])} TON")
        return
    result = random.choice(["орел", "решка"])
    if choice == result:
        win = bet * 2
        msg = f"🎉 ПОБЕДА! ВЫПАЛ {result}! +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! ВЫПАЛ {result}... -{round_ton(bet)} TON"
    users[uid]["balance"] = round_ton(users[uid]["balance"] + win)
    users[uid]["total_bet"] = round_ton(users[uid]["total_bet"] + bet)
    if win > 0:
        users[uid]["total_win"] = round_ton(users[uid]["total_win"] + win)
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🪙 МОНЕТКА\n\nСТАВКА: {bet} TON\n{msg}\n💵 НОВЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def game_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🔢 УГАДАЙ ЧИСЛО\n\n/number [СУММА] [1-10]\nПРИМЕР: /number 0.5 7", reply_markup=games_menu())

async def number_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /number [СУММА] [1-10]")
        return
    try:
        bet = float(context.args[0])
        if bet < 0:
            await update.message.reply_text("❌ СТАВКА НЕ МОЖЕТ БЫТЬ ОТРИЦАТЕЛЬНОЙ")
            return
        guess = int(context.args[1])
    except:
        await update.message.reply_text("❌ НЕВЕРНЫЕ ДАННЫЕ")
        return
    if guess < 1 or guess > 10:
        await update.message.reply_text("❌ ЧИСЛО ОТ 1 ДО 10")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМАЛЬНАЯ СТАВКА {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ! БАЛАНС: {round_ton(users[uid]['balance'])} TON")
        return
    number = random.randint(1, 10)
    if guess == number:
        win = bet * 5
        msg = f"🎉 ПОБЕДА! ЗАГАДАНО {number}! +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! ЗАГАДАНО {number}... -{round_ton(bet)} TON"
    users[uid]["balance"] = round_ton(users[uid]["balance"] + win)
    users[uid]["total_bet"] = round_ton(users[uid]["total_bet"] + bet)
    if win > 0:
        users[uid]["total_win"] = round_ton(users[uid]["total_win"] + win)
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🔢 УГАДАЙ ЧИСЛО\n\nСТАВКА: {bet} TON\n{msg}\n💵 НОВЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def game_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🎲 КОСТИ\n\n/dice_sum [2-12] [БЕТ] - x5\n/dice_over [больше/меньше] [БЕТ] - x2\n/dice_even [чет/нечет] [БЕТ] - x1.5\n\nПРИМЕРЫ:\n/dice_sum 7 1\n/dice_over больше 1\n/dice_even чет 1", reply_markup=games_menu())

async def dice_sum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /dice_sum [2-12] [БЕТ]")
        return
    try:
        guess = int(context.args[0])
        bet = float(context.args[1])
        if bet < 0:
            await update.message.reply_text("❌ СТАВКА НЕ МОЖЕТ БЫТЬ ОТРИЦАТЕЛЬНОЙ")
            return
    except:
        await update.message.reply_text("❌ НЕВЕРНЫЕ ДАННЫЕ")
        return
    if guess < 2 or guess > 12:
        await update.message.reply_text("❌ СУММА ОТ 2 ДО 12")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМАЛЬНАЯ СТАВКА {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ! БАЛАНС: {round_ton(users[uid]['balance'])} TON")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    if guess == total:
        win = bet * 5
        msg = f"🎉 ПОБЕДА! {d1}+{d2}={total}! +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! {d1}+{d2}={total}... -{round_ton(bet)} TON"
    users[uid]["balance"] = round_ton(users[uid]["balance"] + win)
    users[uid]["total_bet"] = round_ton(users[uid]["total_bet"] + bet)
    if win > 0:
        users[uid]["total_win"] = round_ton(users[uid]["total_win"] + win)
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🎲 КОСТИ (СУММА)\n\nСТАВКА: {bet} TON\n{msg}\n💵 НОВЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def dice_over(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /dice_over [больше/меньше] [БЕТ]")
        return
    choice = context.args[0].lower()
    if choice not in ["больше", "меньше"]:
        await update.message.reply_text("❌ больше ИЛИ меньше")
        return
    try:
        bet = float(context.args[1])
        if bet < 0:
            await update.message.reply_text("❌ СТАВКА НЕ МОЖЕТ БЫТЬ ОТРИЦАТЕЛЬНОЙ")
            return
    except:
        await update.message.reply_text("❌ НЕВЕРНАЯ СУММА")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМАЛЬНАЯ СТАВКА {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ! БАЛАНС: {round_ton(users[uid]['balance'])} TON")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    if (choice == "больше" and total > 7) or (choice == "меньше" and total < 7):
        win = bet * 2
        msg = f"🎉 ПОБЕДА! {d1}+{d2}={total}! +{round_ton(win)} TON"
    elif total == 7:
        win = 0
        msg = f"😐 НИЧЬЯ! {d1}+{d2}=7 (СТАВКА ВОЗВРАЩЕНА)"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! {d1}+{d2}={total}... -{round_ton(bet)} TON"
    users[uid]["balance"] = round_ton(users[uid]["balance"] + win)
    users[uid]["total_bet"] = round_ton(users[uid]["total_bet"] + bet)
    if win > 0:
        users[uid]["total_win"] = round_ton(users[uid]["total_win"] + win)
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🎲 КОСТИ (БОЛЬШЕ/МЕНЬШЕ)\n\nСТАВКА: {bet} TON\n{msg}\n💵 НОВЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def dice_even(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /dice_even [чет/нечет] [БЕТ]")
        return
    choice = context.args[0].lower()
    if choice not in ["чет", "нечет"]:
        await update.message.reply_text("❌ чет ИЛИ нечет")
        return
    try:
        bet = float(context.args[1])
        if bet < 0:
            await update.message.reply_text("❌ СТАВКА НЕ МОЖЕТ БЫТЬ ОТРИЦАТЕЛЬНОЙ")
            return
    except:
        await update.message.reply_text("❌ НЕВЕРНАЯ СУММА")
        return
    if bet < float(MIN_BET):
        await update.message.reply_text(f"❌ МИНИМАЛЬНАЯ СТАВКА {MIN_BET} TON")
        return
    if users[uid]["balance"] < bet:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ! БАЛАНС: {round_ton(users[uid]['balance'])} TON")
        return
    d1, d2 = random.randint(1,6), random.randint(1,6)
    total = d1 + d2
    is_even = total % 2 == 0
    if (choice == "чет" and is_even) or (choice == "нечет" and not is_even):
        win = bet * 1.5
        msg = f"🎉 ПОБЕДА! {d1}+{d2}={total} ({choice})! +{round_ton(win)} TON"
    else:
        win = -bet
        msg = f"😢 ПРОИГРЫШ! {d1}+{d2}={total}... -{round_ton(bet)} TON"
    users[uid]["balance"] = round_ton(users[uid]["balance"] + win)
    users[uid]["total_bet"] = round_ton(users[uid]["total_bet"] + bet)
    if win > 0:
        users[uid]["total_win"] = round_ton(users[uid]["total_win"] + win)
    users[uid]["spins"] += 1
    save_data()
    await update.message.reply_text(f"🎲 КОСТИ (ЧЁТ/НЕЧЕТ)\n\nСТАВКА: {bet} TON\n{msg}\n💵 НОВЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name or "Игрок"
    ref = context.args[0] if context.args else None
    await ensure_user_exists(uid)
    
    if ref and ref != uid and ref in users and not users[uid].get("referrer"):
        users[uid]["referrer"] = ref
        if "referrals" not in users[ref]:
            users[ref]["referrals"] = []
        if uid not in users[ref]["referrals"]:
            users[ref]["referrals"].append(uid)
        users[uid]["balance"] = round_ton(users[uid]["balance"] + float(REFERRAL_REGISTER_BONUS))
        save_data()
        await context.bot.send_message(uid, f"🎉 +{REFERRAL_REGISTER_BONUS} TON ЗА РЕГИСТРАЦИЮ ПО РЕФЕРАЛЬНОЙ ССЫЛКЕ!")
        try:
            await context.bot.send_message(ref, f"🤝 НОВЫЙ РЕФЕРАЛ! {name} получил бонус {REFERRAL_REGISTER_BONUS} TON")
        except:
            pass
    
    await update.message.reply_text(
        f"🎰 ДОБРО ПОЖАЛОВАТЬ В {CASINO_NAME} 🎰\n\n"
        f"ПРИВЕТ, {name}!\n\n"
        f"💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON\n\n"
        f"📋 СПИСОК КОМАНД:\n\n"
        f"🎮 ИГРЫ:\n"
        f"🪙 /coin [СУММА] [орел/решка] - Монетка (x2)\n"
        f"🔢 /number [СУММА] [1-10] - Угадай число (x5)\n"
        f"🎲 /dice_sum [СУММА 2-12] [БЕТ] - Кости сумма (x5)\n"
        f"🎲 /dice_over [больше/меньше] [БЕТ] - Кости больше/меньше 7 (x2)\n"
        f"🎲 /dice_even [чет/нечет] [БЕТ] - Кости чёт/нечет (x1.5)\n\n"
        f"🎮 ДЕМО-РЕЖИМ (БЕСПЛАТНО):\n"
        f"🪙 /demo_coin [орел/решка]\n"
        f"🔢 /demo_number [1-10]\n"
        f"🎲 /demo_dice_sum [СУММА]\n"
        f"🎲 /demo_dice_over [больше/меньше]\n"
        f"🎲 /demo_dice_even [чет/нечет]\n\n"
        f"💰 ФИНАНСЫ:\n"
        f"💎 /balance - Проверить баланс\n"
        f"📊 /stats - Статистика\n"
        f"💸 /withdraw [СУММА] [АДРЕС] - Вывести средства\n"
        f"📞 /support - Поддержка\n"
        f"🤝 /ref - Реферальная программа\n\n"
        f"💎 КОШЕЛЁК ДЛЯ ПОПОЛНЕНИЯ:\n`{TON_WALLET}`\n"
        f"📝 В КОММЕНТАРИИ УКАЖИТЕ ВАШ ID: `{uid}`\n\n"
        f"📞 ПОДДЕРЖКА: {SUPPORT}",
        reply_markup=main_menu()
    )

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await message.reply_text(
        f"💎 ПОПОЛНЕНИЕ 💎\n\n"
        f"📦 КОШЕЛЁК:\n`{TON_WALLET}`\n\n"
        f"💰 МИНИМУМ: {MIN_DEPOSIT} TON\n"
        f"📝 В КОММЕНТАРИИ УКАЖИТЕ ID: `{uid}`\n\n"
        f"✅ ПОСЛЕ ОТПРАВКИ НАПИШИТЕ АДМИНУ {SUPPORT}",
        reply_markup=main_menu()
    )

async def add_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ НЕТ ДОСТУПА")
        return
    if len(context.args) != 2:
        await update.message.reply_text("❌ /add_deposit [USER_ID] [СУММА]")
        return
    uid = context.args[0]
    try:
        amount = float(context.args[1])
        if amount <= 0:
            await update.message.reply_text("❌ СУММА ДОЛЖНА БЫТЬ ПОЛОЖИТЕЛЬНОЙ")
            return
    except:
        await update.message.reply_text("❌ НЕВЕРНАЯ СУММА")
        return
    await ensure_user_exists(uid)
    users[uid]["balance"] = round_ton(users[uid]["balance"] + amount)
    users[uid]["total_deposit"] = round_ton(users[uid].get("total_deposit", 0) + amount)
    save_data()
    await update.message.reply_text(f"✅ ДЕПОЗИТ {round_ton(amount)} TON НАЧИСЛЕН ПОЛЬЗОВАТЕЛЮ {uid}\n💰 НОВЫЙ БАЛАНС: {round_ton(users[uid]['balance'])} TON")
    try:
        await context.bot.send_message(uid, f"✅ ВАШ ДЕПОЗИТ {round_ton(amount)} TON ЗАЧИСЛЕН!\n💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON")
    except:
        pass
    referrer = users[uid].get("referrer")
    if referrer and referrer in users and referrer != uid:
        ref_bonus = round_ton(amount * float(REFERRAL_DEPOSIT_PERCENT))
        users[referrer]["balance"] = round_ton(users[referrer]["balance"] + ref_bonus)
        users[referrer]["total_ref_earnings"] = round_ton(users[referrer].get("total_ref_earnings", 0) + ref_bonus)
        save_data()
        try:
            await context.bot.send_message(referrer, f"🎉 ВАШ РЕФЕРАЛ СДЕЛАЛ ДЕПОЗИТ {round_ton(amount)} TON!\n💎 ВЫ ПОЛУЧИЛИ {ref_bonus} TON (5%)")
        except:
            pass

async def withdraw_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await query.message.edit_text(
        f"💸 ВЫВОД СРЕДСТВ\n\n"
        f"💰 ВАШ БАЛАНС: {round_ton(users[uid]['balance'])} TON\n"
        f"💵 МИНИМУМ: {MIN_WITHDRAW} TON\n\n"
        f"ИСПОЛЬЗУЙТЕ КОМАНДУ:\n"
        f"/withdraw [СУММА] [АДРЕС]\n\n"
        f"ПРИМЕР:\n"
        f"/withdraw 10 UQCvOIAt2X1PHfquND-LxzVYg0Gl3a_IExORwwPjowI3Nkb8",
        reply_markup=main_menu()
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    if len(context.args) != 2:
        await update.message.reply_text("❌ /withdraw [СУММА] [АДРЕС]")
        return
    try:
        amount = float(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ СУММА ДОЛЖНА БЫТЬ ПОЛОЖИТЕЛЬНОЙ")
            return
    except:
        await update.message.reply_text("❌ НЕВЕРНАЯ СУММА")
        return
    wallet = context.args[1]
    if not validate_ton_wallet(wallet):
        await update.message.reply_text("❌ НЕВЕРНЫЙ АДРЕС КОШЕЛЬКА TON")
        return
    if amount < float(MIN_WITHDRAW):
        await update.message.reply_text(f"❌ МИНИМУМ ВЫВОДА: {MIN_WITHDRAW} TON")
        return
    if users[uid]["balance"] < amount:
        await update.message.reply_text(f"❌ НЕДОСТАТОЧНО СРЕДСТВ")
        return
    users[uid]["balance"] = round_ton(users[uid]["balance"] - amount)
    rid = f"{uid}_{int(time.time())}"
    withdraw_requests[rid] = {
        "user_id": uid, "amount": amount, "wallet": wallet, "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    save_data()
    await update.message.reply_text(
        f"✅ ЗАЯВКА №{rid} ПРИНЯТА\n\n"
        f"💰 {round_ton(amount)} TON\n"
        f"📦 {wallet}\n"
        f"⏱ ВЫВОД ДО 72 ЧАСОВ",
        reply_markup=main_menu()
    )
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"📝 НОВАЯ ЗАЯВКА {rid}\n👤 {uid}\n💰 {round_ton(amount)} TON\n📦 {wallet}\n\n✅ /approve {rid}\n❌ /decline {rid}"
        )
    except:
        pass

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    await update.message.reply_text(f"💰 БАЛАНС: {round_ton(users[uid]['balance'])} TON", reply_markup=main_menu())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    tb = round_ton(users[uid]["total_bet"])
    tw = round_ton(users[uid]["total_win"])
    result = round_ton(tw - tb)
    await update.message.reply_text(
        f"📊 СТАТИСТИКА 📊\n\n"
        f"🎰 СТАВОК: {users[uid]['spins']}\n"
        f"💰 ПОСТАВЛЕНО: {tb} TON\n"
        f"🏆 ВЫИГРАНО: {tw} TON\n"
        f"📉 РЕЗУЛЬТАТ: {result} TON\n"
        f"💎 ВСЕГО ДЕПОЗИТОВ: {round_ton(users[uid].get('total_deposit', 0))} TON",
        reply_markup=main_menu()
    )

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📞 ПОДДЕРЖКА: {SUPPORT}", reply_markup=main_menu())

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    await ensure_user_exists(uid)
    bot = (await context.bot.get_me()).username
    await update.message.reply_text(
        f"🤝 РЕФЕРАЛЬНАЯ ПРОГРАММА 🤝\n\n"
        f"👥 ПРИГЛАШЁННЫХ: {len(users[uid].get('referrals', []))}\n"
        f"💰 ЗАРАБОТАНО: {round_ton(users[uid].get('total_ref_earnings', 0))} TON\n\n"
        f"🔗 ВАША ССЫЛКА:\n`https://t.me/{bot}?start={uid}`\n\n"
        f"🎁 ЗА КАЖДОГО ДРУГА: +{REFERRAL_REGISTER_BONUS} TON ПРИ РЕГИСТРАЦИИ\n"
        f"💎 5% ОТ ВСЕХ ДЕПОЗИТОВ ДРУГА",
        reply_markup=main_menu()
    )

async def admin_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ НЕТ ДОСТУПА")
        return
    if not withdraw_requests:
        await update.message.reply_text("📭 НЕТ АКТИВНЫХ ЗАЯВОК")
        return
    for rid, req in withdraw_requests.items():
        if req.get("status") == "pending":
            await update.message.reply_text(
                f"📝 ЗАЯВКА: {rid}\n"
                f"👤 {req['user_id']}\n"
                f"💰 {round_ton(req['amount'])} TON\n"
                f"📦 {req['wallet']}\n\n"
                f"✅ /approve {rid}\n"
                f"❌ /decline {rid}"
            )

async def approve_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ НЕТ ДОСТУПА")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ /approve [ID_ЗАЯВКИ]")
        return
    rid = context.args[0]
    if rid not in withdraw_requests or withdraw_requests[rid]["status"] != "pending":
        await update.message.reply_text("❌ ЗАЯВКА НЕ НАЙДЕНА")
        return
    withdraw_requests[rid]["status"] = "approved"
    save_data()
    await update.message.reply_text(f"✅ ЗАЯВКА {rid} ОДОБРЕНА")
    try:
        await context.bot.send_message(withdraw_requests[rid]["user_id"], f"✅ ВАША ЗАЯВКА НА ВЫВОД {round_ton(withdraw_requests[rid]['amount'])} TON ОДОБРЕНА!")
    except:
        pass

async def decline_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ НЕТ ДОСТУПА")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ /decline [ID_ЗАЯВКИ]")
        return
    rid = context.args[0]
    if rid not in withdraw_requests or withdraw_requests[rid]["status"] != "pending":
        await update.message.reply_text("❌ ЗАЯВКА НЕ НАЙДЕНА")
        return
    user_id = withdraw_requests[rid]["user_id"]
    amount = withdraw_requests[rid]["amount"]
    withdraw_requests[rid]["status"] = "declined"
    if user_id in users:
        users[user_id]["balance"] = round_ton(users[user_id]["balance"] + amount)
        save_data()
    await update.message.reply_text(f"❌ ЗАЯВКА {rid} ОТКЛОНЕНА")
    try:
        await context.bot.send_message(user_id, f"❌ ВАША ЗАЯВКА НА ВЫВОД {round_ton(amount)} TON ОТКЛОНЕНА\n💰 СРЕДСТВА ВОЗВРАЩЕНЫ НА БАЛАНС")
    except:
        pass

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
        await query.message.edit_text("🎮 ВЫБЕРИТЕ ИГРУ 🎮", reply_markup=games_menu())
    elif data == "withdraw_menu":
        await withdraw_menu(update, context)
    elif data == "support":
        await support(update, context)
    elif data == "demo_mode":
        await demo_mode_menu(update, context)
    elif data == "referral":
        await referral(update, context)
    elif data == "game_coin":
        await game_coin(update, context)
    elif data == "game_number":
        await game_number(update, context)
    elif data == "game_dice":
        await game_dice(update, context)
    elif data == "demo_coin":
        await demo_coin(update, context)
    elif data == "demo_number":
        await demo_number(update, context)
    elif data == "demo_dice":
        await demo_dice(update, context)
    elif data == "back":
        await query.message.edit_text("🏠 ГЛАВНОЕ МЕНЮ", reply_markup=main_menu())

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

async def main():
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
    
    logger.info(f"✅ {CASINO_NAME} ЗАПУЩЕН!")
    logger.info(f"👨‍💼 АДМИН: {ADMIN_ID}")
    logger.info(f"📝 ЛОГИ СОХРАНЯЮТСЯ В aztec_bet.log")
    
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
