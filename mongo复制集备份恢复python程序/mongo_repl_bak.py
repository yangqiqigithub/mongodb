
import os
import re
import time
import logging
import configparser
import  subprocess
from my_logging import load_my_logging_cfg

def dir_size(dir_abspath):
    '''
     统计目录的大小
    :param dir_absopath:
    :return:
    '''

    cmd="du -sh %s | awk '{print $1}'" %(dir_abspath)
    output=subprocess.getoutput(cmd)
    return  output

def record_log():
    '''
    记录日志的函数 使用方法 record_log().error('错误日志')
    :return:
    '''
    load_my_logging_cfg()
    logger1=logging.getLogger(__name__)
    return logger1

def get_config():

    '''
    用来获取mongo配置的函数
    :return: dict
    '''
    config=configparser.ConfigParser()
    config.sections()
    config.read("config.ini")
    config_dict={
        "db_host":config["default"]["db_host"],
        "db_user":config["default"]["db_user"],
        "db_pwd":config["default"]["db_pwd"],
        "db_authdb":config["default"]["db_authdb"],
        "mongo_home":config["default"]["mongo_home"],
        "dbbak_dir":config["default"]["dbbak_dir"],
        "db_port":config["default"]["db_port"],
        "time_interval":config["default"]["time_interval"]

    }
    return config_dict

def full_bak():
    '''
    全量备份函数 带--oplog
    :return:
    '''
    messages={'status':0,'msg':'','start_time':'','stop_time':''}  #0表示全量备份成功
    now_time=time.strftime("%Y%m%d",time.localtime(time.time())) #20210107-17:14:07
    path = get_config()["dbbak_dir"] + now_time + '/' + 'full'
    if not os.path.exists(path):
        os.makedirs(path)
    dump_cmd="%smongodump --host %s:%s -u %s -p %s --oplog  --authenticationDatabase %s --out %s" % \
        (get_config()["mongo_home"],get_config()["db_host"],get_config()["db_port"],
         get_config()["db_user"],get_config()["db_pwd"],get_config()["db_authdb"],path)
    res=os.system(dump_cmd)
    if res==0:
        oplog_bson_path=path+'/'+'oplog.bson'
        if os.path.isfile(oplog_bson_path):
            oplog_bson_cmd='%sbsondump %s' %(get_config()["mongo_home"],oplog_bson_path)
            output = subprocess.getoutput(oplog_bson_cmd)
            start_time=re.findall('\d+',output)[0] #时间戳
            t=re.findall(r"\d{4}-\d{1,2}-\d{1,2}\w\d{1,2}:\d{1,2}:\d{1,2}", output)[1] #2021-01-11T11:48:20
            stop_time=round(time.mktime(time.strptime(t, '%Y-%m-%dT%X'))) #时间戳
            messages['start_time']=start_time
            messages['stop_time']=stop_time
            msg='Mongodb全量备份成功,备份目录大小为：%s,耗时：%s秒'  %(dir_size(path),int(stop_time)-int(start_time))
            messages['msg'] = msg
            record_log().info(msg)
    else:
        msg='Mongodb 全量备份失败!!'
        messages['status']=1
        messages['msg']=msg
        record_log().error(msg)
    return messages

def ince_bak(start_time):
    '''
    增量备份函数
    增量备份的前提条件是：全量备份成功
    :return:
    '''
    count=1
    while  count < int(24/int(get_config()["time_interval"]))-1:
        #将全量备份结束的时间往前挪几秒，为了数据的完整性，oplog有幂等性，重复执行数据也不会重复
        start_time=int(start_time)-120
        stop_time=int(get_config()["time_interval"])*3600+start_time

        messages={'status': 0, 'msg': ''}  # 0表示备份成功
        now_time=time.strftime("%Y%m%d", time.localtime(time.time()))  # 20210107
        path=get_config()["dbbak_dir"] + now_time +'/'+'incre'+'/'+time.strftime("%Y%m%d_%H_%M_%S",time.localtime(stop_time))
        if not os.path.exists(path):
             os.makedirs(path)
        exec_start_time=round(time.time())
        dump_cmd="%smongodump --host %s:%s -u %s -p %s  --authenticationDatabase %s -d local -c oplog.rs  --query" \
                 " '{ts:{$gte:Timestamp(%s,1),$lte:Timestamp(%s,1)}}' -o  %s" %\
                 (get_config()["mongo_home"],get_config()["db_host"],get_config()["db_port"],
             get_config()["db_user"],get_config()["db_pwd"],get_config()["db_authdb"],start_time,stop_time,path)
        exec_stop_time = round(time.time())

        if messages['status'] == 0: #只有上一次增量备份是成功的才会进行下次的备份
            res = os.system(dump_cmd)
            if res == 0:
                msg = 'Mongodb 第%s次增量备份成功,备份目录大小为：%s,耗时：%s秒' %(count,dir_size(path),int(exec_stop_time)-int(exec_start_time))
                messages['msg'] = msg
                print(msg)
                record_log().info(msg)

            else:
                msg = 'Mongodb 第%s次增量备份失败!!' %(count)
                messages['status'] = 1
                messages['msg'] = msg
                print(msg)
                record_log().error(msg)
        else:
            msg = 'Mongodb 上次（%s次）增量备份失败!!' %(count-1)
            print(msg)
            messages['status'] = 1
            messages['msg'] = msg
            record_log().error(msg)
        count += 1
        start_time=stop_time

def run():
    '''
    启动函数
    :return:
    '''
    print('%s全量备份开始...' %(time.strftime("%Y-%m-%d %X")))
    messages=full_bak()
    print('%s全量备份结束...' % (time.strftime("%Y-%m-%d %X")))
    if messages['status']==0: # 表示全量备份成功 ，可以进行增量备份
        start_time=messages['stop_time'] #增量备份的开始时间就是全量备份的结束时间
        time_interval=int(get_config()["time_interval"])
        print('等待%s小时后增量备份开始...' %(time_interval))
        time.sleep(time_interval*3600)
        print('%s增量备份开始...' % (time.strftime("%Y-%m-%d %X")))
        ince_bak(start_time)
        print('%s增量备份全部结束...' % (time.strftime("%Y-%m-%d %X")))



#run()
























