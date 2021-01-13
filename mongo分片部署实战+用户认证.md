# 集群规划

##### 注意点

各个节点应该交叉部署，避免因为一台服务器宕机，导致某个分片出问题

存放数据的目录应该单独挂载为一块容量大性能高的盘

##### 端口规划

```
 shard1     shard2    config     mongos
 30011      30021      30061     20000
 30012      30022      30062     20001
 30013      30023      30063     20002
```

##### 目录规划

```
mongodb
├── bin
├── config
│   ├── 30061
│   │   ├── conf
│   │   ├── data
│   │   └── log
│   ├── 30062
│   │   ├── conf
│   │   ├── data
│   │   └── log
│   └── 30063
│       ├── conf
│       ├── data
│       └── log
├── mongos
│   ├── 20000
│   │   ├── conf
│   │   └── log
│   ├── 20001
│   │   ├── conf
│   │   └── log
│   └── 20002
│       ├── conf
│       └── log
├── shard1
│   ├── 30011
│   │   ├── conf
│   │   ├── data
│   │   └── log
│   ├── 30012
│   │   ├── conf
│   │   ├── data
│   │   └── log
│   └── 30013
│       ├── conf
│       ├── data
│       └── log
└── shard2
    ├── 30021
    │   ├── conf
    │   ├── data
    │   └── log
    ├── 30022
    │   ├── conf
    │   ├── data
    │   └── log
    └── 30023
        ├── conf
        ├── data
        └── log
```
# 系统准备

##### 关闭大页内存

官方建议 为了提高性能

```
vim  /etc/rc.local
if test -f /sys/kernel/mm/transparent_hugepage/enabled; then
  echo never > /sys/kernel/mm/transparent_hugepage/enabled
fi
if test -f /sys/kernel/mm/transparent_hugepage/defrag; then
  echo never > /sys/kernel/mm/transparent_hugepage/defrag
fi
```

临时执行命令关闭

```
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

##### 修改文件描述符和打开进程的数量

```
vim /etc/security/limits.conf
root soft nofile 65535
root hard nofile 65535
*    soft nofile 65535
*    hard nofile 65535
```

##### 关闭selinux

```
 vim  /etc/selinux/config
 SELINUX=disabled
```

关闭后需要重启生效

# 安装mongodb

##### 下载安装mongo

```
wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel70-3.6.21.tgz
tar zxvf mongodb-linux-x86_64-rhel70-3.6.21.tgz
cp mongodb-linux-x86_64-rhel70-3.6.21/bin /mongodb/
```

##### 创建用户和组

```
useradd mongod 
passwd mongod
```

##### 设置环境变量

```
vim .bash_profile
export PATH=/mongodb/bin:$PATH
source .bash_profile
```

# 目录创建

```
#shard1
mkdir -p /mongodb/shard1/30011/conf/
mkdir -p /mongodb/shard1/30011/log/
mkdir -p /mongodb/shard1/30011/data/
mkdir -p /mongodb/shard1/30012/conf/
mkdir -p /mongodb/shard1/30012/log/
mkdir -p /mongodb/shard1/30012/data/
mkdir -p /mongodb/shard1/30013/conf/
mkdir -p /mongodb/shard1/30013/log/
mkdir -p /mongodb/shard1/30013/data/

#shard2 
mkdir -p /mongodb/shard2/30021/conf/
mkdir -p /mongodb/shard2/30021/log/
mkdir -p /mongodb/shard2/30021/data/
mkdir -p /mongodb/shard2/30022/conf/
mkdir -p /mongodb/shard2/30022/log/
mkdir -p /mongodb/shard2/30022/data/
mkdir -p /mongodb/shard2/30023/conf/
mkdir -p /mongodb/shard2/30023/log/
mkdir -p /mongodb/shard2/30023/data/

#config
mkdir -p  /mongodb/config/30061/conf/
mkdir -p  /mongodb/config/30061/log/
mkdir -p  /mongodb/config/30061/data/
mkdir -p  /mongodb/config/30062/conf/
mkdir -p  /mongodb/config/30062/log/
mkdir -p  /mongodb/config/30062/data/
mkdir -p  /mongodb/config/30063/conf/
mkdir -p  /mongodb/config/30063/log/
mkdir -p  /mongodb/config/30063/data/

