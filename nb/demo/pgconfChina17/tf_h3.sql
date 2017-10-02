WITH xdata as (
    select tag, 
       case when cat = 'linear' then 1.0::float4
            when cat = 'moon' then 2.0::float4
            else 3.0::float4 end,
       x::float4, y::float4 from tf_train
)
select 
dg_utils.transducer_column_float4(1) as accuracy,
dg_utils.transducer($PHIWORKER$PhiExec python2 --task_index=#SEGID#
import vitessedata.phi
import tensorflow.python.platform
import time
import numpy as np
import tensorflow as tf
import os
import logging

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

vitessedata.phi.DeclareTypes('''
//
// BEGIN INPUT TYPES
// tag int32
// cat float32
// x float32
// y float32
// END INPUT TYPES
//
// BEGIN OUTPUT TYPES
// accuracy float32
// END OUTPUT TYPES
//
''')

# Define the flags useable from the command line.
tf.app.flags.DEFINE_string("ps_hosts", "localhost:16180", "Comma-separated list of hostname:port pairs")
tf.app.flags.DEFINE_string("worker_hosts", "localhost:16181,localhost:16182", "Comma-separated list of hostname:port pairs")
tf.app.flags.DEFINE_integer('workers', 2, 'Number of max workers')
tf.app.flags.DEFINE_integer('task_index', 0, 'Task idx')
FLAGS = tf.app.flags.FLAGS

def create_done_queue(i):
    """ Queue used to signal death for i'th ps shard. Intended to have 
    all workers enqueue an item onto it to signal doneness."""
    with tf.device("/job:ps/task:%d" % (i)):
        return tf.FIFOQueue(FLAGS.workers, tf.int32, shared_name="done_queue"+
                        str(i))
  
def create_done_queues():
    """ Assume one 1 ps host. """
    return [create_done_queue(i) for i in range(1)] 


# Global variables.
NUM_LABELS = 2    # The number of labels.
NUM_FEATURES = 3  # The number of features, cat, x, y
BATCH_SIZE = 100  # The number of training examples to use per training step.
NUM_HIDDEN = 20

def nextbatch(): 
    labels = []
    fvecs = []
    cnt = 0
    while True:
        if cnt == BATCH_SIZE:
            break
        rec = vitessedata.phi.NextInput()
        if not rec:
            break
        cnt += 1
        labels.append(rec[0])
        fvecs.append([rec[1], rec[2], rec[3]]) 

    if cnt == 0:
        return cnt, None, None
    else:
        # Convert the array of float arrays into a numpy float matrix.
        fvecs_np = np.matrix(fvecs).astype(np.float32)

        # Convert the array of int labels into a numpy array.
        labels_np = np.array(labels).astype(dtype=np.uint8)

        # Convert the int numpy array into a one-hot matrix.
        labels_onehot = (np.arange(NUM_LABELS) == labels_np[:, None]).astype(np.float32)
        return cnt, fvecs_np, labels_onehot

# Init weights method. (Lifted from Delip Rao: http://deliprao.com/archives/100)
def init_weights(shape, init_method='xavier', xavier_params = (None, None)):
    if init_method == 'zeros':
        return tf.Variable(tf.zeros(shape, dtype=tf.float32))
    elif init_method == 'uniform':
        return tf.Variable(tf.random_normal(shape, stddev=0.01, dtype=tf.float32))
    else: #xavier
        (fan_in, fan_out) = xavier_params
        low = -4*np.sqrt(6.0/(fan_in + fan_out)) # {sigmoid:4, tanh:1} 
        high = 4*np.sqrt(6.0/(fan_in + fan_out))
        return tf.Variable(tf.random_uniform(shape, minval=low, maxval=high, dtype=tf.float32))

def main(_): 
    # cluster and server stuff 
    ps_hosts = FLAGS.ps_hosts.split(",")
    worker_hosts = FLAGS.worker_hosts.split(",")
    cluster = tf.train.ClusterSpec({"ps":ps_hosts, "worker":worker_hosts})
    server = tf.train.Server(cluster, job_name="worker", task_index=FLAGS.task_index)

    # chief worker reset graph...
    # if FLAGS.task_index == 0:
    #      tf.reset_default_graph()

    # Assigns ops to the local worker by default.
    with tf.device(tf.train.replica_device_setter(
        worker_device="/job:worker/task:%d" % FLAGS.task_index,
        cluster=cluster)):
        global_step = tf.Variable(0, trainable=False) 

        # This is where training samples and labels are fed to the graph.
        # These placeholder nodes will be fed a batch of training data at each
        # training step using the {feed_dict} argument to the Run() call below.
        x = tf.placeholder("float", shape=[None, NUM_FEATURES])
        y_ = tf.placeholder("float", shape=[None, NUM_LABELS])
    
        # Define and initialize the network.
        # Initialize the hidden weights and biases.
        w_hidden = init_weights(
            [NUM_FEATURES, NUM_HIDDEN], 
            'xavier', xavier_params=(NUM_FEATURES, NUM_HIDDEN)) 

        b_hidden = init_weights([1,NUM_HIDDEN],'zeros') 

        # The hidden layer.
        hidden = tf.nn.tanh(tf.matmul(x,w_hidden) + b_hidden)

        # Initialize the output weights and biases.
        w_out = init_weights(
                [NUM_HIDDEN, NUM_LABELS],
                'xavier', xavier_params=(NUM_HIDDEN, NUM_LABELS))

        b_out = init_weights([1,NUM_LABELS],'zeros')

        # The output layer.
        y = tf.nn.softmax(tf.matmul(hidden, w_out) + b_out)
    
        # Optimization.
        cross_entropy = -tf.reduce_sum(y_*tf.log(y))
        train_step = tf.train.GradientDescentOptimizer(0.01).minimize(cross_entropy, global_step=global_step)
    
        # Evaluation.
        predicted_class = tf.argmax(y,1);
        correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(y_,1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

        init_op = tf.global_variables_initializer() 
        enq_ops = []
        for q in create_done_queues():
            qop = q.enqueue(1)
            enq_ops.append(qop)

        # Create a "supervisor", which oversees the training process.
        sv = tf.train.Supervisor(is_chief=(FLAGS.task_index == 0),
                             logdir="/home/ftian/oss/dgtools/demo/upwork/tensorflow/h3_log_%d" % FLAGS.task_index,
                             init_op=init_op,
                             # summary_op=summary_op,
                             saver=tf.train.Saver(), 
                             save_model_secs=1,
                             global_step=global_step)

        # on a localhost with mulitple workers, there is a race condition that hangs non chief 
        # workers.   
        sess_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False,
                                 device_filters=["/job:ps", "/job:worker/task:%d" % FLAGS.task_index])
        with sv.prepare_or_wait_for_session(server.target, config=sess_config) as sess:
            # Iterate and train.
            while True:
                logging.info("PHI DBG: Getting Next batch ... ") 
                n, batch_data, batch_labels = nextbatch()
                if n == 0:
                    logging.info("PHI DBG: Done!")
                    break
                # feed data into the model
                logging.info("PHI DBG: Next batch, n = " + str(n))
                time.sleep(0.1)
                _, gstep = sess.run([train_step, global_step], feed_dict={x: batch_data, y_: batch_labels})

            for op in enq_ops:
                logging.info("PHI DBG: End, running enq_ops")
                sess.run(op)

        logging.info("PHI DBG: End, stop")
        sv.stop()

    logging.info("PHI DBG: End, WriteOuptut None")
    vitessedata.phi.WriteOutput(None)

if __name__ == '__main__':
    tf.app.run()
$PHIWORKER$), tworker.*
from ( 
    select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
    union all select * from xdata
) tworker;
