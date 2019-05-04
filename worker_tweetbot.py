import asyncio
import os
import logging
import time
import tornado.ioloop
import tornado.web
import tornado
from requests_oauthlib import OAuth1
from peony import PeonyClient

import tf_connect
from configuration import Configuration

# Set up logging
_LOGGER = logging.getLogger(__name__)

if os.getenv("FLT_DEBUG_MODE", "False") == "True":
    logging_level = logging.DEBUG  # Enable Debug mode
else:
    logging_level = logging.INFO
# Log record format
logging.basicConfig(format="%(asctime)s:%(levelname)s: %(message)s", level=logging_level)

LOAD_TESTING_MODE = False
# If set to true, will not send requests to twitter (to send messages or tweets)
# it will still receive requests and run the whole tensorflow loop
if os.getenv("FLT_LOAD_TESTING_MODE", "False") == "True":
    LOAD_TESTING_MODE = True

# create the client using the api keys
CLIENT = PeonyClient(
    consumer_key=Configuration.CONSUMER_KEY,
    consumer_secret=Configuration.CONSUMER_SECRET,
    access_token=Configuration.ACCESS_TOKEN,
    access_token_secret=Configuration.ACCESS_TOKEN_SECRET,
)
AUTH = OAuth1(
    Configuration.CONSUMER_KEY,
    Configuration.CONSUMER_SECRET,
    Configuration.ACCESS_TOKEN,
    Configuration.ACCESS_TOKEN_SECRET,
)

TF_SERVER_URL = Configuration.TF_SERVER_URL

CURRENT_USER_ID = None
TWEET_REQUEST_COUNT = 0

loop = asyncio.get_event_loop()


async def post_tweet_reply(to_tweet_id, reply_string):
    """ Post a reply to the specified tweet """
    if reply_string:
        post_response = await CLIENT.api.statuses.update.post(
            status=str(reply_string),
            in_reply_to_status_id=to_tweet_id,
            auto_populate_reply_metadata="true",
        )
        _LOGGER.debug("Response: %s", str(post_response))


async def getting_started():
    """This is just a demo of an async API call."""
    user = await CLIENT.user
    _LOGGER.info("I am @%s", str(user.screen_name))
    return user


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    async def post(self):
        tweet = tornado.escape.json_decode(self.request.body)
        reply_string = "Invalid tweet"
        user_mentions_list = []
        try:
            for user_mention in tweet["entities"]["user_mentions"]:
                user_mentions_list.append(user_mention["id_str"])
        except KeyError as excep:
            _LOGGER.error("Tweet did not mention me")
            raise

        if (
            CURRENT_USER_ID in user_mentions_list  # check if user was mentioned
            and tweet["user"]["id_str"] != CURRENT_USER_ID  # check if it our own tweet
            and "retweeted_status" not in tweet  # check if it was a retweet
        ):

            _LOGGER.info("Tweet received from user: %s", tweet["user"]["screen_name"])
            tweet_id = tweet["id_str"]

            if "media" in tweet["entities"] and tweet["entities"]["media"][0]["type"] == "photo":
                image_url = tweet["entities"]["media"][0]["media_url_https"]

                # process image and get response from tf model
                prediction_list = tf_connect.tf_request(TF_SERVER_URL, image_url, AUTH)
                reply_string = tf_connect.process_output(prediction_list)
                reply_string = reply_string + " Likelihood:" + str(prediction_list[0])
                _LOGGER.info(
                    " %s, Image:(%s), Reply %s",
                    tweet["user"]["screen_name"],
                    image_url,
                    reply_string,
                )
                # if load testing don't send the message to twitter
                if LOAD_TESTING_MODE:
                    # Simulate the dalay you would get after you post the tweet
                    await asyncio.sleep(0.3)
                else:
                    start = time.time()
                    await post_tweet_reply(tweet_id, reply_string)
                    end = time.time()
                    _LOGGER.debug("Request took %s seconds", str(end - start))
                global TWEET_REQUEST_COUNT
                TWEET_REQUEST_COUNT += 1
                _LOGGER.info("Processed %s tweets", str(TWEET_REQUEST_COUNT))

        self.write(reply_string)


def make_app():
    _LOGGER.info("Initializing Tornado Web App")
    return tornado.web.Application([(r"/", MainHandler)])


if __name__ == "__main__":
    CURRENT_USER_ID = loop.run_until_complete(getting_started())["id_str"]
    _LOGGER.info("My user id: %s", CURRENT_USER_ID)
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
