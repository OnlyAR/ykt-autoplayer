import json

import argparse

from loguru import logger

from engine import Engine
import config

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", help="任务选项：login / watch", type=str, default="watch")
    args = parser.parse_args()

    if args.task == "login":
        engine = Engine(base_url=config.base_url)
        engine.login()
    else:
        engine = Engine(base_url=config.base_url, show_browser=False)
        engine.login(auto=True)

        name = config.course_name
        course_info = next(filter(lambda x: x["course_name"] == name, engine.api_list_courses()))
        contents = engine.get_course_details(course_info)

        for content in contents:
            if content["type"] != "video":
                continue
            if content["status"] == "已完成":
                print("已完成", content["name"])
                continue
            logger.info("开始观看\n" + json.dumps(content, indent=2, ensure_ascii=False))
            engine.watch(content["url"])