#mongos
mkdir -p  /mongodb/mongos/20000/conf/
mkdir -p  /mongodb/mongos/20000/log/
mkdir -p  /mongodb/mongos/20001/conf/
mkdir -p  /mongodb/mongos/20001/log/
mkdir -p  /mongodb/mongos/20002/conf/
mkdir -p  /mongodb/mongos/20002/log/

#授权
chown mongod:mongod /mongodb -R
```
# 配置shard1

##### mongodb.conf配置
```
su - mongod
cat >  /mongodb/shard1/30011/conf/mongodb.conf  <<EOF
systemLog:
  destination: file
  path: /mongodb/shard1/30011/log/mongodb.log   
  logAppend: true
storage:
  journal:
    enabled: true
  dbPath: /mongodb/shard1/30011/data
  directoryPerDB: true
  #engine: wiredTiger
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: zlib
    indexConfig:
      prefixCompression: true
net:
  bindIp: 192.168.0.13,127.0.0.1
  port: 30011
replication:
  oplogSizeMB: 2048
  replSetName: sh1
sharding:
  clusterRole: shardsvr
processManagement: 
  fork: true
EOF

\cp  /mongodb/shard1/30011/conf/mongodb.conf  /mongodb/shard1/30012/conf/
\cp  /mongodb/shard1/30011/conf/mongodb.conf  /mongodb/shard1/30013/conf/

sed 's#30011#30012#g' /mongodb/shard1/30012/conf/mongodb.conf -i
sed 's#30011#30013#g' /mongodb/shard1/30013/conf/mongodb.conf -i
```

##### 启动节点

```
mongod -f /mongodb/shard1/30011/conf/mongodb.conf
mongod -f /mongodb/shard1/30012/conf/mongodb.conf
mongod -f /mongodb/shard1/30013/conf/mongodb.conf
```

##### 初始化复制集

```
use  admin
config = {_id: 'sh1', members: [
                          {_id: 0, host: '192.168.0.13:30011'},
                          {_id: 1, host: '192.168.0.13:30012'},
                          {_id: 2, host: '192.168.0.13:30013',"arbiterOnly":true}]
           }

rs.initiate(config)
```

##### 创建管理用户

```
use admin
db.createUser({
    user: "root",
    pwd : "xxxxx",
    roles:[
        {role:"root", db:"admin"}
    ]
})
db.auth("root", "xxxxx")
```

##### 创建keyfile文件

```
openssl rand -base64 736 > /mongodb/shard1/.keyfile
chmod 600 /mongodb/shard1/.keyfile
```

##### 添加用户认证

```
vim /mongodb/shard1/30011-13/conf/mongodb.conf
security:
  authorization: enabled
  keyFile: /mongodb/shard1/.keyfile
  clusterAuthMode: keyFile
```

##### 重启节点

```
kill -15 pid
mongod -f /mongodb/shard1/30011/conf/mongodb.conf
mongod -f /mongodb/shard1/30012/conf/mongodb.conf
mongod -f /mongodb/shard1/30013/conf/mongodb.conf
```

##### 登录验证用户认证功能

```
mongo -uroot -pxxxxx --port 30012 admin
```

##### 故障转移测试

````
#登录mongo
mongo -uroot -pxxxxx --port 30012 admin
#查看复制集状态
rs.status()
#杀死主节点
kill -15 pid
#继续登录mongo查看从节点是否变成主节点
#启动杀死的节点，恢复复制集
````

# 配置shard2

##### mongodb.conf配置

```
cat >  /mongodb/shard2/30021/conf/mongodb.conf  <<EOF
systemLog:
  destination: file
  path: /mongodb/shard2/30021/log/mongodb.log   
  logAppend: true
storage:
  journal:
    enabled: true
  dbPath: /mongodb/shard2/30021/data
  directoryPerDB: true
  #engine: wiredTiger
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: zlib
    indexConfig:
      prefixCompression: true
net:
  bindIp: 192.168.0.13,127.0.0.1
  port: 30021
replication:
  oplogSizeMB: 2048
  replSetName: sh2
sharding:
  clusterRole: shardsvr
processManagement: 
  fork: true
