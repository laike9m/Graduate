import os
import json
from datetime import datetime, timedelta
from pprint import pprint

import requests
from pymongo.son_manipulator import SONManipulator

from icommon import *


def is_q_col(collection_name):
    return collection_name.endswith('_q')


def is_a_col(collection_name):
    return collection_name.endswith('_a')


def q_col(tid):
    # get question collection name
    return tid + '_q'


def a_col(tid):
    # get answer collection name
    return tid + '_a'


def a_to_q(collection_name):
    assert collection_name.endswith('_a')
    return collection_name[:-1] + 'q'


def q_to_a(collection_name):
    assert collection_name.endswith('_q')
    return collection_name[:-1] + 'a'


def get_time_string(t):
    return t.strftime("%Y-%m-%d %H:%M:%S")


def now_string():
    return datetime.now().strftime("%H:%M:%S")


def get_datetime_full_string(time_string):
    """
    :param time_string: 2016-01-01 04:35:45
    """
    return datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")


def get_datetime_hour_min_sec(time_string):
    """
    :param time_string: 04:35:45
    :return: datetime(now.year, now.month, now.day, 4, 35, 45)

    如果来的 time_string 正好接近跨天,比如 23:59,则datetime.now()的date很可能是
    真实 date+1d,故需要考虑这种特殊情况
    """
    actual_time = datetime.strptime(time_string, "%H:%M:%S").time()
    now = datetime.now()
    now_day, now_time = now.date(), now.time()
    if actual_time < now_time:  # 同一天
        return datetime.combine(now_day, actual_time)
    else:  # 跨天!!
        return datetime.combine(now_day - timedelta(1), actual_time)


def get_datetime_day_month_year(time_string):
    """
    :param time_string: 2016-01-01
    :return: datetime(2016, 1, 1, 0, 0, 0)
    """
    year, month, day = time_string.split('-')
    return datetime(int(year), int(month), int(day), 0, 0, 0)


def validate_config(config=None):
    import json
    import requests
    config = config if (config and isinstance(config, dict)) else \
             json.load(open(dynamic_config_file, encoding='utf-8'))

    if 'topics' not in config:
        raise LackConfig("Lack topics")

    # check topics are valid
    for topic in config['topics']:
        code = requests.get('https://www.zhihu.com/topic/' + topic).status_code
        if code == 404:
            raise InvalidTopicId
        assert code == 200

    if 'restart' not in config:
        raise LackConfig("Lack restart")

    if 'fetch_new' not in config:
        raise LackConfig("Lack fetch_new")

    assert config['restart'] == False or config['restart'] == True
    return True


def validate_cookie(cookie_file):
    """
    :param cookie_file: file path of cookie
    :return: True for valid, False for invalid
    """
    session = requests.Session()
    if os.path.isfile(cookie_file):
        with open(cookie_file) as f:
            cookies = f.read()
            cookies_dict = json.loads(cookies)
            session.cookies.update(cookies_dict)
            res = session.get('https://www.zhihu.com')
            session.close()
            return '首页' in res.text
    else:
        raise IOError("no such cookie file:" + cookie_file)


def dict_equal(dict_more_key, dict_less_key):
    try:
        for key in dict_less_key:
            if dict_more_key[key] != dict_less_key[key]:
                print("unequal key: " + key)
                pprint(dict_more_key[key])
                pprint(dict_less_key[key])
                return False
    except KeyError:
        return False

    return True


def list_of_dict_equal(list_of_dict_more_key, list_of_dict_less_key):
    from collections import Iterable
    if not isinstance(list_of_dict_more_key, Iterable) or \
        not isinstance(list_of_dict_less_key, Iterable):
        raise Exception("not iterable")
    # deprecated function
    pass


def config_smtp_handler(smtp_handler):
    if 'mailgun_username' in os.environ:
        smtp_handler.username, smtp_handler.password = \
            os.environ['mailgun_username'], os.environ['mailgun_password']
    else:
        with open(smtp_config_file, 'rt') as f:
            smtp_config = json.load(f)
            smtp_handler.username, smtp_handler.password = \
                smtp_config['username'], smtp_config['password']


def interpolate(useraction_list):
    index = 0
    LEN = len(useraction_list)
    while index < LEN:
        if useraction_list[index].time is None:
            nonetime_start = index
            while index < LEN and useraction_list[index].time is None:
                index += 1
            nonetime_end = index  # [nonetime_start, nonetime_end)
            if 0 < nonetime_start and nonetime_end < LEN:
                start_time = useraction_list[nonetime_start-1].time
                end_time = useraction_list[nonetime_end].time
                period = end_time - start_time
                length = nonetime_end - nonetime_start + 1
                for i in range(nonetime_start, nonetime_end):
                    useraction_list[i] = \
                        UserAction(start_time + period*(i+1-nonetime_start)/length,
                                   useraction_list[i].aid,
                                   useraction_list[i].uid,
                                   useraction_list[i].acttype)
            elif nonetime_end < LEN:
                # start 就是0, 都设成 endtime
                for i in range(nonetime_start, nonetime_end):
                    useraction_list[i] = \
                        UserAction(useraction_list[nonetime_end].time,
                                   useraction_list[i].aid,
                                   useraction_list[i].uid,
                                   useraction_list[i].acttype)
            elif nonetime_start > 0:
                # end=LEN, 都设成 starttime
                for i in range(nonetime_start, nonetime_end):
                    useraction_list[i] = \
                        UserAction(useraction_list[nonetime_start-1].time,
                                   useraction_list[i].aid,
                                   useraction_list[i].uid,
                                   useraction_list[i].acttype)
            else:
                # TODO: 如果全部都没有时间,怎么办
                raise Exception('no time: ' + str(useraction_list))
        else:
            index += 1


