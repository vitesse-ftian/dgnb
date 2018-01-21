import dg.xtable
import dg.tf.input_fn

class Estimator:
    def __init__(self, extract_label, batch_sz=100):
        self.extract_label = extract_label
        self.batch_sz = batch_sz
        self.tfinput = dg.tf.input_fn.InputFn()
        self.out_cols = []

    def add_out_col(self, name, typ):
        self.out_cols.append(dg.xtable.XCol(n, t))

    def add_tf_code(self, tfcode): 
        self.tfcode = tfcode

    def tr_out_cols(self):
        s = ""
        for idx, col in enumerate(self.out_cols):
            pgt, trt = col.pg_tr_type()
            s += "dg_utils.transducer_column_{0}({1}) as {2},\n".format(pgt, idx+1, col.name)
        return s

    def build_tr_in_types(self):
        tft = self.tfinput.build_xt()
        s = ""
        for col in tft.schema:
            pgt, trt = col.pg_tr_type()
            s += "// {0} {1}\n".format(col.name, trt)
        return s

    def build_tr_out_types(self):
        s = ""
        for col in self.out_cols:
            pgt, trt = col.pg_tr_type()
            s += "// {0} {1}\n".format(col.name, trt)
        return s

    def build_input_fn_types(self):
        tft = self.tfinput.build_xt()
        return ",".join(["tr.{0}".format(col.tr_type()) for col in tft.schema])

    def build_input_fn_shapes(self):
        tft = self.tfinput.build_xt()
        return ",".join(["[]" for col in tft.schema])

    def build_input_fn_colnames(self):
        tft = self.tfinput.build_xt()
        return ",".join(['"{0}"'.format(col.name) for col in tft.schema])

    def build_tr_sql(self):
        tft = self.tfinput.build_xt()
        return tft.sql

    def build_xt(self, conn):
        sql = self.build_xtsql()
        return dg.xtable.fromSQL(conn, sql)

    def build_xtsql(self):
        sql = """ select {0} 
dg_utils.transducer($PHI$PhiExec python2
import vitessedata.phi
vitessedata.phi.DeclareTypes('''
//
{1}
//
{2}
//
''')
import shutil
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf

class TfPhiReader:
    def __init__(self):
        self.tf_aux_ii = 0
        self.nextrow = None

    def next(self, ii): 
        if self.tf_aux_ii == ii:
            if self.nextrow != None:
                ret = self.nextrow
                self.nextrow = None
                return ret[2:]
            else:
                rec = vitessedata.phi.NextInput()
                if rec == None:
                    return None
                if rec[0] != ii:
                    self.tf_aux_ii = rec[0]
                    self.nextrow = rec
                    return None
                else:
                    return rec[2:]
        else:
            if self.nextrow != None:
                return None
            else:
                rec = vitessedata.phi.NextInput()
                if rec == None:
                    return None
                if rec[0] == ii:
                    self.tf_aux_ii = rec[0]
                    if rec[0] == ii:
                        return rec[2:]
                    else:
                        self.nextrow = rec
                        return None
            
tf_phi_reader = TfPhiReader()

def phi_generator(ii):
    cnt = 0
    rec = tf_phi_reader.next(ii)
    while rec != None:
        cnt += 1
        yield tuple(rec)
        rec = tf_phi_reader.next(ii)

def sql_input_fn(ii): 
    ds = tf.data.Dataset.from_generator(lambda: phi_generator(ii), 
            ({3}),
            ({4}))
    ds = ds.batch({5}) 
    cols = ds.make_one_shot_iterator().get_next()
    features = dict(zip([{6}], cols)) 
    return features

{7}

if __name__ == '__main__:
    sys.stderr = open("/tmp/phi_py2_tf.log", "w")
    tf.logging.set_verbosity(tf.logging.ERROR)
    tf.app.run(main=main, None)

$PHI$), phitft.* from (
{8}
) phitft
""".format(self.tr_out_cols(),
           self.build_tr_in_types(), 
           self.build_tr_out_types(),
           self.build_input_fn_types(),
           self.build_input_fn_shapes(),
           self.batch_sz,
           self.build_input_fn_colnames(),
           self.tfcode,
           self.build_tr_sql())
        return sql




