import logging
import os
import arrow
import json

from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App
import random
import nltk
from nltk.stem import WordNetLemmatizer
from pluralizer import Pluralizer
import re
import string
from nltk.corpus import stopwords


logging.basicConfig(level='INFO')

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),

)

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('stopwords')

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)
lemmatizer = WordNetLemmatizer()
pluralizer = Pluralizer()
stop_words = set(stopwords.words('english'))


def _clean(text):
    text = re.sub('::skin-tone-\d', '', text)
    text = re.sub('\d+', '', text)
    text = text.replace('_', ' ')

    return text


def prepare_emojis(emojis):
    emoji_dict = {'word': {}, 'phrase': {}}
    letters = set(string.ascii_letters)

    for e in emojis:
        if e in letters or e in stop_words or e.isnumeric():
            continue

        full_phrase_with_hyphens = _clean(e)
        emoji_dict[full_phrase_with_hyphens] = e
        full_phrase = full_phrase_with_hyphens.replace('-', ' ')\
                                              .replace('mans ', '')\
                                              .replace('womans ', '')\
                                              .replace('female', '')\
                                              .replace('male', '')\
                                              .strip()
        emoji_dict[full_phrase] = e

        split = full_phrase.split(' ')
        if len(split) == 1:
            singular = pluralizer.singular(full_phrase)
            emoji_dict['word'][singular] = e

            lemma = lemmatizer.lemmatize(e)
            emoji_dict['word'][lemma] = e
        else:
            cleaned_phrase = re.sub('(arrow )|(point )|( alphabet yellow )', '', full_phrase)
            emoji_dict['phrase'][cleaned_phrase] = e

    emoji_dict['word']['email'] = 'e-mail'

    return emoji_dict


with open('all_emoji.json') as f:
    emojis = prepare_emojis(json.load(f))

with open('last_fired_date.txt') as f:
    next_ = arrow.get(f.readlines()[-1])


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@app.message(":wave:")
def say_hello(message, say):
    user = message['user']
    say(f"Hi there, <@{user}>!")


def _is_text(event):
    return (event['type'] == 'message'
            and event.get('text'))


def _is_channel_or_dm(event):
    return event['channel_type'] in ('group', 'im', 'channel')


def _is_not_self(event):
    return event.get('bot_id') != 'B02GSLZ7TGA'


def _is_objected(event):
    text = event.get('text', '').lower()

    return 'object' in text


def objection(client, event, logger):
    seed = random.choice(range(200))
    logger.info(f"Seed: {seed}")

    if seed == 1 or _is_objected(event):
        try:
            client.chat_postMessage(
                    username="OBJECTION!!",
                    text='',
                    channel=event['channel'],
                    thread_ts=event.get('thread_ts') or event['ts'],
                    icon_url="https://avatars.slack-edge.com/2021-10-06/2574348097219_f005de2129158a0a5e0f_192.png",
                    reply_broadcast=True,
                    blocks=[
                        {
                            "type": "image",
                            "image_url": "https://c.tenor.com/DP615vqUzeAAAAAC/ace-attorney-phoenix-wright.gif",
                            "alt_text": "OBJECTION!!"
                        }
                    ]
            )

        except Exception as e:
            logging.info(f"Error objecting: {e}")


def dk_react(client, event, logger):

    text = event['text'].lower()

    if 'david kenny' in text or 'dk' in text:
        try:
            client.reactions_add(
                name='dk',
                channel=event['channel'],
                timestamp=event['ts'])

        except Exception as e:
            logging.info(f"Error adding DK: {e}")


def dk_cringe(client, event, logger):
    now = arrow.now().floor('day')
    global next_

    if now == next_:
        try:
            logging.info('Firing...')
            client.chat_postMessage(
                    username="OBJECTION!!",
                    text='',
                    channel="C029EGZFNBF",  # nielson
                    icon_url="https://avatars.slack-edge.com/2021-10-06/2574348097219_f005de2129158a0a5e0f_192.png",
                    blocks=[
                        {
                            "type": "image",
                            "image_url": "https://i.imgur.com/b4CtEZl.png",
                            "alt_text": "my kenny-cal romance </3"
                        }
                    ]
            )

        except Exception as e:
            logging.info(f"Error posting DK: {e}")
        next_ = next_.shift(months=1)

    logging.info(f'Will fire next on {next_}')


def in_honor_of_harry(client, event, logger):
    if event.get('user') == 'U029HJEVDA6' or event.get('channel') == 'C03F0BQ9REZ':
        words = nltk.word_tokenize(event['text'].lower())
        emojis_to_add = set()
        skin_tone = str(random.choice([1, 2, 3, 4]))

        lemmas = set()
        for word in words:
            if word.isalnum():
                lemmas.add(lemmatizer.lemmatize(word))
                lemmas.add(lemmatizer.lemmatize(pluralizer.singular(word)))

        for lemma in lemmas:
            if lemma in emojis['word']:
                emoji = emojis['word'][lemma]
                if 'skin_tone' in emoji and skin_tone not in emoji:
                    continue
                emojis_to_add.add(emoji)

        for phrase in emojis['phrase']:
            phrase_tokens = phrase.split(' ')
            emoji = emojis['phrase'][phrase]
            if len(set(phrase_tokens) & set(words)) == len(phrase_tokens):
                if 'skin_tone' in emoji and skin_tone not in emoji:
                    continue
                emojis_to_add.add(emoji)

        try:
            for emoji in emojis_to_add:
                client.reactions_add(
                    name=emoji,
                    channel=event['channel'],
                    timestamp=event['ts'])

        except Exception as e:
            logging.info(f"Error adding reaction: {e}")


@app.event("message")
def respond(client, event, logger):
    if _is_text(event) and _is_channel_or_dm(event) and _is_not_self(event):
        objection(client, event, logger)
        dk_react(client, event, logger)
        dk_cringe(client, event, logger)
        in_honor_of_harry(client, event, logger)

