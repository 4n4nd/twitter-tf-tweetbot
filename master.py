import hmac, base64, hashlib
import logging
import json
from flask import Flask, request
from http import HTTPStatus


from configuration import Configuration

app = Flask(__name__)


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
            # Send these to chatbot workers
            pass
    #         loop.run_until_complete(process_message(message))

    return ("", HTTPStatus.OK)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