EOF

\cp  /mongodb/shard2/30021/conf/mongodb.conf  /mongodb/shard2/30022/conf/
\cp  /mongodb/shard2/30021/conf/mongodb.conf  /mongodb/shard2/30023/conf/

sed 's#30021#30022#g' /mongodb/shard2/30022/conf/mongodb.conf -i
sed 's#30021#30023#g' /mongodb/shard2/30023/conf/mongodb.conf -i
```

##### 启动节点

```
mongod -f /mongodb/shard2/30021/conf/mongodb.conf
mongod -f /mongodb/shard2/30022/conf/mongodb.conf
mongod -f /mongodb/shard2/30023/conf/mongodb.conf
```

##### 初始化复制集

```
mongo --port 30021
use  admin
config = {_id: 'sh2', members: [
                          {_id: 0, host: '192.168.0.13:30021'},
                          {_id: 1, host: '192.168.0.13:30022'},
                          {_id: 2, host: '192.168.0.13:30023',"arbiterOnly":true}]
           }
rs.initiate(config)
```

##### 创建管理用户

```
use admin
db.createUser({
    user: "root",
    pwd : "xxxxx",
    roles:[
        {role:"root", db:"admin"}
    ]
})
db.auth("root", "xxxxx")
```

##### 创建keyfile文件

```
cp -a /mongodb/shard1/.keyfile  /mongodb/shard2/
pkill mongo
```

##### 添加用户认证

```
/mongodb/shard2/30021-23/conf/mongodb.conf
security:
  authorization: enabled
  keyFile: /mongodb/shard2/.keyfile
  clusterAuthMode: keyFile
```

##### 重启节点

```
kill -15 pid
mongod -f /mongodb/shard2/30021/conf/mongodb.conf
mongod -f /mongodb/shard2/30022/conf/mongodb.conf
mongod -f /mongodb/shard2/30023/conf/mongodb.conf
```

##### 登录验证用户认证功能

```
mongo -uroot -pxxxxx --port 30021 admin
```

##### 故障转移测试

```
#登录mongo
mongo -uroot -pxxxxx --port 30021 admin
#查看复制集状态
rs.status()
#杀死主节点
kill -15 pid
#继续登录mongo查看从节点是否变成主节点
#启动杀死的节点，恢复复制集
```
# 配置config



##### mongodb.conf配置



```

cat > /mongodb/config/30061/conf/mongodb.conf <<EOF

systemLog:

  destination: file

  path: /mongodb/config/30061/log/mongodb.log

  logAppend: true

storage:

  journal:

    enabled: true

  dbPath: /mongodb/config/30061/data

  directoryPerDB: true

  #engine: wiredTiger

  wiredTiger:

    engineConfig:

      cacheSizeGB: 1

      directoryForIndexes: true

    collectionConfig:

      blockCompressor: zlib

    indexConfig:

      prefixCompression: true

net:

  bindIp: 192.168.0.13,127.0.0.1

  port: 30061

replication:

  oplogSizeMB: 2048

  replSetName: configReplSet

sharding:

  clusterRole: configsvr

processManagement: 

  fork: true

EOF



\cp /mongodb/config/30061/conf/mongodb.conf /mongodb/config/30062/conf/

\cp /mongodb/config/30061/conf/mongodb.conf /mongodb/config/30063/conf/

sed 's#30061#30062#g' /mongodb/config/30062/conf/mongodb.conf -i

sed 's#30061#30063#g' /mongodb/config/30063/conf/mongodb.conf -i

```



##### 启动节点



```

mongod -f /mongodb/config/30061/conf/mongodb.conf 

mongod -f /mongodb/config/30062/conf/mongodb.conf 

mongod -f /mongodb/config/30063/conf/mongodb.conf

```



##### 初始化复制集



```

mongo --port 30061

use  admin

 config = {_id: 'configReplSet', members: [

                          {_id: 0, host: '192.168.0.13:30061'},

                          {_id: 1, host: '192.168.0.13:30062'},

                          {_id: 2, host: '192.168.0.13:30063'}]

           }

rs.initiate(config)

```



##### 创建管理用户



```

use admin

db.createUser({

    user: "root",

    pwd : "xxxxx",

    roles:[

        {role:"root", db:"admin"}

    ]

})

