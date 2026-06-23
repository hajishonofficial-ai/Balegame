"""
ربات بازی‌های ۲ نفره برای اپلیکیشن بله
نویسنده: دستیار هوشمند
ویژگی‌ها:
- چندین بازی ۲ نفره (سنگ کاغذ قیچی، دوز، حدس عدد، جنگ اعداد)
- سیستم شرط‌بندی اختیاری
- اعتبار اولیه ۱۰۰۰ سکه برای هر کاربر
- مچ‌میکینگ تصادفی
- ذخیره‌سازی اطلاعات کاربران
"""

import asyncio
import random
import json
import os
from datetime import datetime
from balethon import Bot
from balethon.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineButton
from balethon.tl.custom import conversation

# ============================================
# تنظیمات ربات
# ============================================
API_ID = 'YOUR_API_ID'  # اینجا API_ID خود را وارد کنید
API_HASH = 'YOUR_API_HASH'  # اینجا API_HASH خود را وارد کنید
BOT_TOKEN = 'YOUR_BOT_TOKEN'  # اینجا توکن ربات خود را وارد کنید

# فایل ذخیره‌سازی اطلاعات کاربران
DATA_FILE = 'users_data.json'

# ============================================
# مدیریت داده‌ها
# ============================================
class UserDataManager:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.users = self.load_data()
    
    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def get_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                'coins': 1000,
                'games_played': 0,
                'games_won': 0,
                'games_lost': 0,
                'in_game': False,
                'current_game': None,
                'opponent': None,
                'bet_amount': 0,
                'waiting_for_match': False
            }
            self.save_data()
        return self.users[user_id]
    
    def update_coins(self, user_id, amount):
        user = self.get_user(user_id)
        user['coins'] += amount
        self.save_data()
        return user['coins']
    
    def get_coins(self, user_id):
        return self.get_user(user_id)['coins']
    
    def set_in_game(self, user_id, in_game=True, game_type=None, opponent=None, bet=0):
        user = self.get_user(user_id)
        user['in_game'] = in_game
        user['current_game'] = game_type
        user['opponent'] = opponent
        user['bet_amount'] = bet
        user['waiting_for_match'] = False
        self.save_data()
    
    def add_game_result(self, user_id, won):
        user = self.get_user(user_id)
        user['games_played'] += 1
        if won:
            user['games_won'] += 1
        else:
            user['games_lost'] += 1
        self.save_data()
    
    def set_waiting(self, user_id, waiting=True):
        user = self.get_user(user_id)
        user['waiting_for_match'] = waiting
        self.save_data()

# ایجاد نمونه مدیر داده‌ها
db = UserDataManager()

# ============================================
# کلاس‌های بازی
# ============================================
class Game:
    def __init__(self, player1, player2, bet=0):
        self.player1 = player1
        self.player2 = player2
        self.bet = bet
        self.winner = None
        self.game_state = {}
    
    async def end_game(self, bot, winner, reason=""):
        pass

