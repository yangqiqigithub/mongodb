# 脚本的目录结构
```
mongodbbak
├── config.ini 配置文件
├── dbbak.log  日志文件
├── mongo_repl_bak.py 核心代码文件
├── my_logging.py 日志定义文件
└── run.py 运行文件

```
# 使用方法
##### 配置文件配置
```
[default]
db_host = 127.0.0.1
db_port = 28018
db_user = root
db_pwd = xxxxx
db_authdb = admin
time_interval = 3
mongo_home = /mongodb/bin/
dbbak_dir = /mongodb/backup/dbbak/
```
```
time_interval = 3 全量备份完毕后，每隔3小时做一次增量备份
```
##### 运行脚本
```
[mongod@m mongodbbak]$ /usr/local/bin/python3 run.py
2021-01-12 17:41:16全量备份开始...
2021-01-12T17:41:16.940+0800    writing admin.system.users to
2021-01-12T17:41:16.941+0800    done dumping admin.system.users (2 documents)
2021-01-12T17:41:16.941+0800    writing admin.system.roles to
2021-01-12T17:41:16.941+0800    done dumping admin.system.roles (1 document)
2021-01-12T17:41:16.941+0800    writing admin.system.version to
2021-01-12T17:41:16.941+0800    done dumping admin.system.version (2 documents)
2021-01-12T17:41:16.942+0800    writing test.foo to
2021-01-12T17:41:17.093+0800    done dumping test.foo (100009 documents)
2021-01-12T17:41:17.094+0800    writing captured oplog to
2021-01-12T17:41:17.094+0800            dumped 1 oplog entry
[INFO][2021-01-12 10:41:17,119][mongo_repl_bak.py:78]Mongodb全量备份成功,备份目录大小为：3.2M,耗时：10秒
2021-01-12 17:41:17全量备份结束...
等待3小时后增量备份开始...
Mongodb 第1次增量备份成功,备份目录大小为：132K,耗时：0秒
[INFO][2021-01-12 20:10:27,660][mongo_repl_bak.py:116]Mongodb 第1次增量备份成功,备份目录大小为：132K,耗时：1秒
2021-01-12T20:10:27.688+0800    writing local.oplog.rs to
2021-01-12T20:10:27.915+0800    done dumping local.oplog.rs (24 documents)
Mongodb 第2次增量备份成功,备份目录大小为：16K,耗时：0秒
[INFO][2021-01-12 20:10:27,919][mongo_repl_bak.py:116]Mongodb 第2次增量备份成功,备份目录大小为：16K,耗时：3秒
2021-01-12T20:10:27.948+0800    writing local.oplog.rs to
2021-01-12T20:10:28.187+0800    done dumping local.oplog.rs (0 documents)
Mongodb 第3次增量备份成功,备份目录大小为：12K,耗时：0秒
[INFO][2021-01-12 20:10:28,192][mongo_repl_bak.py:116]Mongodb 第3次增量备份成功,备份目录大小为：12K,耗时：2秒
2021-01-12T20:10:28.220+0800    writing local.oplog.rs to
2021-01-12T20:10:28.464+0800    done dumping local.oplog.rs (0 documents)
Mongodb 第4次增量备份成功,备份目录大小为：12K,耗时：0秒
[INFO][2021-01-12 20:10:28,469][mongo_repl_bak.py:116]Mongodb 第4次增量备份成功,备份目录大小为：12K,耗时：1秒
2021-01-12T20:10:28.498+0800    writing local.oplog.rs to
2021-01-12T20:10:28.734+0800    done dumping local.oplog.rs (0 documents)
Mongodb 第5次增量备份成功,备份目录大小为：12K,耗时：0秒
[INFO][2021-01-12 20:10:28,739][mongo_repl_bak.py:116]Mongodb 第5次增量备份成功,备份目录大小为：12K,耗时：2秒
2021-01-12T20:10:28.769+0800    writing local.oplog.rs to
2021-01-12T20:10:28.997+0800    done dumping local.oplog.rs (0 documents)
Mongodb 第6次增量备份成功,备份目录大小为：12K,耗时：0秒
[INFO][2021-01-12 20:10:29,003][mongo_repl_bak.py:116]Mongodb 第6次增量备份成功,备份目录大小为：12K,耗时：1秒
2021-01-12 20:10:29增量备份全部结束...

```