db.auth("root", "xxxxx")

```



##### 创建keyfile文件



```

cp -a /mongodb/shard1/.keyfile  /mongodb/config

```



##### 添加用户认证



```

vim /mongodb/config/30061-63/conf/mongodb.conf

security:

  authorization: enabled

  keyFile: /mongodb/config/.keyfile

  clusterAuthMode: keyFile

```



##### 重启节点



```

kill -15 pid

mongod -f /mongodb/config/30061/conf/mongodb.conf 

mongod -f /mongodb/config/30062/conf/mongodb.conf 

mongod -f /mongodb/config/30063/conf/mongodb.conf

```



##### 登录验证用户认证功能



```

mongo -uroot -pxxxxx --port 30061 admin

```



##### 故障转移测试



```
登录mongo
mongo -uroot -pxxxxx --port 30061 admin
查看复制集状态
rs.status()
杀死主节点
kill -15 pid
继续登录mongo查看从节点是否变成主节点
启动杀死的节点，恢复复制集

```



# 配置mongos



##### mongos.conf配置



```

cat > /mongodb/mongos/20000/conf/mongos.conf <<EOF

systemLog:

  destination: file

  path: /mongodb/mongos/20000/log/mongos.log

  logAppend: true

net:

  bindIp: 192.168.0.13,127.0.0.1

  port: 20000

sharding:

  configDB: configReplSet/192.168.0.13:30061,192.168.0.13:30062,192.168.0.13:30063

processManagement: 

  fork: true

security:

  keyFile: /mongodb/mongos/.keyfile

  clusterAuthMode: keyFile

EOF


\cp  /mongodb/mongos/20000/conf/mongos.conf  /mongodb/mongos/20001/conf/

\cp  /mongodb/mongos/20000/conf/mongos.conf  /mongodb/mongos/20002/conf/

sed 's#20000#20001#g' /mongodb/mongos/20001/conf/mongos.conf -i

sed 's#20000#20002#g' /mongodb/mongos/20002/conf/mongos.conf -i

```



##### 启动节点



```
mongos -f /mongodb/mongos/20000/conf/mongos.conf

mongos -f /mongodb/mongos/20001/conf/mongos.conf

mongos -f /mongodb/mongos/20002/conf/mongos.conf

```



##### 登录mongos



```
mongo -uroot -pxxxxx --port 20000 admin

```

# 集群维护
##### 停止集群进程
```
pkill mongo
平滑停止
kill -15 pid 
```
##### 启动集群
```
先启动config
mongod -f /mongodb/config/30061/conf/mongodb.conf 
mongod -f /mongodb/config/30062/conf/mongodb.conf 
mongod -f /mongodb/config/30063/conf/mongodb.conf

再启动 Shard节点
mongod -f /mongodb/shard1/30011/conf/mongodb.conf
mongod -f /mongodb/shard1/30012/conf/mongodb.conf
mongod -f /mongodb/shard1/30013/conf/mongodb.conf

mongod -f /mongodb/shard2/30021/conf/mongodb.conf
mongod -f /mongodb/shard2/30022/conf/mongodb.conf
mongod -f /mongodb/shard2/30023/conf/mongodb.conf

最后启动mongos
mongos -f /mongodb/mongos/20000/conf/mongos.conf
mongos -f /mongodb/mongos/20001/conf/mongos.conf
mongos -f /mongodb/mongos/20002/conf/mongos.conf
```
*注意事项*  
*后期在mongos里创建的业务管理用户，只在config里能查询到，不会同步到shard节点*

##### 登录mongos
```
mongo -uroot -pxxxxx --port 20000 admin
```

# 添加分片节点



##### 添加分片节点



```

mongo -uroot -pxxxxx --port 20000 admin

db.runCommand( { addshard : "sh1/192.168.0.13:30011,192.168.0.13:30012,192.168.0.13:30013",name:"shard1"} )

db.runCommand( { addshard : "sh2/192.168.0.13:30021,192.168.0.13:30022,192.168.0.13:30023",name:"shard2"} )

```



##### 查看分片



```

列出分片

db.runCommand( { listshards : 1 } )

整体状态查看

