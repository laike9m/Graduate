import os
from collections import deque

task_queue = deque()

# zhihu-analysis folder
ROOT = os.path.dirname(os.path.dirname(__file__))
test_cookie = os.path.join(ROOT, 'cookies/zhuoyi.json')
dynamic_config_file = os.path.join(ROOT, 'dynamic/config/dynamic_config.json')
logging_config_file = os.path.join(ROOT, 'dynamic/config/logging_config.json')
TOPIC_PREFIX = "https://www.zhihu.com/topic/"
QUESTION_PREFIX = "https://www.zhihu.com/question/"
FETCH_FOLLOWER = 1
FETCH_FOLLOWEE = 2

if os._called_from_test:
    TASKLOOP_INTERVAL = 5
    MAX_TASK_EXECUTION_TIME = 4
    FETCH_QUESTION_INTERVAL = 5
else:
    TASKLOOP_INTERVAL = 60
    MAX_TASK_EXECUTION_TIME = 55
    FETCH_QUESTION_INTERVAL = 60


if not os.path.exists(os.path.join(ROOT, 'dynamic/logs')):
    os.mkdir(os.path.join(ROOT, 'dynamic/logs'))


class EndProgramException(Exception):
    pass


class InvalidTopicId(Exception):
    pass


class LackConfig(Exception):
    pass

class NoSuchActivity(Exception):
    pass

class FetchTypeError(Exception):
    pass