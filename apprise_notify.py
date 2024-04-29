# -*- coding: utf-8 -*-
import sys
import traceback
import time
import base64
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta  

import apprise
import redis
import pytesseract

import pygetwindow as gw
from PIL import ImageGrab

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from time_nlp.TimeNormalizer import TimeNormalizer
from webrequest.HttpRequest import HttpRequest

# 基本路径
base_dir = r'D:\notify_bot'
apprise_config = r'C:\Users\zhanggaojiong\AppData\Roaming\Apprise\apprise'
iciba_path_dir = base_dir + r'\iciba'
screenshot_path = base_dir + r'\screenshot'

# redis
redis_ip = 'localhost'
redis_port = 6379
redis_db = 15
redis_pass = ''

# api机器人地址
bot_url = 'http://api.qingyunke.com/api.php?key=free&appid=0&msg={0}'

# iciba每日一词
iciba_url = 'http://open.iciba.com/dsapi/'

# 网络请求实例对象
request = HttpRequest()

# 从时间字符串移除识别错误的常见汉字，手动增加使用过程中由于识别错误多余的文字

strings_to_remove = ['了']

# 从识别的描述中修正“提醒”两个字，防止识别“提醒”两个字识别错误，里面填写一些不常见的识别错误文字，修正为正确的文字，如：把[线]修正为[我]等

fix_tixing_dict = {'提':['堤','碮'],
                   '醒':['恒','瞳','旭'],
                   '晚':['院'],
                   '我':['线']}

# 图片转base64


def get_img_base64(img_path):
    f = open(img_path, 'rb')
    ls_f = base64.b64encode(f.read())
    f.close()
    return "data:image/png;base64," + str(ls_f)[1:].strip('\'')
    # return 'data:image/bmp;base64,Qk0eAgAAAAAAALYAAAAoAAAAEgAAABIAAAABAAgAAAAAAAAAAA DEDgAAxA4AACAAAAAgAAAAFSph/ySn4f8jRGP/mt70/zg1M/9DqMr/YWJg/yZqtf8EAwP/Xouz/5O qpP81Vn7/O4ut/xQqQP8TUJL/TmaU/y9ylv8nWKH/g3Z1/x3d9v+JvNj/LCYk/yQcGf8Nb7T/HUKV /w0bJ/8XW7L/YNT7/7b1/P+Niof/I43F/////wAfFhYVFhUWFhYVFRUVFhUWFR8AABYCBwcYARgJC wQNDQICDQ0NBAAABAIaEQcHCwsNDQICBA0NDQIEAAAEAgcHHg4CCw4eFAIPAg0NAgQAAAQLBwceDg sQEQMJHh4GDQ0CBAAAFQsaGgcRDwULCw8UCQ0CDQsEAAAEAAcREQ4LCQEXDgAAAQIZEAQAABUCGAc RGAAJAxsbDAsKAhkQBAAAFQwYGAcHAAMDAxQUFAodDQIVAAAWHgEYGB4YAwMDHBwDCgYNDRUAABUQ AQEYBx4RFBQCFA8CBAACFQAABAgeAR4RAREZAAAJFA4ADQsVAAAECBkBAR4FHhEFHBwUCgoCAhUAA BUICB4eHgEHHBwcHAMUCgICFQAAFQgIDQEeEwEPAwMUCQkAAgwWAAACCAgIAQETExoAGhcXHg4TGR UAABUGFggZDAUFBQwMEBAMBQ8EBgAAHwQKEhISEhISEhIdEhISHRIfAAA='

# 运行CMD命令


def run_cmd_Popen_fileno(cmd_string):
    """
    执行cmd命令，并得到执行后的返回值，python调试界面输出返回值
    :param cmd_string: cmd命令，如：'adb devices'
    :return:
    """
    import subprocess

    print('运行cmd指令：{}'.format(cmd_string))
    return subprocess.Popen(cmd_string, shell=True, stdout=None, stderr=None).wait()

# Send a funny image you found on the internet to a colleague:
# apprise -vv --title 'Agile Joke' \
#         --body 'Did you see this one yet?' \
#         --attach https://i.redd.it/my2t4d2fx0u31.jpg \
#         'mailto://myemail:mypass@gmail.com'