sh.status();

```



# RANGE分片配置测试



##### 激活数据库分片功能



```

mongo -uroot -pxxxxx --port 20000 admin

admin> db.runCommand( { enablesharding : "test" } )

```



##### 指定分片键对集合分片



```

创建索引

use test

> db.vast.ensureIndex( { id: 1 } )

开启分片

use admin

> db.runCommand( { shardcollection : "test.vast",key : {id: 1} } )

```



##### 录入测试数据



```

admin> use test

test> for(i=1;i<1000000;i++){ db.vast.insert({"id":i,"name":"shenzheng","age":70,"date":new Date()}); }

test> db.vast.stats()

```



##### 分片结果测试



```

#shard1

sh1:PRIMARY> db.vast.count();

500001

#shard2

sh2:PRIMARY> 500001

500001

```



# HASH分片配置测试



对oldboy库下的vast大表进行hash

创建哈希索引



##### oldboy开启分片功能



```

mongo -uroot -pxxxxx --port 20000 admin

use admin

admin> db.runCommand( { enablesharding : "oldboy" } )

```



##### oldboy库下的vast表建立hash索引



````

use oldboy

oldboy> db.vast.ensureIndex( { id: "hashed" } )

````



##### 开启分片 



```

use admin

admin > sh.shardCollection( "oldboy.vast", { id: "hashed" } )

```



##### 录入10w行数据测试



```

use oldboy

for(i=1;i<100000;i++){ db.vast.insert({"id":i,"name":"shenzheng","age":70,"date":new Date()}); }

```



##### 分片结果测试



```

mongo -uroot -pxxxxx --port 30011 admin

sh1:PRIMARY> use oldboy

sh1:PRIMARY> db.vast.count()

50393



mongo -uroot -pxxxxx --port 30022 admin

sh2:PRIMARY> use oldboy

sh2:PRIMARY> db.vast.count()

49606

```



# 分片节点的查询及管理



##### 判断是否Shard集群



```css

admin> db.runCommand({ isdbgrid : 1})

```



##### 列出所有分片信息



```css

admin> db.runCommand({ listshards : 1})

```



 ##### 列出开启分片的数据库 



```swift

admin> use config

config> db.databases.find( { "partitioned": true } )

或者：

config> db.databases.find() //列出所有数据库分片情况

```



 ##### 查看分片的片键



```swift

config> db.collections.find().pretty()

{

    "_id" : "test.vast",

    "lastmodEpoch" : ObjectId("58a599f19c898bbfb818b63c"),

    "lastmod" : ISODate("1970-02-19T17:02:47.296Z"),

    "dropped" : false,

    "key" : {

        "id" : 1

    },

    "unique" : false

}

```



##### 查看分片的详细信息



```css

admin> sh.status()

```



##### 删除分片节点（谨慎）



```css

确认blance是否在工作

sh.getBalancerState()

删除shard2节点(谨慎)

mongos> db.runCommand( { removeShard: "shard2" } )

注意：删除操作一定会立即触发blancer。

```



# balancer操作



##### 介绍



```css

mongos的一个重要功能，自动巡查所有shard节点上的chunk的情况，自动做chunk迁移。

什么时候工作？

1、自动运行，会检测系统不繁忙的时候做迁移

2、在做节点删除的时候，立即开始迁移工作

3、balancer只能在预设定的时间窗口内运行


有需要时可以关闭和开启blancer（备份的时候）

mongos> sh.stopBalancer()

mongos> sh.startBalancer()

```



##### 自定义 自动平衡进行的时间段



```objectivec

https://docs.mongodb.com/manual/tutorial/manage-sharded-cluster-balancer/#schedule-the-balancing-window

// connect to mongos



use config

sh.setBalancerState( true )

db.settings.update({ _id : "balancer" }, { $set : { activeWindow : { start : "3:00", stop : "5:00" } } }, true )



sh.getBalancerWindow()

sh.status()



关于集合的balancer（了解下）

关闭某个集合的balance

sh.disableBalancing("db.table")

打开某个集合的balancer

sh.enableBalancing("db.table")

确定某个集合的balance是开启或者关闭

db.getSiblingDB("config").collections.findOne({_id : "db.table"}).noBalance;

```