import logging
import os
import random

from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App


logging.basicConfig(level='INFO')
logging.info('Logging now setup.')

app = App(
    token=os.environ.get("USER_OATH_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


def _is_text(event):
    return (event['type'] == 'message'
            and event.get('text'))


def _is_channel_or_dm(event):
    return event['channel_type'] in ('group', 'im')


def _is_not_self(event):
    return event.get('bot_id') != 'B02GSLZ7TGA'


@app.event("message")
def respond(client, event, logger):

    if _is_text(event) and _is_channel_or_dm(event) and _is_not_self(event):

        seed = random.choice(range(200))
        logger.info(f"Seed: {seed}")

        if seed == 1:
            try:
                client.chat_postMessage(
                    text='',
                    channel=event['channel'],
                    thread_ts=event.get('thread_ts') or event['ts'],
                    reply_broadcast=True,
                    blocks=[
                    {
                        "type": "image",
                        "image_url": "https://c.tenor.com/DP615vqUzeAAAAAC/ace-attorney-phoenix-wright.gif",
                        "alt_text": "OBJECTION!"
                    }
                ]
                )

            except Exception as e:
                logger.error(f"Error objecting: {e}")
