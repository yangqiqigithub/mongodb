```
#!/bin/bash
while :
do
  DATA=`date +%Y-%m-%d\ %H:%M:%S`
  stillRunning=$(ps -ef |grep mongo |grep -v "grep" |grep -v "start")
  if [ "$stillRunning" ] ; then
        echo ${DATA}
    echo "Mongodb_3717 service was already started by another way" 
  else
    echo "Mongodb_3717 service was not started" 
        echo ${DATA}
    echo "Starting service ..." 
    /app/mongodb/start.sh
    echo "Mongodb_3717 service was exited!" 
  fi
  sleep 30
done
```