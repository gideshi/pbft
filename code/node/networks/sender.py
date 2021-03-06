# -*- coding: utf-8 -*-
import socket
from time import sleep

from luckydonaldUtils.logger import logging

from ..env import NODE_PORT, DATABASE_URL
from ..messages import Message
from ..todo import logger

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

MSG_FORMAT = "ANSWER {length}\n{msg}\n"


def send_message(msg):
    import json
    import requests
    logger.debug(msg)
    assert isinstance(msg, Message)
    data = msg.to_dict()
    data_string = json.dumps(data)
    broadcast(data_string)
    loggert = logging.getLogger("request")
    def print_url(r, *args, **kwargs):
        loggert.info(r.url)
    # end def
    while (True):
        try:
            requests.put(DATABASE_URL, data=data_string, hooks=dict(response=print_url))
            break
        except requests.RequestException as e:
            logger.warning("Failed to report message to db: {e}".format(e=e))
        # end def
        return
# end def


def broadcast(message):
    from ..dockerus import ServiceInfos
    if not isinstance(message, str):
        raise TypeError("Parameter `message` is not type `str` but {type}: {msg}".format(type=type(message), msg=message))
    hosts = ServiceInfos().other_hostnames()
    # msg = MSG_FORMAT.format(length=len(message), msg=message)
    message += "\n"
    msg = "ANSWER " + str(len(message)) + "\n" + message
    logger.debug("Prepared sending to *:{port}:\n{msg}".format(port=NODE_PORT, msg=msg))
    msg = bytes(msg, "utf-8")
    for node_host in hosts:
        sent = -1
        while not sent == 1:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:  # UDP SOCK_DGRAM
                    sock.connect((node_host, NODE_PORT))
                    sock.sendall(msg)
                    logger.log(
                        msg="Sending to {host}:{port} succeeded.".format(host=node_host, port=NODE_PORT),
                        level=(logging.SUCCESS if sent == 0 else logging.DEBUG)
                    )
                    sent = 1
                # end with
            except OSError as e:
                logger.error("Sending to {host}:{port} failed: {e} Retrying...".format(e=e, host=node_host, port=NODE_PORT))
                sleep(0.1)
                sent = 0
            # end try
        # end while
    # end for
# end def