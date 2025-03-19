import asyncio
import logging
from multiprocessing.process import parent_process

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.methods import DeleteWebhook
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import requests
from pprint import pprint

TOKEN = '7676339418:AAFVRgzwY264w8OtcA5p6zpyWhy1IMd-gGo'

logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        'Привет! Отправьте ID игрока в формате: <code>1234567890</code> и я предоставлю информацию о нем', parse_mode='HTML')


@dp.message()
async def filter_messages(message: Message):
    try:
        if message.text.isdigit():
            #БАЗОВАЯ ИНФОРМАЦИЯ
            account_id = message.text
            headers = {'accept': 'application/json', }
            params = {'limit': 20, }
            match_params = {'limit': 1, }
            hero_params = {'having': 30 }

            #АПИ-ЗАПРОСЫ
            base_info = requests.get(f'https://api.opendota.com/api/players/{account_id}/', headers=headers)
            wl_info = requests.get(f'https://api.opendota.com/api/players/{account_id}/wl', headers=headers,params=params)
            total_wl = requests.get(f'https://api.opendota.com/api/players/{account_id}/wl', headers=headers)
            mathes = requests.get(f'https://api.opendota.com/api/players/{account_id}/matches', headers=headers,params=match_params)
            heroes = requests.get(f'https://api.opendota.com/api/players/{account_id}/heroes', headers=headers,params=hero_params)
            hero_id_name = requests.get(f'https://api.opendota.com/api/heroes', headers=headers)

            #
            data_base_info = base_info.json()
            data_wl_info = wl_info.json()
            data_total_wl = total_wl.json()
            data_matches = mathes.json()
            heroes_matches = heroes.json()
            heroes_list = hero_id_name.json()

            #ПОЛУЧЕНИЕ БАЗОВОЙ ИНФЫ ОБ АККАУНТЕ
            pprint(data_base_info)
            st_id = data_base_info['profile']['account_id']
            name = data_base_info['profile']['personaname']
            avatar = data_base_info['profile']['avatarfull']
            profile_url = data_base_info['profile']['profileurl']
            rank = data_base_info.get('rank_tier', 0)

            rank_names = {
                10: "Herald",
                20: "Guardian",
                30: "Crusader",
                40: "Archon",
                50: "Legend",
                60: "Ancient",
                70: "Divine",
                80: "Immortal"
            }

            if rank:
                rank_group = (rank // 10) * 10
                rank_stars = rank % 10

                rank_name = rank_names.get(rank_group, "Unknown")
                rank_display = f"{rank_name} {rank_stars}" if rank_group < 80 else rank_name

            #ПОЛУЧЕНИЕ ВИНРЕЙТА 20 КРАЙНИХ ИГР
            pprint(data_wl_info)
            win = data_wl_info['win']
            lose = data_wl_info['lose']
            try:
                winrate = win / (win + lose) * 100
            except:
                winrate = 0

            #ПОЛУЧЕНИЕ ОБЩЕГО ВИНРЕЙТА
            pprint(data_total_wl)
            total_wins = data_total_wl['win']
            total_loses = data_total_wl['lose']
            total_games = total_wins + total_loses
            try:
                total_winrate = total_wins / (total_wins + total_loses) * 100
                if total_winrate > 50:
                    emoji = '🟢'
                else:
                    emoji = '🔴'
            except:
                total_winrate = 0
                emoji = '🟠'


            #ПОЛУЧЕНИЕ ПОСЛЕДНЕГО МАТЧА
            pprint(data_matches)
            try:
                kills = data_matches[0]['kills']
                deaths = data_matches[0]['deaths']
                assists = data_matches[0]['assists']
            except:
                kills = 0
                deaths = 0
                assists = 0

            last = {hero['id']: hero['localized_name'] for hero in heroes_list}

            last_hero = [last.get(hero['hero_id']) for hero in data_matches]

            #ПОЛУЧЕНИЕ СТАТИСТИКИ ПО ГЕРОЯМ
            hero_names = {hero["id"]: hero["localized_name"] for hero in heroes_list}

            filtered_heroes = [{"hero_name": hero_names.get(hero["hero_id"], "Unknown"), "games": hero["games"], "win": hero["win"]} for hero in heroes_matches]

            top_heroes = sorted(filtered_heroes, key=lambda x: x['games'], reverse=True)[:5]

            heroes_text = "\n".join(f"<b>{hero['hero_name']}</b> | <b>Игры:</b> <code>{hero['games']}</code> | <b>Побед:</b> <code>{hero['win']}</code>" for hero in top_heroes)

            #СОЗДАНИЕ ТЕКСТА СООБЩЕНИЯ
            text = (
                f"<b>{name} | {emoji} {int(total_winrate)}% WR</b>\n\n"
                f"Rank Tier:  <code>{rank_display}</code>\n"
                f"Total matches:  <code>{total_games} (🔺{total_wins} 🔻{total_loses})</code>\n"
                f"Last 20 games winrate:  <code>{int(winrate)}%</code>\n"
                f"Last match KDA:  <code>{last_hero} | {kills}/{deaths}/{assists}</code>\n"
                f"Account id:  <code>{st_id}</code>\n\n"
                f"Most played heroes:  <code>\n{heroes_text}</code>\n"
            )

            #СОЗДАНИЕ КЛАВИАТУРЫ
            builder = InlineKeyboardBuilder()
            button1 = types.InlineKeyboardButton(text="Steam profile", url=profile_url)
            builder.row(button1)

            #ОТПРАВКА СООБЩЕНИЯ
            await bot.send_photo(chat_id=message.chat.id, photo=avatar, caption=text, parse_mode="HTML", reply_markup=builder.as_markup())
    except:
        await message.answer('ID не найден. Отправьте ID в формате: <code>1234567890</code>', parse_mode='HTML')


async def main():
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