class RockPaperScissors(Game):
    """بازی سنگ کاغذ قیچی"""
    def __init__(self, player1, player2, bet=0):
        super().__init__(player1, player2, bet)
        self.choices = {'player1': None, 'player2': None}
        self.name = "سنگ کاغذ قیچی"
    
    def make_move(self, player, choice):
        if player == self.player1:
            self.choices['player1'] = choice
        elif player == self.player2:
            self.choices['player2'] = choice
    
    def determine_winner(self):
        c1, c2 = self.choices['player1'], self.choices['player2']
        if c1 == c2:
            return 'draw'
        if (c1 == 'سنگ' and c2 == 'قیچی') or \
           (c1 == 'کاغذ' and c2 == 'سنگ') or \
           (c1 == 'قیچی' and c2 == 'کاغذ'):
            return self.player1
        return self.player2
    
    async def end_game(self, bot, winner, reason=""):
        c1 = self.choices.get('player1', '?')
        c2 = self.choices.get('player2', '?')
        
        msg = f"🎮 نتایج بازی سنگ کاغذ قیچی\n\n"
        msg += f"👤 انتخاب بازیکن ۱: {c1}\n"
        msg += f"👤 انتخاب بازیکن ۲: {c2}\n\n"
        
        if winner == 'draw':
            msg += "🤝 مساوی شد! مبلغ شرط برگشت می‌خورد."
            db.update_coins(self.player1, self.bet)
            db.update_coins(self.player2, self.bet)
        elif winner == self.player1:
            msg += f"🏆 بازیکن ۱ برنده شد!\n💰 مبلغ {self.bet * 2} سکه به حساب برنده واریز شد."
            db.update_coins(self.player1, self.bet * 2)
            db.add_game_result(self.player1, True)
            db.add_game_result(self.player2, False)
        else:
            msg += f"🏆 بازیکن ۲ برنده شد!\n💰 مبلغ {self.bet * 2} سکه به حساب برنده واریز شد."
            db.update_coins(self.player2, self.bet * 2)
            db.add_game_result(self.player2, True)
            db.add_game_result(self.player1, False)
        
        try:
            await bot.send_message(self.player1, msg)
            await bot.send_message(self.player2, msg)
        except:
            pass

class TicTacToe(Game):
    """بازی دوز"""
    def __init__(self, player1, player2, bet=0):
        super().__init__(player1, player2, bet)
        self.board = [' '] * 9
        self.current_player = player1
        self.symbols = {player1: '❌', player2: '⭕'}
        self.name = "دوز"
        self.move_history = []
    
    def display_board(self):
        b = self.board
        return f"""
┌───┬───┬───┐
│ {b[0]} │ {b[1]} │ {b[2]} │
├───┼───┼───┤
│ {b[3]} │ {b[4]} │ {b[5]} │
├───┼───┼───┤
│ {b[6]} │ {b[7]} │ {b[8]} │
└───┴───┴───┘
"""
    
    def make_move(self, player, position):
        if player != self.current_player:
            return False
        if position < 0 or position > 8 or self.board[position] != ' ':
            return False
        
        self.board[position] = self.symbols[player]
        self.move_history.append((player, position))
        
        if self.check_winner():
            self.winner = player
        elif ' ' not in self.board:
            self.winner = 'draw'
        else:
            self.current_player = self.player2 if player == self.player1 else self.player1
        
        return True
    
    def check_winner(self):
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        for cond in win_conditions:
            if self.board[cond[0]] == self.board[cond[1]] == self.board[cond[2]] != ' ':
                return True
        return False
    
    async def end_game(self, bot, winner, reason=""):
        msg = f"🎮 نتایج بازی دوز\n\n{self.display_board()}\n"
        
        if winner == 'draw':
            msg += "🤝 مساوی شد! مبلغ شرط برگشت می‌خورد."
            db.update_coins(self.player1, self.bet)
            db.update_coins(self.player2, self.bet)
        elif winner == self.player1:
            msg += f"🏆 بازیکن ۱ (❌) برنده شد!\n💰 مبلغ {self.bet * 2} سکه به حساب برنده واریز شد."
            db.update_coins(self.player1, self.bet * 2)
            db.add_game_result(self.player1, True)
            db.add_game_result(self.player2, False)
        else:
            msg += f"🏆 بازیکن ۲ (⭕) برنده شد!\n💰 مبلغ {self.bet * 2} سکه به حساب برنده واریز شد."
            db.update_coins(self.player2, self.bet * 2)
            db.add_game_result(self.player2, True)
            db.add_game_result(self.player1, False)
        
        try:
            await bot.send_message(self.player1, msg)
            await bot.send_message(self.player2, msg)
        except:
            pass

