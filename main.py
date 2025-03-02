from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
import asyncio

API_TOKEN = 'TOKEN'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Adminlar user_id larini ro'yxat ko'rinishida saqlash
admins = [805370890, 8069567136]  # Admin user_id lar ro'yxati

# Ma'lumotlar bazasini sozlash
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        fullname TEXT
    )
''')
conn.commit()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ''
    fullname = f"{first_name} {last_name}".strip()

    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, name, fullname) VALUES (?, ?, ?)
    ''', (user_id, first_name, fullname))
    conn.commit()

    await message.answer("✅ OBUNA BO'LDINGIZ\n"
                         "✅ BOTIMIZDA HECH QANDAY REKLAMALAR YO'Q 😊")
    await message.answer("🎬 IZLAYOTGAN KINO KODINI YUBORING 👇👇👇")

# '/cancel' buyruqni sozlash
@dp.message(Command("ortga"))
async def cancel_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id not in admins:  # Admin user_id ni o'zgartiring
        await message.reply("XATOLIK!\n 🎬 IZLAYOTGAN KINO KODINI YUBORING 👇👇👇")
        return
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Bekor qilinadigan jarayon yo'q.")
        return

    await state.clear()
    await message.answer("✅ Jarayon bekor qilindi.")


@dp.message(Command("xabar"))
async def start_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id not in admins:  # Admin user_id ni o'zgartiring
        await message.reply("XATOLIK!\n 🎬 IZLAYOTGAN KINO KODINI YUBORING 👇👇👇")
        return

    await message.answer("Foydalanuvchilarga yuboriladigan xabarni kiriting yoki bekor qilish uchun /ortga buyrug'ini ishlating")
    await state.set_state(BroadcastState.waiting_for_message)

@dp.message(BroadcastState.waiting_for_message, F.text)
async def broadcast_message(message: types.Message, state: FSMContext):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()

    text_to_send = message.text
    success_count = 0
    fail_count = 0

    for user in users:
        user_id = user[0]
        try:
            await bot.send_message(chat_id=user_id, text=text_to_send)
            success_count += 1
        except Exception:
            fail_count += 1

    await message.answer(f"Xabarni qabul qilganlar: {success_count} ta\n"
                         f"Botdan chiqib ketganlar: {fail_count} ta")
    await state.clear()

# Yordam va statistika kabi boshqa komandalar qolgan qismi xuddi oldingi kabi.

# '/yordam' command handler
@dp.message(Command("yordam"))
async def send_help(message: types.Message):
    await message.answer("Kerakli kinoni yuklab olish uchun kino kodini botga yuboring\n"
                         "Masalan: 1234\n"
                         "\n\n"
                         "UzKinos-2024")


# '/statistika' command handler
@dp.message(Command("stat"))
async def send_statistics(message: types.Message):
    if message.from_user.id not in admins:  # Admin user_id ni o'zgartiring
        await message.reply("XATOLIK!\n 🎬 IZLAYOTGAN KINO KODINI YUBORING 👇👇👇")
        return
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]

    cursor.execute('SELECT fullname FROM users')
    users = cursor.fetchall()
    users_list = '\n'.join([f"- {user[0]}" for user in users])

    await message.answer(f"Foydalanuvchilar soni: {user_count} ta \n\n Foydalanuvchilar ro'yxati: \n {users_list}")


# Forward post handler
@dp.message()
async def forward_post(message: types.Message):
    try:
        if message.forward_from_chat:
            original_post_id = message.forward_from_message_id
            original_post_id2 = original_post_id + 1000
            await message.answer(f"KINO KODI: {original_post_id2}\n")
        else:
            post_id = message.text.strip().rsplit('/', 1)[-1]
            post_id1 = int(post_id)
            post_id = post_id1 - 1000
            await bot.copy_message(chat_id=message.chat.id, from_chat_id=-1002400640841, message_id=post_id)
            await message.answer(f"✅ MUVAFFAQIYATLI YUKLANDI. \n"
                                 f"✅ REKLAMASIZ BOT: @UZKINOSBOT")
    except Exception as e:
        await message.reply("🚫XATOLIK!\nBUNDAY MA'LUMOT TOPILMADI. KODNI QAYTADAN TEKSHIRIB KO'RING")
        await message.answer("🎬 IZLAYOTGAN KINO KODINI YUBORING 👇")




# Main function to run the bot
async def main():
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())
