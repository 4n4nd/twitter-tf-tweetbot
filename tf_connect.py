import logging
import os
import requests
import numpy as np
from PIL import Image
from io import BytesIO

from configuration import Configuration
import tf_connect

# Set up logging
_LOGGER = logging.getLogger(__name__)


def create_request(array):
    return '{"instances": %s}' % array


def image_downloader(image_url, auth=None):
    _LOGGER.debug("Downloading image from url: %s", image_url)
    response = requests.get(image_url, auth=auth)
    pil_image = Image.open(BytesIO(response.content))
    return pil_image


def image_to_array(pil_image, shape=None):
    _LOGGER.debug("Converting Image to np array")
    img_array = np.array(pil_image)
    if shape:
        img_array = img_array.reshape(shape)

    img_array = img_array / (255.0)
    return img_array


def tf_request(server_url, image_url, auth=None, image_resolution: tuple = (300, 300)):

    # Download the image using the given url and resize it to the specified resolution
    input_image = image_downloader(image_url, auth).resize(image_resolution)

    # Convert the image to a pixel np array and then create a list
    image_array = [image_to_array(input_image).tolist()]
    # print(image_array)

    # Create a string request from the array to send it to the tensorflow model
    new_request = create_request(str(image_array))

    print(new_request)

    # Post the request to the tensorflow serving api
    _LOGGER.debug("Sending request to tensorflow model serving host (url: %s)", server_url)
    response = requests.post(server_url, new_request)
    _LOGGER.debug("TF Server response: %s", str(response.json()))
    response.raise_for_status()

    # Prediction response from the api
    prediction_value = 1 - response.json()["predictions"][0][0]

    # return the list of predictions
    return [prediction_value]


def process_output(prediction_list: list):
    """
    prediction_list = [is_not_fedora]
    so 1 is false and 0 is true
    """
    # find the index with the highest value of likelihood
    # max_index = prediction_list.index(max(prediction_list))
    # is_fedora = bool(max_index)
    if prediction_list[0] > float(os.getenv("FLT_FEDORA_FOUND_THRESHOLD", "0.95")):
        return "I found a Red Hat Fedora!"

    return "No Red Hat Fedora found :("