class GuessNumber(Game):
    """بازی حدس عدد"""
    def __init__(self, player1, player2, bet=0):
        super().__init__(player1, player2, bet)
        self.target_number = random.randint(1, 100)
        self.guesses = {'player1': [], 'player2': []}
        self.current_player = player1
        self.max_guesses = 10
        self.name = "حدس عدد"
    
    def make_guess(self, player, guess):
        if player != self.current_player:
            return None
        
        try:
            guess = int(guess)
        except:
            return "نامعتبر"
        
        if guess < 1 or guess > 100:
            return "عدد باید بین ۱ تا ۱۰۰ باشد"
        
        if player == self.player1:
            self.guesses['player1'].append(guess)
        else:
            self.guesses['player2'].append(guess)
        
        if guess == self.target_number:
            self.winner = player
            return "correct"
        
        all_guesses = self.guesses['player1'] + self.guesses['player2']
        if len(all_guesses) >= self.max_guesses:
            self.winner = self.player2 if player == self.player1 else self.player1
            return "out_of_guesses"
        
        hint = ""
        if guess < self.target_number:
            hint = "📈 برو بالاتر!"
        else:
            hint = "📉 برو پایین‌تر!"
        
        self.current_player = self.player2 if player == self.player1 else self.player1
        return hint
    
    async def end_game(self, bot, winner, reason=""):
        msg = f"🎮 نتایج بازی حدس عدد\n\n"
        msg += f"🎯 عدد هدف: {self.target_number}\n\n"
        msg += f"👤 حدس‌های بازیکن ۱: {self.guesses['player1']}\n"
        msg += f"👤 حدس‌های بازیکن ۲: {self.guesses['player2']}\n\n"
        
        if winner == self.player1:
            msg += f"🏆 بازیکن ۱ برنده شد!\n💰 مبلغ {self.bet * 2} سکه به حساب برنده واریز شد."
            db.update_coins(self.player1, self.bet * 2)
            db.add_game_result(self.player1, True)
            db.add_game_result(self.player2, False)
        else:
            msg += f"🏆 بازیکن ۲ برنده شد!\n💰 مبلغ {self.bet * 2} سکه به حساب برنده واریز شد."
            db.update_coins(self.player2, self.bet * 2)
            db.add_game_result(self.player2, True)
            db.add_game_result(self.player1, False)
        
        try:
            await bot.send_message(self.player1, msg)
            await bot.send_message(self.player2, msg)
        except:
            pass

class NumberWar(Game):
    """بازی جنگ اعداد"""
    def __init__(self, player1, player2, bet=0):
        super().__init__(player1, player2, bet)
        self.cards_p1 = list(range(1, 14)) * 2
        self.cards_p2 = list(range(1, 14)) * 2
        random.shuffle(self.cards_p1)
        random.shuffle(self.cards_p2)
        self.rounds = []
        self.name = "جنگ اعداد"
    
    def play_round(self, round_num):
        if round_num >= len(self.cards_p1):
            return None
        
        card1 = self.cards_p1[round_num]
        card2 = self.cards_p2[round_num]
        self.rounds.append((card1, card2))
        
        if card1 > card2:
            return self.player1
        elif card2 > card1:
            return self.player2
        return 'draw'
    
    async def end_game(self, bot, winner, reason=""):
        p1_wins = sum(1 for r in self.rounds if r[0] > r[1])
        p2_wins = sum(1 for r in self.rounds if r[1] > r[0])
        draws = sum(1 for r in self.rounds if r[0] == r[1])
        
        msg = f"🎮 نتایج بازی جنگ اعداد\n\n"
        msg += f"📊 آمار دورها:\n"
        msg += f"🏆 برد بازیکن ۱: {p1_wins}\n"
        msg += f"🏆 برد بازیکن ۲: {p2_wins}\n"
        msg += f"🤝 مساوی: {draws}\n\n"
        
        if p1_wins > p2_wins:
            winner = self.player1
            msg += f"🏆 بازیکن ۱ برنده نهایی شد!\n💰 مبلغ {self.bet * 2} سکه به حساب برنده واریز شد."
            db.update_coins(self.player1, self.bet * 2)
            db.add_game_result(self.player1, True)
            db.add_game_result(self.player2, False)
        elif p2_wins > p1_wins:
            winner = self.player2
            msg += f"🏆 بازیکن ۲ برنده نهایی شد!\n💰 مبلغ {self.bet * 2} سکه به حساب برنده واریز شد."
            db.update_coins(self.player2, self.bet * 2)
            db.add_game_result(self.player2, True)
            db.add_game_result(self.player1, False)
        else:
            msg += "🤝 مساوی شد! مبلغ شرط برگشت می‌خورد."
            db.update_coins(self.player1, self.bet)
            db.update_coins(self.player2, self.bet)
        
        try:
            await bot.send_message(self.player1, msg)
            await bot.send_message(self.player2, msg)
        except:
            pass