# Easily send an update from a critical server to your dev team
# apprise -vv --title 'system crash' \
#         --body 'I do not think Jim fixed the bug; see attached...' \
#         --attach /var/log/myprogram.log \
#         --attach /var/debug/core.2345 \
#         --tag devteam


# 发送提醒消息


def send_remind_text(title, body, attachs=None):
    # cmd_string = "apprise -vv -t \"{}\" -b \"{}\" --input-format=html".format(title, body)
    cmd_string = "apprise -vv -t \"{}\" -b \"{}\"".format(title, body)
    if attachs != None:
        for attach in attachs:
            cmd_string += " --attach \"" + attach + "\""
    run_cmd_Popen_fileno(cmd_string)


def send_remind_text2(title, body, attachs=None):
    # Create an Apprise instance
    apobj = apprise.Apprise()

    # Create an Config instance
    config = apprise.AppriseConfig()

    # Add a configuration source:
    config.add(apprise_config)

    # Add another...
    # config.add('https://myserver:8080/path/to/config')

    # Make sure to add our config into our apprise object
    apobj.add(config)

    # Now add all of the entries we're intrested in:
    # attach = (
    #     # ?name= allows us to rename the actual jpeg as found on the site
    #     # to be another name when sent to our receipient(s)
    #     'https://i.redd.it/my2t4d2fx0u31.jpg?name=FlyingToMars.jpg',

    #     # Now add another:
    #     '/path/to/funny/joke.gif',
    # )

    # Send your multiple attachments with a single notify call:
    res = apobj.notify(
        title=title,
        body=body,
        attach=attachs,
        body_format='html'
    )
    return res

# 每日iciba提醒任务


def iciba_everyday_job():
    tts_img_path = request.save_iciba_mp3_and_img(iciba_path_dir, iciba_url)
    if tts_img_path[0] == '' or tts_img_path[1] == '':
        time.sleep(5)
        tts_img_path = request.save_iciba_mp3_and_img(
            iciba_path_dir, iciba_url)
    random_second = random.randint(0, 7200)
    print('iciba_everyday_job 延迟秒数：' + str(random_second))
    time.sleep(random_second)
    body = "<body style='height:auto'><img alt='{}' src='{}' /></body>".format(
        tts_img_path[3], get_img_base64(tts_img_path[1]))
    now = datetime.now()
    res = send_remind_text2(tts_img_path[2].split('_')[1], body, [
                            tts_img_path[0], tts_img_path[1]])
    now2 = datetime.now()
    print('iciba_everyday_job 发送耗时：{} 发送结果：{}'.format(
        str((now2 - now).total_seconds()), res))

def get_notift_text():
    # 确定您要获取的窗口名称
    window_name = ['我的iPhone','我的Android手机']
    window = None
    # 获取指定名称的窗口
    for name in window_name:
        windows = gw.getWindowsWithTitle(name)
        if len(windows)<=0:
            continue
        else:
            window = windows[0]
            break

    if window is None:
        return False,'',''
    # 获取窗口的位置和大小
    x, y, width, height = window.left, window.top, window.width, window.height

    x2 = 60
    y2 = 90

    x_right = 20
    y_down = 120

    x = x+x2
    y = y+y2

    # 根据窗口的位置和大小进行截图
    time.sleep(1) # 截图前暂停一下，防止截图模糊造成识别错误
    screenshot = ImageGrab.grab(bbox=(x, y, x + width-x2-x_right, y + height-y2-y_down))

    # 保存截图到指定路径（例如D盘根目录下的screenshot.png）
    # 这个save其实没必要的，只是调试时可以看到你所截的图，便于调整截图位置
    save_path = screenshot_path + "/screenshot" + str(datetime.now().strftime('%Y%m%d%H%M%S')) + str(random.randint(1000, 9999))+".png"
    screenshot.save(save_path)

    if window is not None:
        window.close()

    # 打开本地图片
    # image_path = "D:/screenshot/screenshot2.png"
    # screenshot2 = Image.open(image_path)

    # 使用Tesseract识别截图中的文字
    # custom_config = r'--oem 3 --psm 6'
    custom_config = r'--oem 1 --psm 6'
    recognized_text = pytesseract.image_to_string(screenshot, lang='chi_sim', config=custom_config)

    # 输出识别的文字
    print("识别的文字是：\n", recognized_text)
    recognized_text_arr = recognized_text.split('\n')
    print('recognized_text_arr原始：' + str(recognized_text_arr))
    recognized_text_arr = [''.join(e.split()) for e in recognized_text_arr if e.strip()]
    print('recognized_text_arr去空元素后：' + str(recognized_text_arr))
    if len(recognized_text_arr)<=0:
        print('本次未识别到文字')
        return True,'',''
    print('本次识别到的待提醒文字：' + recognized_text_arr[-1])
    tixing_sentence = fix_notify_desc(recognized_text_arr[-1], fix_tixing_dict)
    print('修正后的待提醒文字：' + tixing_sentence)
    title_body = tixing_sentence.split('提醒')
    if len(title_body)<2:
        return True,title_body[0],''
    return True, '提醒' + title_body[1].replace('我',''), title_body[0]