def acttype2str(acttype) -> str:
    """
    不需要 str2acttype, 因为不需要 json -> DB
    :param acttype:
    :return: string representation
    """
    assert acttype != 0
    actions = []
    for i in range(6):
        if (acttype >> i) % 2 == 1:  # ith bit is one
            actions.append(action_table[1 << i])
    return ','.join(actions)


class MyEncoder(json.JSONEncoder):
    """save to json"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, (Enum, TimeRange)):
            return str(obj)

        return json.JSONEncoder.default(self, obj)


# http://api.mongodb.org/python/current/examples/custom_type.html#automatic-encoding-and-decoding
# SONManipulator is deprecated
# http://api.mongodb.org/python/current/changelog.html#sonmanipulator-changes
def transform_incoming(son):
    """save to mongodb"""
    if isinstance(son, list):
        for i, item in enumerate(son):
            son[i] = transform_incoming(item)
    else:
        for (key, value) in son.items():
            if isinstance(value, RelationType):
                son[key] = str(value)
            elif isinstance(value, TimeRange):
                son[key] = value.dump()
            elif isinstance(value, dict) or isinstance(value, list):
                son[key] = transform_incoming(value)
    return son


def transform_outgoing(son):
    """read from mongodb"""
    if isinstance(son, list):
        for i, item in enumerate(son):
            son[i] = transform_outgoing(item)
    else:
        for (key, value) in son.items():
            if key == 'reltype':
                son[key] = match[value]
            elif key == 'time' and isinstance(value, dict):
                son[key] = TimeRange(value['start'], value['end'])
            elif isinstance(value, dict) or isinstance(value, list):
                son[key] = transform_outgoing(value)
    return son


def is_upvote(action: UserAction):
    acttype = action.acttype
    return True if acttype & 0b001000 else False


def is_comment(action: UserAction):
    acttype = action.acttype
    return True if acttype & 0b010000 else False


def is_collect(action: UserAction):
    acttype = action.acttype
    return True if acttype & 0b100000 else False


def is_answer(action: UserAction):
    acttype = action.acttype
    return True if acttype & 0b000100 else False

"""
O(nlgn) Solution
http://www.geeksforgeeks.org/longest-monotonically-increasing-subsequence-size-n-log-n/
"""
def longestIncreasingSubsequence(nums):
    if not nums or len(nums) <= 1:
        return nums

    tailIndices = [0] * len(nums)  # record tail element of active lists
    prevIndices = [-1] * len(nums)
    length = 1

    for i, num in enumerate(nums[1:], 1):
        if num < nums[tailIndices[0]]:
            tailIndices[0] = i
        elif num >= nums[tailIndices[length-1]]:
            prevIndices[i] = tailIndices[length-1]
            tailIndices[length] = i
            length += 1
        else:
            pos = GetCeilIndex(nums, tailIndices, -1, length-1, num)
            prevIndices[i] = tailIndices[pos-1]
            tailIndices[pos] = i

    result = []
    i = tailIndices[length-1]
    index_list = []
    while i >= 0:
        index_list.append(i)
        result.append(nums[i])
        i = prevIndices[i]

    index_list.reverse()
    return list(reversed(result)), index_list


def GetCeilIndex(A, T, l, r, key):
   while r - l > 1:
      m = int(l + (r - l)/2)
      if A[T[m]] >= key:
         r = m
      else:
         l = m

   return r


def avg_time(start, end):
    delta = end - start
    return start + delta / 2


def timerange2datetime(t: Union[datetime, TimeRange]):
    """
    在fill_question_follower 里需要把 timerange 转换成 datetime
    """
    if isinstance(t, datetime):
        return t

    if not any([t.start, t.end]):
        raise Exception("start and end are both none")
    elif t.start is None:
        return t.end - timedelta(seconds=10)
    elif t.end is None:
        return t.start + timedelta(seconds=10)
    else:
        return avg_time(t.start, t.end)


__all__ = [
    'a_col', 'q_col', 'get_time_string', 'now_string',
    'get_datetime_day_month_year', 'get_datetime_hour_min_sec',
    'get_datetime_full_string', 'validate_config', 'validate_cookie',
    'dict_equal', 'is_a_col', 'is_q_col', 'config_smtp_handler', 'interpolate',
    'acttype2str', 'MyEncoder', 'a_to_q', 'q_to_a', 'transform_incoming',
    'transform_outgoing', 'is_upvote', 'is_comment', 'is_collect', 'is_answer',
    'longestIncreasingSubsequence', 'avg_time', 'timerange2datetime'
]