## 安装部署
####  下载mongodb
https://www.mongodb.com/try/download/community

####  系统准备  
centos6.2以上  
关闭大页内存-官方建议 为了提高性能  
root用户写入文件关闭大页内存  
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
修改文件描述符和打开进程的数量
vim /etc/security/limits.conf
```
root soft nofile 65535
root hard nofile 65535
* soft nofile 65535
* hard nofile 65535
```
#### mongodb的安装

创建用户和组
```
useradd mongod 
passwd mongod
```
创建目录
```
mkdir -p /mongodb/conf
mkdir -p /mongodb/log
mkdir -p /mongodb/data
```
安装解压
```
tar zxvf /src/mongodb-linux-x86_64-rhel70-3.6.21.tgz
cp -a /src/mongodb-linux-x86_64-rhel70-3.6.21/bin  /mongodb/
chown mongod:mongod /mongodb/ -R
```
设置环境变量
vim .bash_profile
```
export PATH=/mongodb/bin:$PATH
source .bash_profile
```
启动mongod
```
mongod --dbpath=/mongodb/data --logpath=/mongodb/log/mongodb.log --port=27017 --logappend --fork
```
登录mongo
```
mongo
```
#### mongodb的配置

mongodb在3.0以后加入了YAML模式，本次用YAML格式

/mongodb/conf/mongo.conf

```
systemLog:

   destination: file 

   path: "/mongodb/log/mongodb.log"

   logAppend: true

processManagement:

   fork: false

net:

   port: 27017

   bindIp: "0.0.0.0"

storage:

   dbPath: "/mongodb/data/"

   journal:

      enabled: true
```
重启mongo
```
mongod -f /mongodb/conf/mongo.conf --shutdown
mongod -f /mongodb/conf/mongo.conf & 
```
# mongo的常用命令   

==>按照此官方文档进行学习https://docs.mongodb.com/v3.6/crud/

#### 库命令
```
> show dbs = show databases

admin   0.000GB

config  0.000GB

local   0.000GB

> use admin

switched to db admin

> use test

switched to db test

> db.dropDatabase()

{ "dropped" : "test", "ok" : 1 }
```
#### 表命令
```
> show tables = show collections

system.version

> db

admin

> use test

switched to db test

> db.tab.insert({name:"qiqige"})

WriteResult({ "nInserted" : 1 })

> db.tab.find()

{ "_id" : ObjectId("5fbf9449cbe8e227709f3c5f"), "name" : "qiqige" }

> show tables

tab

> db.version()

3.6.21

> db.tt.insert({name:"qiqige",age:12,"gender":"woman"})

WriteResult({ "nInserted" : 1 })

查询命令可以多了解一些，就像mysql一样查询命令最丰富了

> db.tt.find()  默认只显示20页

{ "_id" : ObjectId("5fbf99310a08962813700cb2"), "name" : "qiqige", "age" : 12, "gender" : "woman" }

> db.tt.find({name:"qiqige"})

{ "_id" : ObjectId("5fbf99310a08962813700cb2"), "name" : "qiqige", "age" : 12, "gender" : "woman" }

> db.tt.find({name:"qiqige"}).pretty()

{

        "_id" : ObjectId("5fbf99310a08962813700cb2"),

        "name" : "qiqige",

        "age" : 12,

        "gender" : "woman"

}



> db.tt.renameCollection('tt1')

{ "ok" : 1 }

> show tables;

tt1

> db.tt1.count()

1

> for (i=0;i<10000;i++){db.tt1.insert({"uid":i,"name":"mongodb","age":6,"date":new Date()})} 批量插入

WriteResult({ "nInserted" : 1 })

查看集合的状态信息

> db.tt1.stats()

> db.tt1.dataSize()  集合中数据的原始大小  字节单位

800070

> db.tt1.totalIndexSize() 集合中索引数据的原始大小

114688

> db.tt1.totalSize() 集合中索引和数据压缩之后的大小  主要看这个  mongo的压缩比高于mysql

389120

> db.tt1.storageSize() 集合中数据压缩存储的大小

274432

>

```

