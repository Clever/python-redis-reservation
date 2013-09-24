import unittest
import socket
import time
from threading import Timer
import redis as redis_lib
from redis_reservation import *


class ReserveResourceTests(unittest.TestCase):

  def setUp(self):
    self.redis = redis_lib.StrictRedis()

  def test_lock_success(self):
    """ can get a lock using the contextmanager """
    key = 'system-test_system'
    reserve = ReserveResource(self.redis, key, 'test_worker')
    self.assertIsNone(self.redis.get(key))
    with reserve.lock() as lock_status:
      self.assertTrue(lock_status)
      self.assertEqual('{}-{}-{}'.format(socket.gethostname(),
                                         'test_worker',
                                         os.getpid()),
                       self.redis.get(key))
    self.assertIsNone(self.redis.get(key))
     
  def test_lock_fail(self):
    """ fails if there is already a lock using the contextmanager """

    key = 'system-test_system'
    self.redis.set(key, 'MOCK')

    self.assertEqual('MOCK', self.redis.get(key))
    reserve = ReserveResource(self.redis, key, 'test_worker')
    with reserve.lock() as resource_lock:
      self.assertFalse(resource_lock, "reserved lock, while locked by someone else")
    self.assertEqual('MOCK', self.redis.get(key))
    self.redis.delete(key)

  def test_lock_err(self):
    """ contextmanager handles redis errors """

    key = 'system-test_system'
    class FailingRedis:
      def setnx(self, *args, **kwargs):
        raise redis_lib.RedisError("its in the name to fail")
    reserve = ReserveResource(self.redis, key, 'test_worker')
    reserve.redis = FailingRedis()

    with reserve.lock() as resource_lock:
      self.assertEqual(resource_lock.message, "its in the name to fail")
  
  def test_lock_release_on_err(self):
    """ contextmanager releases locks on error in with block """

    key = 'system-test_system'
    reserve = ReserveResource(self.redis, key, 'test_worker')
    
    try:
      with reserve.lock() as resource_lock:
        self.assertEqual('{}-{}-{}'.format(socket.gethostname(),
                                           'test_worker',
                                           os.getpid()),
                         self.redis.get(key))
        raise Exception("error within with")
    except Exception as e:
      self.assertEqual(e.message, 'error within with')
      self.assertFalse(self.redis.get(key))

  def test_lock_wait(self):
    """ can wait for lock to be aquired using contextmanager """

    key = 'system-test_system'
    self.redis.set(key, 'MOCK')
    def delete_lock(key):
      self.redis.delete(key)
    t = Timer(1.0, delete_lock, [key], {})
    t.start()

    reserve = ReserveResource(self.redis, key, 'test_worker')
    reserve.heartbeat_interval = 0.2
    self.assertEqual('MOCK', self.redis.get(key))

    with reserve.lock(wait=True) as lock_status:
      time.sleep(1)  # wait a little bit for the heartbeat to run
      self.assertTrue(lock_status)
      self.assertEqual('{}-{}-{}'.format(socket.gethostname(),
                                         'test_worker',
                                         os.getpid()),
                       self.redis.get(key))
    self.assertIsNone(self.redis.get(key))


if __name__ == '__main__':
  unittest.main()
