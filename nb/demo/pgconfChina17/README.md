# Scripting MPP RDBMS with Transducer

First, one should run the load sql script in data dir to populate
database.

Assuming go and python are installed on all hosts (master and segs)
all the notebook examples, exception tensorflow should just run, 
after fixing sql connection string.

* A [Basic](./Basic.ipynb) example
* Simple [DBLink](./Transfer.ipynb) example.
* Generate [Runs](./stockrun.ipynb) from synthetic stock price data.
* [Graph](./Graph.ipynb) algorithm, BSF and OSSP.
* Tensorflow [h3](./TensorFlow.ipynb) 3 hidden layers ANN.


Tensorflow example needs tensorflow libray to be installed on all 
hosts.  After that, one need to update the sql to point the directory
to right place (ftian/oss of course won't work).  To train, just 
```
psql -f tf_ps.sql 
```  
in one console, then 
```
psql -f tf_h3.sql
```
in another console.

To evaluate, 
```
psql -f tf_h3_eval.sql.
```

Evaluate can be executed during training and you should see accurary fluctuates.
