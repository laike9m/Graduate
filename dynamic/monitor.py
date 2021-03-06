# coding: utf-8

"""
定期爬话题页面
"""

import logging
import concurrent.futures as cf
from concurrent.futures import ThreadPoolExecutor

import requests
from zhihu.question import Question

from task import *
from manager import QuestionManager
from utils import answer_task_queue
from common import *
if hasattr(os, '_called_from_test'):
    from client_pool import get_client_test as get_client  # don't use proxy
else:
    from client_pool import get_client

logger = logging.getLogger(__name__)


class TopicMonitor:

    def __init__(self):
        self.topics = [
            get_client().topic(TOPIC_PREFIX + tid) for tid in topics
        ]
        if fetch_old:
            self._load_old_question()

        self.executor = ThreadPoolExecutor(max_workers=len(topics))

    @staticmethod
    def _load_old_question():
        # 数据库中已有的 question 加入 task queue, answer 不用管
        logger.info('Loading old questions from database............')

        for question_doc in QuestionManager.get_all_questions():
            if not question_doc['active']:
                continue
            if question_doc['url'].endswith('/'):
                question_doc['url'] = question_doc['url'][:-1] + '?sort=created'
            question_task_queue.append(
                FetchQuestionInfo(tid=question_doc['topic'],
                                  question_doc=question_doc)
            )

        logger.info('Loading old questions from database succeed :)')

    def detect_new_question(self):
        """
        爬取话题页面，寻找新问题
        """
        self.new_questions = set()
        futures = []
        for topic in self.topics:
            futures.append(self.executor.submit(self.execute, topic))
        cf.wait(futures, timeout=60, return_when=cf.ALL_COMPLETED)

    def execute(self, topic):
        tid = str(topic.id)
        it = iter(topic.questions)
        question = next(it)
        latest_ctime = QuestionManager.latest_question_creation_time[tid]
        QuestionManager.set_latest(tid, question.creation_time)

        # latest_ctime is None 代表第一次执行, 此时不抓取新问题
        if latest_ctime is None:
            return

        while question.creation_time > latest_ctime:
            # 已经是 http
            question._url = question.url[:-1] + '?sort=created'
            try:
                if question.deleted:
                    continue

                # 去掉占了多个所选话题的问题
                if question.id in self.new_questions:
                    logger.info("重复话题, 跳过: " + str(question.id))
                    continue
                else:
                    self.new_questions.add(question.id)

                asker = '' if question.author is ANONYMOUS else question.author.id
                QuestionManager.save_question(tid, question._url, question.id,
                                              question.creation_time, asker,
                                              question.title)
                question_task_queue.append(FetchQuestionInfo(tid, question))
            except (TypeError, IndexError):
                logger.warning(question.url)
            finally:
                question = next(it)