def is_valid_time(time_str):
    try:
        datetime_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        return True, datetime_obj
    except ValueError:
        return False, None

def remove_strings(main_string, strings_to_remove):
    for string in strings_to_remove:
        main_string = main_string.replace(string, '')
    return main_string

def fix_notify_desc(input_string, fix_tixing_dict):
    # 繁体转简体
    input_string = request.cht_to_chs(input_string)
    # 遍历字典中的键值对
    for key, value_list in fix_tixing_dict.items():
        # 遍历值（数组）中的每个元素
        for value in value_list:
            # 将字符串中与值匹配的字符替换为对应的键
            input_string = input_string.replace(value, key)
    return input_string

def get_datetime(sentence):
    print('时间sentence:' + sentence)
    sentence = remove_strings(sentence, strings_to_remove)
    print('修正后的时间sentence:' + sentence)
    tn = TimeNormalizer(isPreferFuture=False)
    time_dict = tn.parse(sentence, datetime.now())
    timeStr = ''
    if 'error' in time_dict.keys():
        print('本次时间解析出错啦')
        return False,''
    if time_dict['type'] == 'timestamp':
        timeStr = time_dict['timestamp']
    elif time_dict['type'] == 'timedelta':
        time_delta_dict = time_dict['timedelta']
        now = datetime.now()
        delta = timedelta(days=time_delta_dict['year'] * 365 + time_delta_dict['month'] * 30 + time_delta_dict['day'],
                          hours=time_delta_dict['hour'], minutes=time_delta_dict['minute'], seconds=time_delta_dict['second'])
        timeStr = str(now + delta).split('.')[0]
    if timeStr == '':
        print('本次未解析出时间')
        return False,''
    remind_time = datetime.strptime(timeStr, '%Y-%m-%d %H:%M:%S')
    print('remind_time:' + str(remind_time))
    return True,timeStr


redis_store = RedisJobStore(
    host=redis_ip, port=redis_port, db=redis_db, password=redis_pass)
jobstores = {'redis': redis_store}
executors = {
    'default': ThreadPoolExecutor(100),  # 默认线程数
    'processpool': ProcessPoolExecutor(30)  # 默认进程
}
job_defaults = {
    'coalesce': True,
    'max_instances': 30,
    'misfire_grace_time': None
}
scheduler = BackgroundScheduler(
    jobstores=jobstores, executors=executors, job_defaults=job_defaults)

# date: 特定的时间点触发
# interval: 固定时间间隔触发
# cron: 在特定时间周期性地触发
scheduler.add_job(func=iciba_everyday_job, trigger="cron", hour=8, minute=30, jobstore='redis',
                  misfire_grace_time=2*60*60, id='iciba_everyday_job', replace_existing=True)
scheduler.add_job(func=send_remind_text, args=['还房贷', '还房贷'], trigger="cron", day=9, hour=15, minute=0, start_date='2017-10-9',
                  end_date='2032-9-10', jobstore='redis', misfire_grace_time=24*60*60, id='house_loan_everymonth_job', replace_existing=True)