# ============================================
# مدیریت بازی‌ها
# ============================================
active_games = {}
waiting_queue = []

def create_game(game_type, player1, player2, bet=0):
    if game_type == 'rps':
        return RockPaperScissors(player1, player2, bet)
    elif game_type == 'tictactoe':
        return TicTacToe(player1, player2, bet)
    elif game_type == 'guess':
        return GuessNumber(player1, player2, bet)
    elif game_type == 'war':
        return NumberWar(player1, player2, bet)
    return None

# ============================================
# کیبوردها
# ============================================
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [KeyboardButton('🎮 شروع بازی'), KeyboardButton('📊 پروفایل من')],
        [KeyboardButton('🏆 جدول برترین‌ها'), KeyboardButton('❓ راهنما')],
        resize_keyboard=True
    )

def game_selection_keyboard():
    return InlineKeyboardMarkup(
        [InlineButton('🗿 سنگ کاغذ قیچی', data='game_rps')],
        [InlineButton('⭕ دوز', data='game_tictactoe')],
        [InlineButton('🔢 حدس عدد', data='game_guess')],
        [InlineButton('⚔️ جنگ اعداد', data='game_war')],
        [InlineButton('❌ انصراف', data='cancel')]
    )

def bet_selection_keyboard():
    buttons = []
    amounts = [100, 200, 500, 1000, 2000]
    for i in range(0, len(amounts), 2):
        row = []
        row.append(InlineButton(f'{amounts[i]} 💰', data=f'bet_{amounts[i]}'))
        if i + 1 < len(amounts):
            row.append(InlineButton(f'{amounts[i+1]} 💰', data=f'bet_{amounts[i+1]}'))
        buttons.append(row)
    buttons.append([InlineButton('🚫 بدون شرط', data='bet_0')])
    buttons.append([InlineButton('❌ انصراف', data='cancel')])
    return InlineKeyboardMarkup(*buttons)

def rps_keyboard():
    return InlineKeyboardMarkup(
        [InlineButton('🗿 سنگ', data='rps_rock')],
        [InlineButton('📄 کاغذ', data='rps_paper')],
        [InlineButton('✂️ قیچی', data='rps_scissors')]
    )

def tictactoe_keyboard(game):
    board = game.board
    buttons = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            pos = i + j
            symbol = board[pos] if board[pos] != ' ' else f'{pos}'
            row.append(InlineButton(symbol, data=f'ttt_{pos}'))
        buttons.append(row)
    buttons.append([InlineButton('❌ انصراف', data='cancel_game')])
    return InlineKeyboardMarkup(*buttons)

# ============================================
# ایجاد ربات
# ============================================
bot = Bot(API_ID, API_HASH, BOT_TOKEN)

# ============================================
# هندلرها
# ============================================
@bot.on_message('/start')
async def start_handler(message):
    user_id = message.peer_id.user_id
    db.get_user(user_id)
    
    welcome_msg = f"""
🎉 سلام! به ربات بازی‌های ۲ نفره خوش آمدی! 🎮

🎁 شما {db.get_coins(user_id)} سکه اعتبار اولیه دریافت کردید.

می‌تونی با دوستانت یا به صورت تصادفی با دیگران بازی کنی!

🎲 بازی‌های موجود:
• سنگ کاغذ قیچی
• دوز (Tic Tac Toe)
• حدس عدد
• جنگ اعداد

💡 برای شروع دکمه «🎮 شروع بازی» را بزن!
"""
    await message.reply(welcome_msg, keyboard=main_menu_keyboard())