#### 状态查看命令
```
> db.stats()

{

        "db" : "test",

        "collections" : 2,

        "views" : 0,

        "objects" : 1,

        "avgObjSize" : 39,

        "dataSize" : 39,

        "storageSize" : 20480,

        "numExtents" : 0,

        "indexes" : 2,

        "indexSize" : 20480,

        "fsUsedSize" : 6018129920,

        "fsTotalSize" : 21002579968,

        "ok" : 1

}

```
#### 帮助命令
```
db.help()

db.table.help()

rs.help()

sh.help()
```
#### 命令的种类
```
db.xx  可用tab键寻找

db.help()

db.tablename.help()

db.tablename.xx 可用tab键寻找
```
#### 用户管理

注意：  

验证库 给那个库创建管理用户就use到那个库创建用户 登录的时候需要指定库登录   

创建管理员需要use到admin库里 登录的时候需要指定库  

常用角色：root、read、readWrite  


1、新建用户时，use到的库，就是此用户的验证库  

2、登录时，必须明确指定验证库才能登录   

3、管理员用户的库是admin,普通用户的验证库一般是所管理的库  

4、如果直接登录到数据库里，不use,默认是test库，生产环境不建议  

```
> use admin;

switched to db admin

> db.createUser({ user:"root", pwd:"Qn@9965321", roles:[{role:"root",db:"admin"}] })

Successfully added user: {

        "user" : "root",

        "roles" : [

                {

                        "role" : "root",

                        "db" : "admin"

                }

        ]

}

> db.auth('root','Qn@9965321')

1
```

mongo开启验证  

cat /mongodb/conf/mongo.conf  

文件末尾添加如下两行  
```
security:

    authorization: enabled
```

登录mongo
```
mongo -uroot -pxxxxx admin
mongo -uroot -pxxxx  55.99.22.33/admin  远程登录

```
创建用户
```
> use test;

switched to db test

> db.createUser({ user:"test", pwd:"xxxxx", roles:[{role:"readWrite",db:"test"}] })

Successfully added user: {

        "user" : "test",

        "roles" : [

                {

                        "role" : "readWrite",

                        "db" : "test"

                }

        ]

}

> db.auth('test','xxxxx')

1

>



db.createUser(

{ user:"test", 

pwd:"xxxxx", 

roles:[{role:"read",db:"test"},{role:"readWrite",db:"test2"}]  创建test用户对test库只读，对test2库读写

}

)

```

查看用户
```
> use admin

switched to db admin

> show tables;

system.users

system.version

> db.system.users.find()

{ "_id" : "admin.root", "userId" : UUID("c67a294f-a0b1-4f7b-93c1-c7b39c5667cf"), "user" : "root", "db" : "admin", "credentials" : { "SCRAM-SHA-1" : { "iterationCount" : 10000, "salt" : "cx59R+7Vy5un60j0myCU4A==", "storedKey" : "GpHMBPe+cwtCBZPP4WMvlSqujrY=", "serverKey" : "9oFQuQWMhO1FbIT8BUeH/N9WHNg=" } }, "roles" : [ { "role" : "root", "db" : "admin" } ] }

{ "_id" : "test.test", "userId" : UUID("17170445-f838-4f0e-9067-cb175103f460"), "user" : "test", "db" : "test", "credentials" : { "SCRAM-SHA-1" : { "iterationCount" : 10000, "salt" : "TpFO2QcxydH3SUX/xHyKYQ==", "storedKey" : "UDFVHbzmqYkZHu3QRuZ9QprWCtw=", "serverKey" : "LPzsE6VlTCZQhoHmX3Phc18fNR0=" } }, "roles" : [ { "role" : "readWrite", "db" : "test" } ] }

{ "_id" : "test.testread", "userId" : UUID("d01ea1f1-75f1-45b5-b36d-11e2f461dbae"), "user" : "testread", "db" : "test", "credentials" : { "SCRAM-SHA-1" : { "iterationCount" : 10000, "salt" : "Y2KDBWEug9jA0sFqUK9HNA==", "storedKey" : "5b4LYupUIaWCUG8UYUkuZ7L9B/g=", "serverKey" : "LukIjZAyIXjxw5VbTp0/hD2UNFc=" } }, "roles" : [ { "role" : "read", "db" : "test" } ] }

>

```

删除用户
```

使用管理员用户登录后，删除那个用户就先use到那个用户的验证库下

> use test

switched to db test

> db.dropUser('test')

true
```