# scheduler.add_job(func=send_remind_text, args=[my_wxid, '\u23f0  还车贷'], trigger="cron", day=15, hour=15, minute=0, start_date='2020-9-15', end_date='2022-9-16', jobstore='redis', misfire_grace_time=24*60*60, id='car_loan_everymonth_job', replace_existing=True)
scheduler.add_job(func=send_remind_text, args=['交房租', '交房租'], trigger="cron", month='2,5,8,11', day=20, hour=15, minute=0,
                  start_date='2020-11-20', end_date='2023-5-21', jobstore='redis', misfire_grace_time=24*60*60, id='room_charge_every3month_job', replace_existing=True)
scheduler.add_job(func=send_remind_text, args=['杨、申签到', '杨、申签到'], trigger="cron", hour=8, minute=0,
                  jobstore='redis', misfire_grace_time=24*60*60, id='sign_in_everyday_job', replace_existing=True)
scheduler.add_job(func=send_remind_text, args=['淘宝签到', '淘宝签到'], trigger="cron", hour=8, minute=0,
                  jobstore='redis', misfire_grace_time=24*60*60, id='tb_sign_in_everyday_job', replace_existing=True)
scheduler.add_job(func=send_remind_text, args=['吃饭', '吃饭'], trigger="cron", day_of_week='0-4', hour=11,
                  minute=42, jobstore='redis', misfire_grace_time=24*60*60, id='lunch_everyday_job', replace_existing=True)
# scheduler.add_job(func=add_date_job, trigger="interval", seconds=1)
# scheduler.add_job(job, 'interval', seconds=1)
scheduler.start()

# 连接到 Redis
redis_conn = redis.Redis(host=redis_ip, port=redis_port, db=redis_db, password=redis_pass)

# 通过我的手机QQ自然语言输入识别
try:
    while True:
        try:
            time.sleep(1)
            text_list = get_notift_text()
            if not text_list[0]:
                print(str(datetime.now()) + ' 没有识别到指定窗口')
                continue
            if len(text_list)<3:
                print(str(datetime.now()) + ' 不是完整的提醒语句')
                continue
            if '提醒' not in text_list[1]:
                print(str(datetime.now()) + ' 不是提醒语句')
                continue
            if not text_list[2] or text_list[2].isspace():
                print(str(datetime.now()) + ' 时间描述为空')
                continue
            date_time_result = get_datetime(text_list[2])
            if not date_time_result[0]:
                print(str(datetime.now()) + ' 时间解释不正确或未解析出时间')
                continue
            date_time_string = date_time_result[1]
            dt_result = is_valid_time(date_time_string)
            if not dt_result[0]:
                print(str(datetime.now()) + ' 时间无效')
                continue
            title = text_list[1].replace('提醒','')
            if redis_conn.exists(title):
                print(str(datetime.now()) + ' 已存在该提醒')
                continue
            print(str(datetime.now()) + ' 识别到的时间为：' + str(dt_result[1]))
            if dt_result[1]<datetime.now():
                print(str(datetime.now()) + ' 时间已过期')
                continue
            # 获取当前时间  
            current_time = datetime.now()
            # 计算未来时间和当前时间之间的差值（使用relativedelta得到更精确的年份差）  
            year_difference = relativedelta(dt_result[1], current_time).years
            if  year_difference >= 1:
                print(str(datetime.now()) + ' 时间超过一年')
                continue

            scheduler.add_job(func=send_remind_text, args=[title,date_time_string], trigger="date", run_date=dt_result[1], jobstore='redis')
            redis_conn.setex(title, 300, date_time_string)
            print(str(datetime.now()) + ' 已设置提醒：' + date_time_string + ' ' + title)
            send_remind_text('['+title+']已设置','已设置：' + date_time_string + ' 提醒 ' + title)
        except Exception as e:
            # 如果发生异常，捕获它并记录日志
            exc_type, exc_value, exc_traceback = sys.exc_info()  
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)  
            tb_str = ''.join(tb_lines)
            print(f"An error occurred: {e}")
            print(f"Traceback:\n{tb_str}")
            continue
except KeyboardInterrupt:
    sys.exit()