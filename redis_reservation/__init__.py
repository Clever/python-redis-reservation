from contextlib import contextmanager
from threading import Timer
import threading
from redis import StrictRedis, RedisError
import logging
import socket
import time
import os


class ReserveException(Exception):
  pass


class ReserveResource:
    
  def __init__(self, redis, key, by, lock_ttl=30*60, heartbeat_interval=10*60):
    self.key = 'reservation-{}'.format(key)
    self.val = '{}-{}-{}'.format(socket.gethostname(), by, os.getpid())
    self.lock_ttl = lock_ttl
    self.heartbeat_interval = heartbeat_interval
    self.redis = redis
    self.reserved = False
    self.logger = logging.getLogger(by)  # log with the name of the reserver
    self.heartbeat_thread = None

  @contextmanager
  def lock(self, wait=False):
    try:
      if wait is True:
        yield self.wait_until_reserve()
      else:
        lock = self.reserve()
        if lock is True:
          self.logger.info("RESERVE: successfully reserved {}".format(self.key))
          yield True
        else:
          self.logger.info("RESERVE: System {} already reserved by {}"
                  .format(self.key, self.redis.get(self.key)))
          yield False
    except RedisError as err:
      self.logger.error("RESERVE_ERROR: RedisError during RESERVE/RUN of with ReserveResource.lock")
      self.logger.error(err)
      yield err
    finally:
      try:
        self.release()
      except RedisError as err:
        self.logger.error("RESERVE_ERROR: RedisError during RELEASE "
                "of with ReserveResource.lock", err)

  def reserve(self):
    result = self.redis.set(self.key, self.val, nx=True, ex=self.lock_ttl)
    if result is 1 or result is True:
      self.reserved = True
      self._heartbeat()  # setup heartbeat
      return True  # aquired lock
    return False

  def wait_until_reserve(self):
    """ Keep trying to reserve resource till we get a lock """
    while True:
      self.reserve()
      if self.reserved is True:
        return True
      time.sleep(1)  # check every 1 sec

  def release(self):
    if self.heartbeat_thread:
      # cancel heartbeat thread after waiting for execution finish (if any)
      self.heartbeat_thread.cancel()

    if self.reserved is False:
      return True 

    result = self.redis.delete(self.key)
    self.reserved = False

    if result is 1 or result is True:
      return True
    return False  # lock already gone

  def _set_expiration(self):
    result = self.redis.expire(self.key, self.lock_ttl)
    return result is 1 or result is True
    return False
  
  def _heartbeat(self):
    if self.reserved is False:
      return
    if not (self.heartbeat_interval and self.heartbeat_interval > 0):
      return
    
    self._set_expiration()
    self.heartbeat_thread = Timer(self.heartbeat_interval, self._heartbeat, ())
    self.heartbeat_thread.daemon = True  # don't keep app alive just for this thread
    self.heartbeat_thread.start()
