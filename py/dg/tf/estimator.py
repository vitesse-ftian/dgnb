import dg.xtable

class Feature
    def __init__(self, name):
        self.name = name
        self.indent = '    ' 
    def child(self, c):
        if type(c) is str:
            return "'{0}'".format(c)
        else:
            return c.name

class NumericColumn(Feature):
    def __init__(self, name):
        Feature.__init__(self, name)
    def gencode(self):
        return '''{0}{1} = tf.feature_column.numeric_column('{1}')\n'''.format(self.indent, self.name)

class CategoricalColumn(Feature):
    def __init__(self, name, vals=None, hash_bucket_size=None):
        Feature.__init__(self, name)
        self.vals = vals
        self.hash_bucket_size = hash_bucket_size 
    def gencode(self):
        if self.vals == None:
            return '''{0}{1} = tf.feature_column.categorical_column_with_hash_bucket('{1}', hash_bucket_size={2})\n'''.format(self.indent, self.name, self.hash_bucket_size)
        else:
            return '''{0}{1} = tf.feature_column.categorical_column_with_vocabulary_list('{1}', {2})\n'''.format(self.indent, self.name, str(self.vals))

class BucketizedColumn(Feature):
    def __init__(self, name, f, boundaries):
        Feature.__init__(self, name)
        self.f = f
        self.boundaries = boundaries
    def gencode(self):
        return '''{0}{1} = tf.feature_column.bucketized_column({2}, boundaries={3})\n'''.format(self.indent, self.name, self.child(self.f), str(self.boundaries))

class CrossedColumn(Feature):
    def __init__(self, name, fs, hash_bucket_size): 
        Feature.__init__(self, name)
        self.fs = fs
        self.hash_bucket_size = hash_bucket_size 
    def children(self):
        return ", ".join([self.child(f) for f in self.fs])
    def gencode(self):
        return '''{0}{1} = tf.feature_column.crossed_column([{2}], hash_bucket_size={3})\n'''.format(self.indent, self.name, self.children(), self.hash_bucket_size)

class IndicatorColumn(Feature):
    def __init__(self, name, f):
        Feature.__init__(self, name)
        self.f = f
    def gencode(self):
        return '''{0}{1} = tf.feature_column.indicator_column({2})\n'''.format(self.indent, self.name, self.child(self.f))

class EmbeddingColumn(Feature):
    def __init__(self, name, f, dimension):
        Feature.__init__(self, name)
        self.f = f
        self.dimension = dimension
    def gencode(self):
        return '''{0}{1} = tf.feature_column.embedding_column({2}, dimension={3})\n'''.format(self.indent, self.name, self.child(self.f), self.dimension)

def numeric_column(name):
    return NumericFeature(name)

def categorical_column_with_vocabulary_list(name, vals):
    return CategoricalFeature(name, vals=vals)

def categorical_column_with_hash_bucket(name, hash_bucket_size) 
    return CategoricalFeature(name, hash_bucket_size=hash_bucket_size) 

def bucketized_column(name, f, boundaries):
    return BucketizedColumn(name, f, boundaries)

def crossed_column(name, fs, hash_bucket_size):
    return CrossedColumn(name, fs, hash_bucket_size)

def indicator_column(name, f):
    return IndicatorColumn(name, f)

def embedding_column(name, f, dimension):
    return EmbeddingColumn(name, f, dimension)

class LinearClassifier:
    def __init__(self, model_dir, inputfn):
        self.model_dir = model_dir
        self.inputfn = inputfn
        self.feature = []

    def add_feature(self, f):
        self.feature.append(f)

    def xtable(self):
