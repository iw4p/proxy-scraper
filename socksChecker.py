import aiohttp
import random
from aiohttp_socks import ProxyConnector
import asyncio
import datetime
import psutil
import os
import ssl
import time
import pytz
import json


def clear_console():
    if psutil.WINDOWS:
        return os.system("cls")
    else:
        return os.system("clear")


urls = ['https://ulbwa.suicide.today/',
        'https://suicide.today/']

allProxys = []
fastProxys = []
slowProxys = []
checked = []

clear_console()

print("   _____            _        _____  _____ _               _             \n"  # noqa
      "  / ____|          | |      | ____|/ ____| |             | |            \n"  # noqa
      " | (___   ___   ___| | _____| |__ | |    | |__   ___  ___| | _____ _ __ \n"  # noqa
      "  \___ \ / _ \ / __| |/ / __|___ \| |    | '_ \ / _ \/ __| |/ / _ \ '__|\n"  # noqa
      "  ____) | (_) | (__|   <\__ \___) | |____| | | |  __/ (__|   <  __/ |   \n"  # noqa
      " |_____/ \___/ \___|_|\_\___/____/ \_____|_| |_|\___|\___|_|\_\___|_|   \n\n"  # noqa
      "- - - - - - - - - - - - - - - - - - - - - - - "
      "- - - - - - - - - - - - - \n\n"
      "Скрипт создан @ulbwaa для @rfoxxxyshit\n\n"
      "- - - - - - - - - - - - - - - - - - - - - - - "
      "- - - - - - - - - - - - - \n"
      )

if random.choice([True, False]):
    print('Наши другие проекты доступны по следующим ссылкам:\n\n'
          'https://github.com/Ulbwaa\n'
          'https://github.com/rfoxxxyshit\n'
          'https://github.com/rfoxxxy\n\n'
          '- - - - - - - - - - - - - - - - - - - - - - -'
          ' - - - - - - - - - - - - - \n'
          )

time.sleep(5)

try:
    with open('proxy.txt', 'r') as f:
        proxys = f.read().split('\n')
        print('Прокси успешно загружены. Всего прокси '
              f'загружено: {len(proxys)}.\n\n'
              'Начинаю проверку...',
              end=('\n\n- - - - - - - - - - - - - - - - - - -'
                   ' - - - - - - - - - - - - - - - - - \n\n'))
except FileNotFoundError:
    print('Файл proxy.txt не найден. Пожалуйста, создайте его и поместите '
          'туда\n\nсписок ваших прокси для обеспечения '
          'работоспособности скрипта.',
          end='\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - '
              '- - - - - - - - \n\n'
          )
    exit(-1)


def write():
    with open('allProxys.txt', 'w') as file:
        file.write("\n".join(allProxys))

    with open('fastProxys.txt', 'w') as file:
        file.write("\n".join(fastProxys))

    with open('slowProxys.txt', 'w') as file:
        file.write("\n".join(slowProxys))


def get_time():
    time = datetime.datetime.now(pytz.timezone('Europe/Moscow'))

    if len(str(time.hour)) < 2:
        hour = f'0{time.hour}'
    else:
        hour = time.hour

    if len(str(time.minute)) < 2:
        minutes = f'0{time.minute}'
    else:
        minutes = time.minute

    if len(str(time.second)) < 2:
        seconds = f'0{time.second}'
    else:
        seconds = time.second

    return f'{hour}:{minutes}:{seconds}'


async def checkProxys():
    working = skipped = 0

    for proxy in proxys:
        if proxy.split(':')[0] in checked:
            skipped += 1
            continue

        url = random.choice(urls)
        print(f'[{get_time()}] Проверяю {proxy} '
              f'(Подключение к {url.split("/")[2]}):',
              end='\n')
        connector = ProxyConnector.from_url(f'socks5://{proxy}',
                                            limit=200,
                                            limit_per_host=200,
                                            force_close=True,
                                            enable_cleanup_closed=True,
                                            verify_ssl=False)

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get('https://ramziv.com/ip', timeout=5) \
                        as response:
                    ip = await response.text()

                async with session.get(
                        f'http://www.geoplugin.net/json.gp?{ip}',
                        timeout=5
                ) as response:
                    country = json.loads(
                        await response.text()
                    )[
                        'geoplugin_countryName'
                    ]

                start_time_stamp = time.time()

                async with session.get(url, timeout=5):
                    await session.close()

                ping = round((time.time() - start_time_stamp) * 1000)
                allProxys.append(proxy)

                if ping <= 1100:
                    fastProxys.append(proxy)
                else:
                    slowProxys.append(proxy)

                write()

                working += 1
                checked.append(proxy.split(':')[0])
                print(f'[{get_time()}] Успешное подключение! '
                      f'(Задержка: {ping} ms, IP-Адрес: {ip}), '
                      f'страна: {country})',
                      end=('\n\n- - - - - - - - - - - - - - - - - - - - - - '
                           '- - - - - - - - - - - - - - \n\n'))
        except Exception:
            skipped += 1
            checked.append(proxy.split(':')[0])
            print(f'[{get_time()}] Неудачное подключение.',
                  end=('\n\n- - - - - - - - - - - - - - - - '
                       '- - - - - - - - - - '
                       '- - - - - - - - - - \n\n'))

    print(f'Проверка завершена! Нашлись {working} работоспособных прокси.'
          f' {skipped} прокси были пропущены.\n'
          f'Все работоспособные прокси сохранены в файле allProxys.txt.\n'
          'Быстрые прокси сохранены в файле fastProxys.txt\n'
          'Медленные прокси сохранены в файле slowProxys.txt',
          end=('\n\n- - - - - - - - - - - - - - - - '
               '- - - - - - - - - - '
               '- - - - - - - - - - \n\n'))

    exit(0)


try:
    asyncio.run(checkProxys())
except RuntimeError:
    exit(0)
except KeyboardInterrupt:
    exit(0)