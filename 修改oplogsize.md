# 背景
由于某些情况，我们必须修改oplog size来增大同步窗口期，例如业务的快速增长，延迟节点无法跟上Primary节点的oplog增长速度；MongoDB在3.6版本后才对oplogSize支持了动态修改，但MongoDB版本低于3.6版本则需要逐个剔除副本集逐个扩容，至此记录修改oplogsize的步骤。

# 修改MongoDB3.6版本以上的oplog
 3.6版本后支持的动态扩容方法
 针对副本集必须在每个节点进行修改操作，仅仅修改某个节点没作用

```
查看 oplog 的状态，输出信息包括 oplog 日志大小，操作日志记录的起始时间
repset:PRIMARY> db.getReplicationInfo() 
{
    "logSizeMB" : 1755.03173828125,
    "usedMB" : 0.84,
    "timeDiff" : 861042,
    "timeDiffHours" : 239.18,
    "tFirst" : "Mon Jun 24 2019 16:18:20 GMT+0800 (CST)",
    "tLast" : "Thu Jul 04 2019 15:29:02 GMT+0800 (CST)",
    "now" : "Thu Jul 04 2019 15:29:06 GMT+0800 (CST)"
}
查看oplog的状态、总大小、使用大小、存储的时间范围、记录时长
repset:PRIMARY> db.printReplicationInfo()
configured oplog size:   1755.03173828125MB
log length start to end: 861132secs (239.2hrs)
oplog first event time:  Mon Jun 24 2019 16:18:20 GMT+0800 (CST)
oplog last event time:   Thu Jul 04 2019 15:30:32 GMT+0800 (CST)
now:                     Thu Jul 04 2019 15:30:36 GMT+0800 (CST)
查询当前当前oplog的大小
repset:PRIMARY> use local
switched to db local
repset:PRIMARY> db.oplog.rs.stats().maxSize
NumberLong(1840284160)  #单位为bytes，即1.8G
修改oplog的大小
repset:PRIMARY> use local
switched to db local
repset:PRIMARY> db.adminCommand({replSetResizeOplog:1,size:4096})   #单位为MB，扩容至4G
{
    "ok" : 1,
    "operationTime" : Timestamp(1562225042, 1),
    "$clusterTime" : {
        "clusterTime" : Timestamp(1562225042, 1),
        "signature" : {
            "hash" : BinData(0,"AAAAAAAAAAAAAAAAAAAAAAAAAAA="),
            "keyId" : NumberLong(0)
        }
    }
}
验证修改结果
repset:PRIMARY> db.oplog.rs.stats().maxSize
NumberLong("4294967296")
```
# 修改MongoDB3.6版本以下的oplog
需求： Oplog扩容，尽量少的影响业务  

思路：先由从节点开始，一台一台的从复制集中剥离，修改，再回归复制集，最后操作主节点来减少业务影响时间。

流程：先关闭一个从节点，去掉–replSet启动参数,更换启动端口–port,将节点以单机模式启动。

备份：备份现有的oplog

