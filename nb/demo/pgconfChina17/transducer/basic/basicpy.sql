-- PHI example.  python2.
-- It is a valid SQL select query
--

select 
--
-- output types, as UDF.
-- 
dg_utils.transducer_column_int4(1) as i32,
dg_utils.transducer_column_float4(2) as f32,
dg_utils.transducer_column_text(3) as t,
--
-- transducer function call, as UDF.
--
dg_utils.transducer($PHI$PhiExec python2
# A valid python program below
import vitessedata.phi
# Python declare input/output types.
vitessedata.phi.DeclareTypes('''
//
// BEGIN INPUT TYPES
// a int32
// b float32
// c string
// END INPUT TYPES
//
// BEGIN OUTPUT TYPES
// x int32
// y float32
// z string
// END OUTPUT TYPES
//
''')

def do_x():
    # This is the input data loop.
    while True:
        rec = vitessedata.phi.NextInput()
        if not rec:
            break

        outrec = [None, None, None]

        if rec[0] is None:
            outrec[0] = rec[0]
        else:
            outrec[0] = rec[0] * 2

        if rec[1] is None:
            outrec[1] = rec[1]
        else:
            outrec[1] = rec[1] * 2.0

        if rec[2] is None:
            outrec[2] = None 
        else:
            outrec[2] = "foo" + rec[2] 

        # Output
        vitessedata.phi.WriteOutput(outrec)

    # Write None to signal end of output
    vitessedata.phi.WriteOutput(None)

if __name__ == '__main__':
    do_x()

$PHI$), 
-- 
-- Input to Transducer
-- 
t.*
--
-- From, any SQL table/view subquery
-- 
from (
    select i::int, i::float4, i::text from generate_series(1, 20) i
) t
;
