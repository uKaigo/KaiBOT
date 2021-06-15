import asyncio
from discord import http


def ack_interaction(bot, interaction_id, interaction_token):
    route = http.Route(
        'POST',
        '/interactions/{interaction_id}/{interaction_token}/callback',
        interaction_id=interaction_id,
        interaction_token=interaction_token,
    )

    payload = {'type': 6}

    return bot.http.request(route, json=payload)


def wait_for_click(bot, message_id, member_id, *, timeout=60):
    async def inner():
        while True:
            event = await bot.wait_for('socket_response', timeout=60)

            if event['t'] != 'INTERACTION_CREATE':
                continue

            payload = event['d']

            await ack_interaction(bot, payload['id'], payload['token'])

            try:
                if payload['message']['id'] != str(message_id):
                    continue

                if payload['member']['user']['id'] != str(member_id):
                    continue
            except KeyError as e:
                continue

            button_id = payload['data']['custom_id']

            return button_id

    return asyncio.wait_for(inner(), timeout=timeout)