@bot.on_message('🎮 شروع بازی')
async def start_game_handler(message):
    user_id = message.peer_id.user_id
    user = db.get_user(user_id)
    
    if user['in_game']:
        await message.reply("❌ شما در حال حاضر در یک بازی هستید!")
        return
    
    if user['waiting_for_match']:
        await message.reply("❌ شما قبلاً در صف انتظار هستید!")
        return
    
    await message.reply("🎯 انتخاب نوع بازی:", keyboard=game_selection_keyboard())

@bot.on_callback_query('game_')
async def game_type_callback(query):
    user_id = query.peer_id.user_id
    user = db.get_user(user_id)
    
    if user['in_game']:
        await query.answer("❌ شما در حال حاضر در یک بازی هستید!", alert=True)
        return
    
    game_type = query.data.split('_')[1]
    game_names = {'rps': 'سنگ کاغذ قیچی', 'tictactoe': 'دوز', 'guess': 'حدس عدد', 'war': 'جنگ اعداد'}
    
    await query.edit_message(f"🎮 بازی انتخاب شده: {game_names.get(game_type, '')}\n\n💰 مقدار شرط را انتخاب کنید:")
    
    user['temp_game_type'] = game_type
    db.save_data()

@bot.on_callback_query('bet_')
async def bet_callback(query):
    user_id = query.peer_id.user_id
    user = db.get_user(user_id)
    
    if 'temp_game_type' not in user:
        await query.answer("❌ ابتدا نوع بازی را انتخاب کنید!", alert=True)
        return
    
    bet_amount = int(query.data.split('_')[1])
    
    if bet_amount > user['coins']:
        await query.answer("❌ اعتبار کافی ندارید!", alert=True)
        return
    
    user['temp_bet'] = bet_amount
    db.save_data()
    
    game_names = {'rps': 'سنگ کاغذ قیچی', 'tictactoe': 'دوز', 'guess': 'حدس عدد', 'war': 'جنگ اعداد'}
    game_type = user['temp_game_type']
    
    await query.edit_message(f"""
🎮 آماده‌سازی بازی...

🎯 بازی: {game_names.get(game_type, '')}
💰 شرط: {bet_amount} سکه

⏳ در حال جستجو برای حریف...
""")
    
    db.set_waiting(user_id, True)
    waiting_queue.append((user_id, game_type, bet_amount, query.msg_id))
    
    await match_players(bot)

@bot.on_callback_query('cancel')
async def cancel_callback(query):
    user_id = query.peer_id.user_id
    user = db.get_user(user_id)
    
    if 'temp_game_type' in user:
        del user['temp_game_type']
    if 'temp_bet' in user:
        del user['temp_bet']
    db.save_data()
    
    await query.edit_message("❌ عملیات لغو شد.\n\nبرای شروع مجدد دکمه «🎮 شروع بازی» را بزنید.")

@bot.on_message('📊 پروفایل من')
async def profile_handler(message):
    user_id = message.peer_id.user_id
    user = db.get_user(user_id)
    
    win_rate = 0
    if user['games_played'] > 0:
        win_rate = (user['games_won'] / user['games_played']) * 100
    
    profile_msg = f"""
📊 پروفایل شما

💰 اعتبار: {user['coins']} سکه
🎮 تعداد بازی‌ها: {user['games_played']}
🏆 برد: {user['games_won']}
❌ باخت: {user['games_lost']}
📈 نرخ برد: {win_rate:.1f}%

{'🌟 بازیکن حرفه‌ای!' if win_rate > 60 else '💪 بیشتر بازی کن تا بهتر بشی!'}
"""
    await message.reply(profile_msg)

