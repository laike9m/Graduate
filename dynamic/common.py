import os
from datetime import timedelta, datetime
from collections import deque

import ezcf
from config.dynamic_config import topics, ANSWER_TASKLOOP_INTERVAL, \
                MAX_ANSWER_TASK_EXECUTION_TIME, FETCH_QUESTION_INTERVAL, restart, \
                fetch_new, fetch_old, QUESTION_INACTIVE_INTERVAL, \
                ANSWER_INACTIVE_INTERVAL, MAX_NO_ANSWER_INTERVAL, \
                QUESTION_TASKLOOP_INTERVAL
from zhihu import ANONYMOUS
from zhihu.acttype import ActType

FOLLOW_QUESTION = ActType.FOLLOW_QUESTION
ANSWER_QUESTION = ActType.ANSWER_QUESTION

answer_task_queue = deque()
question_task_queue = deque()
cancelled_questions = set()

# zhihu-analysis folder
ROOT = os.path.dirname(os.path.dirname(__file__))
test_cookie = os.path.join(ROOT, 'cookies/zhuoyi.json')
dynamic_config_file = os.path.join(ROOT, 'dynamic/config/dynamic_config.json')
logging_config_file = os.path.join(ROOT, 'dynamic/config/logging_config.json')
smtp_config_file = os.path.join(ROOT, 'dynamic/config/smtp_config.json')
TOPIC_PREFIX = "http://www.zhihu.com/topic/"
QUESTION_PREFIX = "http://www.zhihu.com/question/"
QUESTION_PREFIX_S = "https://www.zhihu.com/question/"
FETCH_FOLLOWER = 1
FETCH_FOLLOWEE = 2
MAX_NO_ANSWER_INTERVAL = timedelta(minutes=MAX_NO_ANSWER_INTERVAL)
QUESTION_INACTIVE_INTERVAL = timedelta(hours=QUESTION_INACTIVE_INTERVAL)
ANSWER_INACTIVE_INTERVAL = timedelta(hours=ANSWER_INACTIVE_INTERVAL)
epoch = datetime(1970, 1, 1)

if hasattr(os, '_called_from_test'):
    ANSWER_TASKLOOP_INTERVAL = 5
    QUESTION_TASKLOOP_INTERVAL = 5
    MAX_TASK_EXECUTION_TIME = 4
    FETCH_QUESTION_INTERVAL = 5
    topics = {"1234": "test_topic"}
    test_tid = '1234'
    test_tid2 = '5678'
    fetch_old = True
    fetch_new = True


if not os.path.exists(os.path.join(ROOT, 'dynamic/logs')):
    os.mkdir(os.path.join(ROOT, 'dynamic/logs'))
logging_dir = os.path.join(ROOT, 'dynamic/logs')


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