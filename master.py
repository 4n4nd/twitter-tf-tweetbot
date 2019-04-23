import hmac, base64, hashlib
import logging
import os
import asyncio
import json
import requests
from flask import Flask, request
from http import HTTPStatus
from peony import PeonyClient

from configuration import Configuration

# Set up logging
_LOGGER = logging.getLogger(__name__)
if os.getenv("FLT_DEBUG_MODE", "False") == "True":
    logging_level = logging.DEBUG  # Enable Debug mode
else:
    logging_level = logging.INFO
# Log record format
logging.basicConfig(format="%(asctime)s:%(levelname)s: %(message)s", level=logging_level)

app = Flask(__name__)

# create the client using the api keys
CLIENT = PeonyClient(
    consumer_key=Configuration.CONSUMER_KEY,
    consumer_secret=Configuration.CONSUMER_SECRET,
    access_token=Configuration.ACCESS_TOKEN,
    access_token_secret=Configuration.ACCESS_TOKEN_SECRET,
)
CURRENT_USER_ID = None
loop = asyncio.get_event_loop()


async def getting_started():
    """This is just a demo of an async API call."""
    user = await CLIENT.user
    _LOGGER.info("I am @%s", str(user.screen_name))
    return user


@app.route("/")
def default_page():
    return "Functional"


# crc validation for the twitter account activity api webhook
@app.route("/webhook", methods=["GET"])
def twitter_crc_validation():

    crc = request.args["crc_token"]

    validation = hmac.new(
        key=bytes(Configuration.CONSUMER_SECRET, "utf-8"),
        msg=bytes(crc, "utf-8"),
        digestmod=hashlib.sha256,
    )
    digested = base64.b64encode(validation.digest())
    response = {"response_token": "sha256=" + format(str(digested)[2:-1])}
    _LOGGER.info("responding to CRC call")
    return json.dumps(response)


@app.route("/webhook", methods=["POST"])
def twitter_event_received():
    event_json = request.get_json()
    _LOGGER.debug("Twitter Event Received: %s ", str(event_json))
    response_string = "None"
    # Maybe validate the requests here (Check if they are actually from twitter)

    # Send mentions to tweetbot workers, Send dms to chatbot workers
    if "direct_message_events" in event_json.keys():
        for message in event_json["direct_message_events"]:
            if (
                message["type"] == "message_create"  # Check if new message
                and str(message["message_create"]["sender_id"])
                != CURRENT_USER_ID  # Check if its your own message
            ):
                # Send this message to chatbot workers
                try:
                    response = requests.post(
                        url=Configuration.CHATBOT_WORKER_URL, data=json.dumps(message)
                    )
                    response_string = response.text
                    response.raise_for_status()
                except Exception as excep:
                    # log error here
                    _LOGGER.error(
                        "Error %s while processing the following message %s ",
                        str(excep),
                        str(message),
                    )
                    return ("{0}".format(response_string), HTTPStatus.INTERNAL_SERVER_ERROR)
                    # raise excep # don't raise when in production

    if "tweet_create_events" in event_json.keys():
        for tweet in event_json["tweet_create_events"]:
            user_mentions_list = []
            for user_mention in tweet["entities"]["user_mentions"]:
                user_mentions_list.append(user_mention["id_str"])

            # Reply to tweet only if the bot was mentioned
            if str(CURRENT_USER_ID) in user_mentions_list:
                # Send this tweet to tweetbot workers
                try:
                    response = requests.post(
                        url=Configuration.TWEETBOT_WORKER_URL, data=json.dumps(tweet)
                    )
                    response.raise_for_status()
                except Exception as excep:
                    # log error here
                    _LOGGER.error(
                        "Error %s while processing the following tweet %s ", str(excep), str(tweet)
                    )
                    return ("{0}".format(response_string), HTTPStatus.INTERNAL_SERVER_ERROR)
                    # raise excep # don't raise when in production

    return ("{0}".format(response_string), HTTPStatus.OK)


if __name__ == "__main__":
    CURRENT_USER_ID = loop.run_until_complete(getting_started())["id_str"]
    print(CURRENT_USER_ID)
    app.run(host="0.0.0.0", debug=False, port=8080)