# 脚本编写原理
根据使用--oplog参数得到的oplog.bson文件拿到全量备份的结束时间，作为下一次增量备份的开始时间
##### 创建备份用户
```
db.createUser({user:'backupuser',pwd:'xxxxxx',roles: [{role:'backup',db:'admin'}]})
```
### 备份原理
##### 全量备份整个实例
```
mongodump --host 127.0.0.1:28017 -u backupuser -p xxxxxx --oplog --authenticationDatabase admin -o /mongodb/backup/fullbak/
```
```
--oplog 只适用于整个mongo实例备份，会产生oplog.bson文件，记录备份的开始和结束时间
[root@m full]# bsondump oplog.bson
{"ts":{"$timestamp":{"t":1610422195（开始时间）,"i":1}},"t":{"$numberLong":"3"},"h":{"$numberLong":"6295515218108182872"},"v":2,"op":"n","ns":"","wall":{"$date":"2021-01-12T03:29:55.248Z"},"o":{"msg":"periodic noop"}}
2021-01-12T11:44:19.865+0800（结束时间）	1 objects found
```
全量备份完后的目录结构
```
├── admin
│   ├── system.roles.bson
│   ├── system.roles.metadata.json
│   ├── system.users.bson
│   ├── system.users.metadata.json
│   ├── system.version.bson
│   └── system.version.metadata.json
├── oplog.bson
└── test
    ├── foo.bson
    └── foo.metadata.json

```
##### 增量备份
经测试备份local库下的oplog.rs 集合可以实现增量备份
增量备份的前提是全量备份成功
```
mongodump --host 127.0.0.1:28017 -u backupuser -p xxxxx  --authenticationDatabase admin -d local -c oplog.rs  --query '{ts:{$gte:Timestamp(1610356207,1),$lte:Timestamp(1610356327,1)}}' -o   ./
```
```
--query 备份指定时间范围内的数据
全量备份的结束时间就是第一次增量备份的开始时间
自定义时间间隔，比如每隔2小时备份一次，那么第一次增量备份的结束时间就是第一次增量备份的开始时间再往后推2小时，第一增量备份的结束时间是第二次全量备份的开始时间依次类推
```
增量备份完毕后的目录结构
```
└── local
    ├── oplog.rs.bson
    └── oplog.rs.metadata.json
```
###  恢复的原理
首先进行全量备份的恢复
```
mongorestore --host 127.0.0.1:28017 -u root -p xxxx  --oplogReplay  --authenticationDatabase admin ./fullbak
```
举例如下：
```
[mongod@m full]$ ls
admin  oplog.bson  test
[mongod@m full]$ mongorestore --host 127.0.0.1:28017 -u root -p xxxxx  --oplogReplay  --authenticationDatabase admin ./
2021-01-12T16:06:09.532+0800    preparing collections to restore from
2021-01-12T16:06:09.534+0800    reading metadata for test.foo from test/foo.metadata.json
2021-01-12T16:06:09.549+0800    restoring test.foo from test/foo.bson
2021-01-12T16:06:09.581+0800    no indexes to restore
2021-01-12T16:06:09.581+0800    finished restoring test.foo (10 documents)
2021-01-12T16:06:09.581+0800    restoring users from admin/system.users.bson
2021-01-12T16:06:09.622+0800    restoring roles from admin/system.roles.bson
2021-01-12T16:06:09.702+0800    replaying oplog
2021-01-12T16:06:09.703+0800    done

```
依次进行增量备份的恢复
将oplog.rs.bson 文件拷贝到一个空目录里，然后重命名为oplog.bson
再用如下命令恢复
```
mongorestore --host 127.0.0.1:28017 -u root -p xxx  --oplogReplay  --authenticationDatabase admin ./
```
举例如下：
```
[mongod@m incre]$ cd 20210112_13_25_55/
[mongod@m 20210112_13_25_55]$ ls
local
[mongod@m 20210112_13_25_55]$ cd  local/
[mongod@m local]$ ls
oplog.rs.bson  oplog.rs.metadata.json
[mongod@m local]$ mkdir tt
[mongod@m local]$ mv oplog.rs.bson ./tt/oplog.bson
[mongod@m tt]$ ls
oplog.bson
[mongod@m tt]$ mongorestore --host 127.0.0.1:28017 -u root -p xxxx --oplogReplay  --authenticationDatabase admin ./
2021-01-12T16:08:26.544+0800    preparing collections to restore from
2021-01-12T16:08:26.544+0800    replaying oplog
2021-01-12T16:08:26.549+0800    done

```
注意：
如果在恢复的过程中，报错如下
not authorized on test to execute command ...
需要重新创建角色，授权恢复用户
```
use admin
db.createRole({role:'sysadmin',roles:[], privileges:[ {resource:{anyResource:true},actions:['anyAction']}]})

db.grantRolesToUser( "admin" , [ { role: "sysadmin", db: "admin" } ])
```