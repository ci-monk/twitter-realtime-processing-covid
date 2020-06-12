# -*- coding: utf-8 -*-

import tweepy
from time import sleep
from tweepy import Stream
from json import dumps, loads
from datetime import datetime
from kafka import KafkaProducer
from http.client import IncompleteRead
from tweepy.streaming import StreamListener
from typing import Callable, NoReturn, Text
from urllib3.exceptions import ProtocolError

# ==============================================================================
# GLOBAL
# ==============================================================================

consumer_key = 'mLhqSwCo0QzPetvyqXnuaqv9M'
consumer_secret = 'HcOsJycgN9u8IKqct6k7OvTMR6Fjb0bfx1Y6AMOtOgxmtsdqOK'
access_token = '1254380788281495552-QtJYhKhY8N9TKrsP8Z5ZNwYgZ31PY5'
access_token_secret = '1vODLDbWXaY4UoMEqSWTvlQDK0nwXvHpZn1SkifhhpZ4d'
broker, topico = "localhost:9092", "dados-tweets"
producer = KafkaProducer(bootstrap_servers=[broker])

# ==============================================================================
# CLASS
# ==============================================================================

class TwitterListener(StreamListener):

  def on_connect(self) -> NoReturn:
    print("You are now connected to the Twitter streaming API.")

  def on_data(self, data: Text) -> NoReturn:
    try:
      parsed = loads(data)
      if "extended_tweet" in parsed:
        text = parsed["extended_tweet"]["full_text"]
      text = parsed["text"]
      tweet = dumps({
        "user_name": parsed["user"]["screen_name"],
        "followers": parsed["user"]["followers_count"],
        "friends": parsed["user"]["friends_count"],
        "text": text,
        "data_collection": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      })
      print("Send message to Kafka Producer...")
      producer.send(topico, value=tweet.encode("utf-8"))
      print("Sleeping 3 seconds...")
      sleep(3)
    except BaseException as error:
      print(f"BaseException Twitter On Data - {error}")
    except Exception as error:
      print(f"Exception Twitter On Data - {error}")
    except ProtocolError as error:
      print(f"ProtocolError Twitter On Data - {error}")
    else:
      return True

  def on_error(self, status_code) -> bool:
    if status_code == 420:
      print(f"Returning False on_data method in case rate limit occurs")
      return False
    print(f"Error received in kafka producer - {status_code}")
    return True

  def on_timeout(self) -> bool:
    print(f"Twitter timeout...")
    return True

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
listener = TwitterListener()

if producer.bootstrap_connected():
  while True:
    try:
      stream = Stream(
        api.auth,
        listener
      )
      stream.filter(track=["covid", "corona", "pandemic", "covid-19", "virus", "corona virus"])
    except IncompleteRead:
      continue
    except KeyboardInterrupt:
      stream.disconnect()
      break
else:
  print("Failed to connect to service")