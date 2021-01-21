```
#!/bin/bash 
#created by qiqi 2018-5-4

#db.createUser({user:'backuouser',pwd:'phcXJhXoHt6v4CU',roles: [{role:'backup',db:'admin'}]})

USERNAME=xxx #备份的用户名 
PASSWORD=xxxx #备份的密码
HOST=xxxx #备份主机
PORT=xxx

DATE=`date +%Y-%m-%d`  #用来做备份文件名字的一部分
OLDDATE=`date +%Y-%m-%d -d '-3 days'`  #本地保存天数  

#指定命令所用的全路径
MONGODUMP=/usr/local/mongodb-3.2.16/bin/mongodump
MONGO=/usr/local/mongodb-3.2.16/bin/mongo
#创建备份的目录和文件
BACKDIR=./
[ -d ${BACKDIR} ] || mkdir -p ${BACKDIR}
[ -d ${BACKDIR}/${DATE} ] || mkdir ${BACKDIR}/${DATE}
[ ! -d ${BACKDIR}/${OLDDATE} ] || rm -rf ${BACKDIR}/${OLDDATE} #保存5天 多余的删除最前边的
#开始备份  for循环想要备份的数据库

MONGODBLIST=(banquanku blockchain copyright_filing copyright_monitor  haihang tutu)

#以下这条命令要先在命令行 试试 在用到脚本里
#MONGODBLIST=`${MONGO}  ${HOST}:${PORT}/admin  -u$USERNAME -p$PASSWORD  --eval "printjson(db.getMongo().getDBNames())" | grep -iv "\[\|\]\|MongoDB\|connecting\|local" | sed  's/"//' | sed 's/",//' | sed 's/"//'`

for db in ${MONGODBLIST[*]}
do
    ${MONGODUMP} --host ${HOST}:${PORT} -u ${USERNAME} -p ${PASSWORD} -d ${db} -o ${BACKDIR}/${DATE}/  --authenticationDatabase=admin
done
```