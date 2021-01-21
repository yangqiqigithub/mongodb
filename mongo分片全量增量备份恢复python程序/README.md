# 前提条件
备份工具会接入mongo服务的路由，然后备份整个集群。为了保证备份时，服务器正常工作，该工具在设计时要求：每个节点必须是副本集，且从节点可用。
# 使用方法
##### 找到仲裁节点（或其它安装mongodb的主机），作为备份机，并检查和安装依赖
安装python（一般是Linux默认安装好的）  
检测是否安装python：python --version
(centos6.5默认的2.6.6版本即可，该工具的python版本为2.7，不支持3.x)
#### 安装脚本依赖环境
直接执行 autoInstall.sh  可自动安装
##### 安装pymongo
```
下载地址：https://pypi.org/project/pymongo/#files
Tar zxvf pymongo-3.2.2.tar.gz
cd  pymongo-3.2.2"
python setup.py install
```
##### 安装 pyasn1
```
下载地址：https://pypi.org/project/pyasn1/#files
tar zxvf pyasn1-0.4.4.tar.gz
cd pyasn1-0.4.4
python setup.py install
```
##### 将下述两个文件放到备份机的同一目录下
mongos_backup.conf  （需要修改参数）
在Linux修改的时候确定都修改正确
并且从windows上传输上去的话，检查不要有类似 ^M等字样   

mongos_backup_from_secondary.py  （需要可执行权限）  
##### 修改参数（只需修改mongos_backup.conf）
```
[base-options]
mongo_bin_dir=/usr/local/mongodb/bin   #mongodb安装目录，即二进制文件目录
full_backup_dir=/usr/local/mongodb/backup/full   #全备目录
inc_backup_dir=/usr/local/mongodb/backup/inc   #增备目录
backup_start_date=2016-01-01  #指定备份开始日期（只需第一次使用时才指定）

[mongos-options]
mongos_ip=10.1.1.1    #路由地址
mongos_port=20000     #路由端口
 
[config-server-options]
config_ip=10.1.1.1    #配置服务器地址，一般有3个任选一个
config_port=10000     #配置服务器端口，与config_ip对应的端口
```
##### 运行方式
全备和增备均是对整个集群操作，通过路由实现

```
python full_mongos_backup_from_secondary
python inc_mongos_backup_from_secondary
```
##### 定时任务
编辑 crontab –e，增加两行
```
0     2  *  *  1  python  全路径/full_mongos_backup_from_secondary
0  2  *  *  2,3,4,5,6,0  python 全路径/inc_mongos_backup_from_secondary 
```
解释：
第一行：每周一的凌晨2点进行一次全备；（具体时间可调）
第二行：除周一外每天的凌晨2点进行一次增备；