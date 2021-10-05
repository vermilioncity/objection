import os
import random
from slack_bolt import App

app = App(
    token=os.environ.get("USER_OATH_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


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


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))