@bot.on_message('🏆 جدول برترین‌ها')
async def leaderboard_handler(message):
    sorted_users = sorted(db.users.items(), key=lambda x: x[1]['games_won'], reverse=True)[:10]
    
    msg = "🏆 جدول برترین‌ها 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medals = ['🥇', '🥈', '🥉']
        medal = medals[i-1] if i <= 3 else f'{i}.'
        msg += f"{medal} کاربر {uid}: {data['games_won']} برد\n"
    
    await message.reply(msg)

@bot.on_message('❓ راهنما')
async def help_handler(message):
    help_msg = """
❓ راهنمای ربات

🎮 شروع بازی:
۱. دکمه «🎮 شروع بازی» را بزنید
۲. نوع بازی را انتخاب کنید
۳. مقدار شرط را انتخاب کنید (یا بدون شرط)
۴. صبر کنید تا حریف پیدا شود

🎲 بازی‌ها:
• سنگ کاغذ قیچی: کلاسیک و سریع
• دوز: بازی فکری روی صفحه ۳x۳
• حدس عدد: عدد بین ۱-۱۰۰ را حدس بزنید
• جنگ اعداد: مقایسه کارت‌های تصادفی

💰 سیستم شرط‌بندی:
• اعتبار اولیه: ۱۰۰۰ سکه
• برنده تمام شرط را می‌برد
• در صورت مساوی شرط برگشت می‌خورد
• می‌توانید بدون شرط هم بازی کنید

موفق باشید! 🍀
"""
    await message.reply(help_msg)

# ============================================
# سیستم مچ‌میکینگ
# ============================================
async def match_players(bot):
    global waiting_queue
    
    if len(waiting_queue) < 2:
        return
    
    to_remove = []
    
    for i in range(len(waiting_queue)):
        if i in to_remove:
            continue
        
        for j in range(i + 1, len(waiting_queue)):
            if j in to_remove:
                continue
            
            p1_info = waiting_queue[i]
            p2_info = waiting_queue[j]
            
            if p1_info[1] == p2_info[1] and p1_info[2] == p2_info[2]:
                p1_id, game_type, bet, p1_msg_id = p1_info
                p2_id, _, _, p2_msg_id = p2_info
                
                user1 = db.get_user(p1_id)
                user2 = db.get_user(p2_id)
                
                if bet > 0:
                    user1['coins'] -= bet
                    user2['coins'] -= bet
                    db.save_data()
                
                game = create_game(game_type, p1_id, p2_id, bet)
                active_games[f"{p1_id}-{p2_id}"] = game
                
                db.set_in_game(p1_id, True, game_type, p2_id, bet)
                db.set_in_game(p2_id, True, game_type, p1_id, bet)
                
                to_remove.extend([i, j])
                
                game_names = {'rps': 'سنگ کاغذ قیچی', 'tictactoe': 'دوز', 'guess': 'حدس عدد', 'war': 'جنگ اعداد'}
                
                start_msg = f"""
🎮 بازی شروع شد!

🎯 بازی: {game_names.get(game_type, '')}
💰 شرط: {bet} سکه
👤 حریف شما پیدا شد!

"""
                
                if game_type == 'rps':
                    start_msg += "لطفاً انتخاب خود را انجام دهید:"
                    try:
                        await bot.send_message(p1_id, start_msg, keyboard=rps_keyboard())
                        await bot.send_message(p2_id, start_msg, keyboard=rps_keyboard())
                    except:
                        pass
                elif game_type == 'tictactoe':
                    start_msg += f"نوبت بازیکن {p1_id} است (❌)"
                    try:
                        await bot.send_message(p1_id, start_msg + game.display_board(), keyboard=tictactoe_keyboard(game))
                        await bot.send_message(p2_id, start_msg + game.display_board())
                    except:
                        pass
                elif game_type == 'guess':
                    start_msg += f"نوبت بازیکن {p1_id} است\nیک عدد بین ۱ تا ۱۰۰ حدس بزنید!"
                    try:
                        await bot.send_message(p1_id, start_msg)
                        await bot.send_message(p2_id, start_msg.replace(p1_id, p2_id))
                    except:
                        pass
                elif game_type == 'war':
                    start_msg += "کارت‌ها توزیع شدند! بازی به صورت خودکار انجام می‌شود..."
                    try:
                        await bot.send_message(p1_id, start_msg)
                        await bot.send_message(p2_id, start_msg)
                    except:
                        pass
                    
                    await play_number_war(bot, game)
                
                break
    
    if to_remove:
        waiting_queue = [q for idx, q in enumerate(waiting_queue) if idx not in to_remove]
        for uid, _, _, _ in [waiting_queue[i] for i in to_remove if i < len(waiting_queue)]:
            db.set_waiting(uid, False)

