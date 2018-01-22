import dg.conn
import dg.xtable
import dg.tf.estimator

if __name__ == '__main__':
    conn = dg.conn.Conn("ftian") 
    est = dg.tf.estimator.Estimator(batch_sz=40)
    est.add_out_col('nth', 'int')
    est.add_out_col('accuracy', 'float4')

    xt1 = dg.xtable.fromTable(conn, 'widedeep_train')
    xt2 = dg.xtable.fromTable(conn, 'widedeep_test')

    for ii in range(20):
        est.tfinput.add_xt(xt1, repeat=2, shuffle=True)
        est.tfinput.add_xt(xt1) 
        est.tfinput.add_xt(xt2)

    tfcode = """
import shutil

CONF_dir = '/tmp/census_model'
CONF_rmdir = True
CONF_model = 'wide_deep'   # can be wide, deep, wide_deep

def build_model_columns():
    # Continuous columns
    age = tf.feature_column.numeric_column('age')
    education_num = tf.feature_column.numeric_column('education_num')
    capital_gain = tf.feature_column.numeric_column('capital_gain')
    capital_loss = tf.feature_column.numeric_column('capital_loss')
    hours_per_week = tf.feature_column.numeric_column('hours_per_week')

    education = tf.feature_column.categorical_column_with_vocabulary_list(
        'education', [
          'Bachelors', 'HS-grad', '11th', 'Masters', '9th', 'Some-college',
          'Assoc-acdm', 'Assoc-voc', '7th-8th', 'Doctorate', 'Prof-school',
          '5th-6th', '10th', '1st-4th', 'Preschool', '12th'])

    marital_status = tf.feature_column.categorical_column_with_vocabulary_list(
      'marital_status', [
          'Married-civ-spouse', 'Divorced', 'Married-spouse-absent',
          'Never-married', 'Separated', 'Married-AF-spouse', 'Widowed'])

    relationship = tf.feature_column.categorical_column_with_vocabulary_list(
        'relationship', [
          'Husband', 'Not-in-family', 'Wife', 'Own-child', 'Unmarried',
          'Other-relative'])

    workclass = tf.feature_column.categorical_column_with_vocabulary_list(
      'workclass', [
          'Self-emp-not-inc', 'Private', 'State-gov', 'Federal-gov',
          'Local-gov', '?', 'Self-emp-inc', 'Without-pay', 'Never-worked'])

    # To show an example of hashing:
    occupation = tf.feature_column.categorical_column_with_hash_bucket(
        'occupation', hash_bucket_size=1000)

    # Transformations.
    age_buckets = tf.feature_column.bucketized_column(
        age, boundaries=[18, 25, 30, 35, 40, 45, 50, 55, 60, 65])

    # Wide columns and deep columns.
    base_columns = [
        education, marital_status, relationship, workclass, occupation,
        age_buckets,
    ]

    crossed_columns = [
        tf.feature_column.crossed_column(
            ['education', 'occupation'], hash_bucket_size=1000),
        tf.feature_column.crossed_column(
            [age_buckets, 'education', 'occupation'], hash_bucket_size=1000),
    ]

    wide_columns = base_columns + crossed_columns

    deep_columns = [
        age,
        education_num,
        capital_gain,
        capital_loss,
        hours_per_week,
        tf.feature_column.indicator_column(workclass),
        tf.feature_column.indicator_column(education),
        tf.feature_column.indicator_column(marital_status),
        tf.feature_column.indicator_column(relationship),
        # To show an example of embedding
        tf.feature_column.embedding_column(occupation, dimension=8),
    ]
    return wide_columns, deep_columns

def build_estimator(model_dir, model_type):
    wide_columns, deep_columns = build_model_columns()
    hidden_units = [100, 75, 50, 25]
    # Create a tf.estimator.RunConfig to ensure the model is run on CPU, which
    # trains faster than GPU for this model.
    run_config = tf.estimator.RunConfig().replace(
        session_config=tf.ConfigProto(device_count={'GPU': 0}))

    if model_type == 'wide':
        return tf.estimator.LinearClassifier(
            model_dir=model_dir,
            feature_columns=wide_columns,
            config=run_config)
    elif model_type == 'deep':
        return tf.estimator.DNNClassifier(
            model_dir=model_dir,
            feature_columns=deep_columns,
            hidden_units=hidden_units,
            config=run_config)
    else:
        return tf.estimator.DNNLinearCombinedClassifier(
            model_dir=model_dir,
            linear_feature_columns=wide_columns,
            dnn_feature_columns=deep_columns,
            dnn_hidden_units=hidden_units,
            config=run_config)

def input_fn(ii):
    features = sql_input_fn(ii)
    labels = features.pop('income')
    return features, tf.equal(labels, '>50K')

def main(unused_args): 
    # Clean up the model directory if present
    if CONF_rmdir:
        shutil.rmtree(CONF_dir, ignore_errors=True)
    model = build_estimator(CONF_dir, CONF_model)

    for ii in range (20):
        model.train(input_fn=lambda: input_fn(ii * 3))
        result1 = model.evaluate(input_fn=lambda: input_fn(ii * 3 + 1))
        sys.stderr.write("Round " + str(ii) + " accuracy: " + str(result1['accuracy']) + "\\n")
        result2 = model.evaluate(input_fn=lambda: input_fn(ii * 3 + 2))
        sys.stderr.write("Round " + str(ii) + " accuracy: " + str(result2['accuracy']) + "\\n")
        vitessedata.phi.WriteOutput([ii, float(result2['accuracy'])])

    vitessedata.phi.WriteOutput(None)

"""
    est.add_tf_code(tfcode)

    estsql = est.build_sql()
    print(estsql)
    estxt = est.build_xt(conn)
    print(estxt.show())

