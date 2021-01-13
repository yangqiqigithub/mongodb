
# 规划
本次搭建一主两从  
 
172.20.125.181:28017  
172.20.125.181:28018  
172.20.125.181:28019  

172.20.125.181:28020 用来测试节点的添加和删除  
# 系统准备
centos6.2以上  
本次实验防火墙已经关闭  

#### 关闭大页内存
官方建议 为了提高性能  
写入文件关闭大页内存  
vim  /etc/rc.local   
```
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
#### 修改文件描述符和打开进程的数量
vim /etc/security/limits.conf
```
root soft nofile 65535
root hard nofile 65535
* soft nofile 65535
* hard nofile 65535
```
# 安装mongodb

#### 创建用户和组
```
useradd mongod 
passwd mongod
```
#### 创建目录
```
mkdir -p /mongodb/conf
```
#### 安装解压
```
wget  https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel70-3.6.21.tgz
tar zxvf /src/mongodb-linux-x86_64-rhel70-3.6.21.tgz
cp -a /src/mongodb-linux-x86_64-rhel70-3.6.21/bin  /mongodb/
chown mongod:mongod /mongodb/ -R
```
#### 设置环境变量
```
vim .bash_profile
export PATH=/mongodb/bin:$PATH
source .bash_profile
```
#### 创建数据和日志目录
```
su - mongod 
mkdir -p /mongodb/28017/conf /mongodb/28017/data /mongodb/28017/log
mkdir -p /mongodb/28018/conf /mongodb/28018/data /mongodb/28018/log
mkdir -p /mongodb/28019/conf /mongodb/28019/data /mongodb/28019/log
mkdir -p /mongodb/28020/conf /mongodb/28020/data /mongodb/28020/log
```
# 配置复制集
#### 配置文件列表
```
/mongodb/28017/conf/mongod.conf
/mongodb/28018/conf/mongod.conf
/mongodb/28019/conf/mongod.conf
/mongodb/28020/conf/mongod.conf
```
#### 配置文件配置
```
cat > /mongodb/28017/conf/mongod.conf <<EOF
systemLog:
  destination: file
  path: /mongodb/28017/log/mongodb.log
  logAppend: true
storage:
  journal:
    enabled: true
  dbPath: /mongodb/28017/data
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
processManagement:
  fork: true
net:
  bindIp:  172.20.125.180,127.0.0.1
  port: 28017
replication:
  oplogSizeMB: 2048
  replSetName: my_repl
EOF
```
```
\cp  /mongodb/28017/conf/mongod.conf  /mongodb/28018/conf/
\cp  /mongodb/28017/conf/mongod.conf  /mongodb/28019/conf/
\cp  /mongodb/28017/conf/mongod.conf  /mongodb/28020/conf/

sed 's#28017#28018#g' /mongodb/28018/conf/mongod.conf -i
sed 's#28017#28019#g' /mongodb/28019/conf/mongod.conf -i
sed 's#28017#28020#g' /mongodb/28020/conf/mongod.conf -i
```
#### 创建复制集间验证的密钥文件
```
openssl rand -base64 102 > /mongodb/28017/.faceai.key
chmod 600 /mongodb/28017/.faceai.key
cp -a /mongodb/28017/.faceai.key  /mongodb/28018/
cp -a /mongodb/28017/.faceai.key  /mongodb/28019/
cp -a /mongodb/28017/.faceai.key  /mongodb/28020/
```
#### 启动实例
```
mongod -f /mongodb/28017/conf/mongod.conf
mongod -f /mongodb/28018/conf/mongod.conf
mongod -f /mongodb/28019/conf/mongod.conf
mongod -f /mongodb/28020/conf/mongod.conf
netstat -lnp|grep 280
```
#### 登录数据库配置复制集
```
mongo -port 28017 admin
config = {_id: 'my_repl', members: [
                          {_id: 0, host: '172.20.125.180:28017'},
                          {_id: 1, host: '172.20.125.180:28018'},
                          {_id: 2, host: '172.20.125.180:28019'}]
          }                
rs.initiate(config) 
```
#### 查看复制集状态
```
查看复制集状态
rs.status()
查看复制集配置
rs.config()
查看当前是否是主节点
rs.isMaster(); 
```
#### 配置管理员用户
```
use admin;
db.createUser(
     {
         user: "root",
         pwd: "xxxxx",
         roles: [ { role: "root" , db: "admin" } ]
     }
 )
