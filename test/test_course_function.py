import json
import unittest

import config
from src.engine import Engine


class TestCourseFunction(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(config.base_url, show_browser=True)
        self.engine.login(auto=True)

    def test_get_course_list(self):
        courses = self.engine.api_list_courses()
        self.assertGreater(len(courses), 0)
        print(json.dumps(courses, indent=4, ensure_ascii=False))

    def test_api_get_course_contents(self):
        name = config.course_name
        course_info = next(filter(lambda x: x["course_name"] == name, self.engine.api_list_courses()))
        contents = self.engine.api_get_course_contents(course_info)
        print(json.dumps(contents, indent=4, ensure_ascii=False))
        self.assertGreater(len(contents), 0)

    def test_get_course_contents(self):
        name = config.course_name
        course_info = next(filter(lambda x: x["course_name"] == name, self.engine.api_list_courses()))
        contents = self.engine.get_course_contents(course_info)
        print(json.dumps(contents, indent=4, ensure_ascii=False))
        self.assertGreater(len(contents), 0)

    def test_get_course_details(self):
        name = config.course_name
        course_info = next(filter(lambda x: x["course_name"] == name, self.engine.api_list_courses()))
        contents = self.engine.get_course_details(course_info)
        print(json.dumps(contents, indent=4, ensure_ascii=False))
        self.assertGreater(len(contents), 0)