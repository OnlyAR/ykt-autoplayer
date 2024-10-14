import time
import unittest
import config

from src.engine import Engine


class TestLogin(unittest.TestCase):
    def test_scan_login(self):
        engine = Engine(base_url=config.base_url)
        engine.login()
        self.assertEqual(engine.driver.current_url, engine.course_url)

    def test_auto_login(self):
        engine = Engine(base_url=config.base_url, show_browser=True)
        engine.login(auto=True)
        self.assertEqual(engine.driver.current_url, engine.course_url)
        time.sleep(300)