db.auth('root','xxxxx')
```
#### 停止所有实例
```
pkill mongo
```
#### 修改配置文件开启验证  
所有节点的mongod.conf 末尾添加  
#以下几行要么不添加要么都添加  
注意根据实际路径 填写keyfile的路径  
```
security:
  authorization: enabled
  clusterAuthMode: keyFile
  keyFile: /mongodb/2801x/.faceai.key
```
#### 启动实例
```
mongod -f /mongodb/28017/conf/mongod.conf
mongod -f /mongodb/28018/conf/mongod.conf
mongod -f /mongodb/28019/conf/mongod.conf
mongod -f /mongodb/28020/conf/mongod.conf
netstat -lnp|grep 280
```

#### 用户带密码登录
```
mongo -uroot -pxxxxx --port 28018 admin
```
# 验证测试
#### 查看复制集状态
```
查看复制集状态
rs.status()
查看复制集配置
rs.config()
查看当前是否是主节点
rs.isMaster(); 
```

#### 批量插入测试数据
```
use test
for(var i = 1 ;i < 100; i++) {db.foo.insert({a:i});}
db.foo.count()
```
#### 登录从节点查看数据
```
use test;
rs.slaveOk();
db.foo.count();
```
# 故障转移测试
#### 添加删除节点
```
rs.remove("ip:port"); // 删除一个节点
rs.add("ip:port"); // 新增从节点
rs.addArb("ip:port"); // 新增仲裁节点
```
*注意事项*
```
my_repl:PRIMARY> cfg=rs.conf()
{
        "_id" : "my_repl",
        "version" : 5,
        "protocolVersion" : NumberLong(1),
        "members" : [
                {
                        "_id" : 1, 
                        ## 做过节点的增删后，这个_id可能就不是从0开始了，但是这个节点索引依然是0 
                        "host" : "172.20.125.180:28017",
                        "arbiterOnly" : false,
                },
                {
                        "_id" : 2,
                        "host" : "172.20.125.180:28018",
                        "arbiterOnly" : false,
                },
                {
                        "_id" : 3,
                        "host" : "172.20.125.180:28020",
                        "arbiterOnly" : true,
                }
        ],
        
}
# 这里要很注意[]里的2不是指_id=2的，是从0开始数，到2的哪个节点
my_repl:PRIMARY> cfg.members[2].priority=0
0
my_repl:PRIMARY> cfg.members[2].hidden=true
true
my_repl:PRIMARY> cfg.members[2].slaveDelay=120
120
my_repl:PRIMARY> rs.reconfig(cfg)
{
        "ok" : 1,
        "operationTime" : Timestamp(1606739283, 1),
        "$clusterTime" : {
                "clusterTime" : Timestamp(1606739283, 1),
                "signature" : {
                        "hash" : BinData(0,"AAAAAAAAAAAAAAAAAAAAAAAAAAA="),
                        "keyId" : NumberLong(0)
                }
        }
}
```

#### 特殊从节点
arbiter节点：主要负责选主过程中的投票，但是不存储任何数据，也不提供任何服务  
hidden节点：隐藏节点，不参与选主，也不对外提供服务。  
delay节点：延时节点，数据落后于主库一段时间，因为数据是延时的，也不应该提供服务或参与选主，所以通常会配合hidden（隐藏）  
一般情况下会将delay+hidden一起配置使用  
#### 配置延时节点（一般延时节点也配置成hidden）
```
cfg=rs.conf() 
cfg.members[2].priority=0
cfg.members[2].hidden=true
cfg.members[2].slaveDelay=120
rs.reconfig(cfg)    


取消以上配置
cfg=rs.conf() 
cfg.members[2].priority=1
cfg.members[2].hidden=false
cfg.members[2].slaveDelay=0
rs.reconfig(cfg)    
配置成功后，通过以下命令查询配置后的属性
rs.conf(); 
```

# 副本集的其他命令
```
查看副本集的配置信息
admin> rs.conf()
查看副本集各成员的状态
admin> rs.status()
++++++++++++++++++++++++++++++++++++++++++++++++
--副本集角色切换（不要人为随便操作）
admin> rs.stepDown()
注：
admin> rs.freeze(300) //锁定从，使其不会转变成主库
freeze()和stepDown单位都是秒。
+++++++++++++++++++++++++++++++++++++++++++++
设置副本节点可读：在副本节点执行
admin> rs.slaveOk()
eg：
admin> use app
switched to db app
app> db.createCollection('a')
{ "ok" : 0, "errmsg" : "not master", "code" : 10107 }

查看副本节点（监控主从延时）
admin> rs.printSlaveReplicationInfo()
source: 192.168.1.22:27017
    syncedTo: Thu May 26 2016 10:28:56 GMT+0800 (CST)
    0 secs (0 hrs) behind the primary
```