# ============================================
# هندلرهای اختصاصی بازی‌ها
# ============================================
@bot.on_callback_query('rps_')
async def rps_move_callback(query):
    user_id = query.peer_id.user_id
    user = db.get_user(user_id)
    
    if not user['in_game'] or user['current_game'] != 'rps':
        await query.answer("❌ این بازی متعلق به شما نیست!", alert=True)
        return
    
    choice_map = {'rps_rock': 'سنگ', 'rps_paper': 'کاغذ', 'rps_scissors': 'قیچی'}
    choice = choice_map.get(query.data)
    
    game_key = None
    game = None
    for key, g in active_games.items():
        if isinstance(g, RockPaperScissors) and (user_id == g.player1 or user_id == g.player2):
            game_key = key
            game = g
            break
    
    if not game:
        await query.answer("❌ بازی پیدا نشد!", alert=True)
        return
    
    game.make_move(user_id, choice)
    await query.answer(f"✅ انتخاب شما: {choice}", alert=False)
    
    opponent = game.player2 if user_id == game.player1 else game.player1
    opponent_user = db.get_user(opponent)
    
    if game.choices['player1'] and game.choices['player2']:
        winner = game.determine_winner()
        await game.end_game(bot, winner)
        
        db.set_in_game(user_id, False)
        db.set_in_game(opponent, False)
        
        if game_key in active_games:
            del active_games[game_key]
        
        await query.edit_message("🎮 بازی به پایان رسید!\nنتایج را بررسی کنید.")

@bot.on_callback_query('ttt_')
async def ttt_move_callback(query):
    user_id = query.peer_id.user_id
    user = db.get_user(user_id)
    
    if not user['in_game'] or user['current_game'] != 'tictactoe':
        await query.answer("❌ این بازی متعلق به شما نیست!", alert=True)
        return
    
    game_key = None
    game = None
    for key, g in active_games.items():
        if isinstance(g, TicTacToe) and (user_id == g.player1 or user_id == g.player2):
            game_key = key
            game = g
            break
    
    if not game:
        await query.answer("❌ بازی پیدا نشد!", alert=True)
        return
    
    if user_id != game.current_player:
        await query.answer("❌ نوبت شما نیست!", alert=True)
        return
    
    position = int(query.data.split('_')[1])
    
    if not game.make_move(user_id, position):
        await query.answer("❌ حرکت نامعتبر!", alert=True)
        return
    
    await query.edit_message(f"بازی دوز\n\n{game.display_board()}\n\nنوبت: بازیکن {game.current_player}")
    
    if game.winner:
        await game.end_game(bot, game.winner)
        db.set_in_game(user_id, False)
        db.set_in_game(game.opponent if user_id == game.player1 else game.player1, False)
        if game_key in active_games:
            del active_games[game_key]
        return
    
    opponent = game.player2 if user_id == game.player1 else game.player1
    try:
        await bot.send_message(opponent, f"نوبت شماست!\n\n{game.display_board()}", keyboard=tictactoe_keyboard(game))
    except:
        pass