##### 关闭从节点
```
[root@iZ2ze6rm1auwacy4tk6ucaZ ~]# ps -ef|grep mongo
root     28527     1  0 14:46 ?        00:00:17 mongod -f /etc/mongod1.conf
root     28605     1  0 14:46 ?        00:00:18 mongod -f /etc/mongod2.conf
root     28686     1  0 14:46 ?        00:00:12 mongod -f /etc/mongod3.conf
root     30794 28282  0 15:50 pts/0    00:00:00 grep mongo
[root@iZ2ze6rm1auwacy4tk6ucaZ ~]# mongod --shutdown -f /etc/mongod2.conf 
killing process with pid: 28605
```
##### 修改从节点的配置文件
注释副本集配置参数并修改端口，以单机模式启动
```
[root@iZ2ze6rm1auwacy4tk6ucaZ ~]# mongod -f /etc/mongod2.conf 
about to fork child process, waiting until server is ready for connections.
forked process: 30940
child process started successfully, parent exiting
```
注：此时停止掉副节点的依旧保持在副本集中，不过此时它的状态为不可达，健康值为0。在作为单机模式启动修改完成，再以副本集模式启动即可。
##### 备份节点oplog记录
```
[root@iZ2ze6rm1auwacy4tk6ucaZ ~]# mongodump -h 172.17.136.124:27021 -d  local -c oplog.rs -o /root/oplog
2019-07-04T15:59:01.603+0800    writing local.oplog.rs to 
2019-07-04T15:59:01.630+0800    done dumping local.oplog.rs (8069 documents)
```
##### 进入mongo，将现在的oplog中最新的位置复制到tmp表（local数据库）中
```
> use local
switched to db local
> db.temp.save( db.oplog.rs.find( { }, { ts: 1, h: 1 } ).sort( {$natural : -1} ).limit(1).next() )
WriteResult({ "nInserted" : 1 })
> db.temp.find()  #验证记录是否存在
{ "_id" : ObjectId("5d1db2646bebcb3f6483cce3"), "ts" : Timestamp(1562226683, 1), "h" : NumberLong("2207544736706975504") }
```
#####  删除原有的oplog集合
```
> db.oplog.rs.drop()
true
```
##### 创建新的oplog集合，为4G
```
> db.runCommand({create:"oplog.rs",capped:true,size:(4*1024*1024*1024)})
{ "ok" : 1 }  #创建成功
```
##### 将tmp中的数据存储到新的oplog中，并验证
```
> db.oplog.rs.save( db.temp.findOne() )
WriteResult({
    "nMatched" : 0,
    "nUpserted" : 1,
    "nModified" : 0,
    "_id" : ObjectId("5d1db2646bebcb3f6483cce3")
})
> db.oplog.rs.find()  #验证
 { "_id" : ObjectId("5d1db2646bebcb3f6483cce3"), "ts" : Timestamp(1562226683, 1), "h" : NumberLong("2207544736706975504") }
```
##### 关闭从节点，并恢复原有config配置，并在config中设置oplogSize为你之前设置的大小，并启动
关闭从节点
```
[root@iZ2ze6rm1auwacy4tk6ucaZ ~]# mongod --shutdown -f /etc/mongod2.conf 
killing process with pid: 30940
```
恢复原有配置文件时，要注意oplogSizeMB参数值的修改，修改为扩容后的值
```
#配置文件中指定oplog大小
replication:
  oplogSizeMB: 4096
  replSetName: repset
```
重新启动从节点
```
[root@iZ2ze6rm1auwacy4tk6ucaZ ~]# mongod -f /etc/mongod2.conf 
about to fork child process, waiting until server is ready for connections.
forked process: 31702
child process started successfully, parent exiting
```
登陆mongoshell检查节点状态及oplog大小
```
[root@iZ2ze6rm1auwacy4tk6ucaZ ~]# mongo 172.17.136.124:27018
repset:SECONDARY> db.getReplicationInfo()
{
    "logSizeMB" : 4096,
    "usedMB" : 0.01,
    "timeDiff" : 0,
    "timeDiffHours" : 0,
    "tFirst" : "Thu Jul 04 2019 15:51:23 GMT+0800 (CST)",
    "tLast" : "Thu Jul 04 2019 15:51:23 GMT+0800 (CST)",
    "now" : "Thu Jul 04 2019 16:20:43 GMT+0800 (CST)"
}
```
 至此，oplog大小修改完毕，依次修改其他节点，修改主节点是可先降级或直接关闭主节点
 ```
 Primary>rs.stepDown()          ---可以更有效的产生选举
 ```
 补充：

1、若是在启动副本集是指定了oplogsize大小。在动态扩容后，oplog.rs集合大小已发生变化，但配置文件中最初指定的oplogsize大小不变，并且重启后依旧不变，但是oplogsize依旧是扩容之后的大小。

2、如果减小oplogsize的大小，可能会造成oplog记录丢失，导致节点异常，故不可减小。