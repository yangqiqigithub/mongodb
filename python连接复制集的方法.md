```
from pymongo import MongoClient, ReadPreference

def db_conn():
    client = MongoClient(['127.0.0.1:28017', '127.0.0.1:28018', '127.0.0.1:28019'])
    db_auth = client.admin
    db_auth.authenticate('root', 'xxxxxx)
    db = client.get_database('test', read_preference=ReadPreference.SECONDARY_PREFERRED)
    print(db)
if __name__ == '__main__':
    db_conn()

```

```
client = MongoClient(['127.0.0.1:28017', '127.0.0.1:28018', '127.0.0.1:28019'])
主要是想说这行代码 ，会写上复制集的所有节点（除了仲裁节点），当主节点死了，代码依然可以连接mongo
```

在副本集Replica Set中才涉及到ReadPreference的设置，默认情况下，读写都是分发都Primary节点执行，但是对于写少读多的情况，我们希望进行读写分离来分摊压力，所以希望使用Secondary节点来进行读取，Primary只承担写的责任（实际上写只能分发到Primary节点，不可修改）。

MongoDB有5种ReadPreference模式：

primary
主节点，默认模式，读操作只在主节点，如果主节点不可用，报错或者抛出异常。

primaryPreferred
首选主节点，大多情况下读操作在主节点，如果主节点不可用，如故障转移，读操作在从节点。

secondary
从节点，读操作只在从节点， 如果从节点不可用，报错或者抛出异常。

secondaryPreferred
首选从节点，大多情况下读操作在从节点，特殊情况（如单主节点架构）读操作在主节点。

nearest
最邻近节点，读操作在最邻近的成员，可能是主节点或者从节点。