@bot.on_callback_query('cancel_game')
async def cancel_game_callback(query):
    user_id = query.peer_id.user_id
    user = db.get_user(user_id)
    
    if not user['in_game']:
        await query.answer("❌ شما در بازی نیستید!", alert=True)
        return
    
    game_key = None
    game = None
    for key, g in active_games.items():
        if user_id == g.player1 or user_id == g.player2:
            game_key = key
            game = g
            break
    
    if game:
        opponent = game.player2 if user_id == game.player1 else game.player1
        
        if game.bet > 0:
            db.update_coins(opponent, game.bet * 2)
        
        db.add_game_result(opponent, True)
        db.add_game_result(user_id, False)
        
        db.set_in_game(user_id, False)
        db.set_in_game(opponent, False)
        
        if game_key in active_games:
            del active_games[game_key]
        
        try:
            await bot.send_message(opponent, f"🚫 حریف شما انصراف داد!\nشما برنده شدید! 💰 {game.bet * 2} سکه دریافت کردید.")
        except:
            pass
    
    await query.edit_message("❌ شما از بازی انصراف دادید.")

@bot.on_message('🔢')
async def guess_number_handler(message):
    user_id = message.peer_id.user_id
    user = db.get_user(user_id)
    
    if not user['in_game'] or user['current_game'] != 'guess':
        return
    
    game_key = None
    game = None
    for key, g in active_games.items():
        if isinstance(g, GuessNumber) and (user_id == g.player1 or user_id == g.player2):
            game_key = key
            game = g
            break
    
    if not game:
        return
    
    if user_id != game.current_player:
        await message.reply("❌ نوبت شما نیست!")
        return
    
    try:
        guess = int(message.text)
    except:
        await message.reply("❌ لطفاً یک عدد وارد کنید!")
        return
    
    result = game.make_guess(user_id, guess)
    
    if result == "correct":
        await message.reply(f"🎉 تبریک! عدد درست را حدس زدید!\nعدد هدف: {game.target_number}")
        await game.end_game(bot, user_id)
        db.set_in_game(user_id, False)
        db.set_in_game(game.player2 if user_id == game.player1 else game.player1, False)
        if game_key in active_games:
            del active_games[game_key]
    elif result == "out_of_guesses":
        winner = game.player2 if user_id == game.player1 else game.player1
        await message.reply(f"😔 فرصت‌های شما تمام شد!\nعدد هدف: {game.target_number}")
        await game.end_game(bot, winner)
        db.set_in_game(user_id, False)
        db.set_in_game(game.player2 if user_id == game.player1 else game.player1, False)
        if game_key in active_games:
            del active_games[game_key]
    elif result:
        remaining = game.max_guesses - len(game.guesses['player1']) - len(game.guesses['player2'])
        await message.reply(f"{result}\n\nتعداد حدس‌های باقی‌مانده: {remaining}\n\nنوبت حریف شماست.")
        
        opponent = game.player2 if user_id == game.player1 else game.player1
        try:
            await bot.send_message(opponent, f"نوبت شماست!\n\nحدس حریف: {guess}\n{result}\n\nتعداد حدس‌های باقی‌مانده: {remaining}")
        except:
            pass

async def play_number_war(bot, game):
    await asyncio.sleep(2)
    
    for round_num in range(len(game.cards_p1)):
        winner = game.play_round(round_num)
        await asyncio.sleep(0.5)
    
    if game.winner is None:
        p1_wins = sum(1 for r in game.rounds if r[0] > r[1])
        p2_wins = sum(1 for r in game.rounds if r[1] > r[0])
        if p1_wins > p2_wins:
            game.winner = game.player1
        elif p2_wins > p1_wins:
            game.winner = game.player2
        else:
            game.winner = 'draw'
    
    await game.end_game(bot, game.winner)
    
    db.set_in_game(game.player1, False)
    db.set_in_game(game.player2, False)
    
    game_key = f"{game.player1}-{game.player2}"
    if game_key in active_games:
        del active_games[game_key]

# ============================================
# اجرای ربات
# ============================================
if __name__ == '__main__':
    print("🤖 ربات بازی‌های ۲ نفره در حال اجراست...")
    print("لطفاً API_ID، API_HASH و BOT_TOKEN را در کد تنظیم کنید.")
    bot.start()
