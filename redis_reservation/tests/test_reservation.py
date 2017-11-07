import unittest
import socket
import time
from threading import Timer
import redis as redis_lib
from redis_reservation import *
import signal


class ReserveResourceTests(unittest.TestCase):

  def setUp(self):
    self.redis = redis_lib.StrictRedis()
    self.key_format = 'reservation-{}'

  def test_lock_success(self):
    """ can get a lock using the contextmanager """
    key = 'test_resource'
    redis_key = self.key_format.format(key)

    reserve = ReserveResource(self.redis, key, 'test_worker')
    self.assertIsNone(self.redis.get(redis_key))
    with reserve.lock() as lock_status:
      self.assertTrue(lock_status)
      self.assertEqual('{}-{}-{}'.format(socket.gethostname(),
                                         'test_worker',
                                         os.getpid()),
                       self.redis.get(redis_key))
    self.assertIsNone(self.redis.get(redis_key))
     
  def test_lock_fail(self):
    """ fails if there is already a lock using the contextmanager """

    key = 'test_resource'
    redis_key = self.key_format.format(key)

    self.redis.set(redis_key, 'MOCK')
    self.assertEqual('MOCK', self.redis.get(redis_key))
    reserve = ReserveResource(self.redis, key, 'test_worker')
    with reserve.lock() as resource_lock:
      self.assertFalse(resource_lock, "reserved lock, while locked by someone else")
    self.assertEqual('MOCK', self.redis.get(redis_key))
    self.redis.delete(redis_key)

  def test_lock_err(self):
    """ contextmanager handles redis errors """

    key = 'test_resource'
    class FailingRedis:
      def set(self, *args, **kwargs):
        raise redis_lib.RedisError("its in the name to fail")
    reserve = ReserveResource(self.redis, key, 'test_worker')
    reserve.redis = FailingRedis()

    with reserve.lock() as resource_lock:
      self.assertEqual(resource_lock.message, "its in the name to fail")
  
  def test_lock_release_on_err(self):
    """ contextmanager releases locks on error in with block """

    key = 'test_resource'
    redis_key = self.key_format.format(key)
    reserve = ReserveResource(self.redis, key, 'test_worker')
    
    try:
      with reserve.lock() as resource_lock:
        self.assertEqual('{}-{}-{}'.format(socket.gethostname(),
                                           'test_worker',
                                           os.getpid()),
                         self.redis.get(redis_key))
        raise Exception("error within with")
    except Exception as e:
      self.assertEqual(e.message, 'error within with')
      self.assertFalse(self.redis.get(redis_key))

  def test_lock_wait(self):
    """ can wait for lock to be aquired using contextmanager """

    key = 'test_resource'
    redis_key = self.key_format.format(key)
    self.redis.set(redis_key, "MOCK")
    def delete_lock(key):
      self.redis.delete(redis_key)
    t = Timer(1.0, delete_lock, [key], {})
    t.start()

    reserve = ReserveResource(self.redis, key, 'test_worker')
    reserve.heartbeat_interval = 0.2
    self.assertEqual('MOCK', self.redis.get(redis_key))

    with reserve.lock(wait=True) as lock_status:
      time.sleep(1)  # wait a little bit for the heartbeat to run
      self.assertTrue(lock_status)
      self.assertEqual('{}-{}-{}'.format(socket.gethostname(),
                                         'test_worker',
                                         os.getpid()),
                       self.redis.get(redis_key))
    self.assertIsNone(self.redis.get(redis_key))


class TestSignalHandling(unittest.TestCase):
  def setUp(self):
    self.redis = redis_lib.StrictRedis()
    self.key_format = 'reservation-{}'
    self.exited_context = False
    self.called_previous_sigterm_handler = False
  def tearDown(self):
    # make sure we exited the ctx manager and called previous signal handler
    self.assertTrue(self.exited_context is True)
    self.assertTrue(self.called_previous_sigterm_handler is True)

  def my_awesome_sigterm_handler(self, signum, frame):
    self.called_previous_sigterm_handler = True

  def test_sigterm(self):
    key = 'test_resource'
    redis_key = self.key_format.format(key)
    signal.signal(signal.SIGTERM, self.my_awesome_sigterm_handler)

    reserve = ReserveResource(self.redis, key, 'test_worker')
    self.assertIsNone(self.redis.get(redis_key))
    with reserve.lock() as lock_status:
      os.kill(os.getpid(), signal.SIGTERM)
    self.exited_context = True
    self.assertIsNone(self.redis.get(redis_key))

if __name__ == '__main__':
  unittest.main()
