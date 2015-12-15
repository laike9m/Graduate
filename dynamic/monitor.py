# coding: utf-8

"""
定期爬话题页面
"""

import ezcf

from config.dynamic_config import topics
from task import *
from model import Question


class TopicMonitor:

    PREFIX = "http://www.zhihu.com/topic/"

    def __init__(self, client, queue):
        self.client = client
        self.task_queue = queue
        self.Topics = [
            client.Topic(self.PREFIX+tid) for tid in topics
        ]

    def detect_new_question(self):
        """
        爬取话题页面，寻找新问题
        :return:
        """
        for Topic in self.Topics:
            for q in Topic.questions:
                if q.id == Question.get_latest_question(Topic.id):
                    break
                else:
                    self.task_queue.append(FetchNewAnswer(q))

