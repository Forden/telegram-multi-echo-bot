import ssl

from aiogram import Bot, Dispatcher, types
from aiohttp import web

import config

bot = Bot(token='', parse_mode='HTML', validate_token=False)
dp = Dispatcher(bot=bot)


@dp.message_handler()
async def echo(msg: types.Message):
    txt = msg.html_text + f'\nsent from @{(await bot.me).username}'
    await bot.send_message(msg.from_user.id, txt)


async def execute(req: web.Request) -> web.Response:
    token = req.match_info['token']
    with dp.bot.with_token(token, validate_token=True):
        upds = [types.Update(**(await req.json()))]
        await dp.process_updates(upds)
    return web.Response()


async def startup(app: web.Application):
    resp = await dp.bot.session.get('https://api.ipify.org')
    ip = await resp.text()
    for i in config.tokens:
        with dp.bot.with_token(i, validate_token=True):
            await dp.bot.delete_webhook()
            url = f'https://{ip}:8443/webhook/{i}'
            await dp.bot.set_webhook(url, certificate=open(config.WEBHOOK_SSL_CERT, 'r'))


if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(config.WEBHOOK_SSL_CERT, config.WEBHOOK_SSL_PRIV)
    app = web.Application()
    app.on_startup.append(startup)
    app.add_routes([web.post('/webhook/{token}', execute)])
    web.run_app(app, port=8443, host='0.0.0.0', ssl_context=context)
