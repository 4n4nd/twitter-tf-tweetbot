import hmac, base64, hashlib
import logging
import os
import json
import requests
from flask import Flask, request
from http import HTTPStatus


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
    print("responding to CRC call")
    return json.dumps(response)


@app.route("/webhook", methods=["POST"])
def twitter_event_received():
    event_json = request.get_json()
    print(event_json)

    # Maybe validate the requests here (Check if they are actually from twitter)

    # Send mentions to tweetbot workers, Send dms to chatbot workers
    if "direct_message_events" in event_json.keys():
        for message in event_json["direct_message_events"]:
            # Send this message to chatbot workers
            try:
                requests.post(url=Configuration.CHATBOT_WORKER_URL, data=json.dumps(message))
            except Exception as excep:
                # log error here
                _LOGGER.error(
                    "Error %s while processing the following message %s ", str(excep), str(message)
                )
                # raise excep # don't raise when in production

    if "tweet_create_events" in event_json.keys():
        for tweet in event_json["tweet_create_events"]:
            # Send this tweet to tweetbot workers
            try:
                requests.post(url=Configuration.TWEETBOT_WORKER_URL, data=json.dumps(tweet))
            except Exception as excep:
                # log error here
                _LOGGER.error(
                    "Error %s while processing the following tweet %s ", str(excep), str(tweet)
                )
                # raise excep # don't raise when in production

    return ("", HTTPStatus.OK)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
