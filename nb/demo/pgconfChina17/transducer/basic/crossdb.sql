-- Example of PHI Transducer.
-- It is a SQL select statement 
WITH FOO AS ( 
select 
--
-- Output columns 
--
dg_utils.transducer_column_int4(1) as pk, 
dg_utils.transducer_column_int4(2) as sk, 
dg_utils.transducer_column_int4(3) as avail,
dg_utils.transducer_column_float4(4) as cost,
dg_utils.transducer_column_text(5) as cmt,

--
-- Transuducer functions, $PHI$ is PostgreSQL dollar quoted string.  
--
dg_utils.transducer($PHI$PhiExec go x
// BEGIN INPUT TYPES
// i int32 
// END INPUT TYPES
//
// BEGIN OUTPUT TYPES
// pk int32
// sk int32
// avail int32
// cost float32
// cmt string
// END OUTPUT TYPES
//

package main

import (
	"os"
	"github.com/vitesse-ftian/dggo/vitessedata/xtable"
)

func write_fake(i int32) {
		var outrec OutRecord
		outrec.Set_pk(i)
		outrec.Set_sk(i)
		outrec.Set_avail(i)
		outrec.Set_cost(0)
		outrec.Set_cmt("FAKE")
		WriteOutput(&outrec)
}
	

func main() {
	// We use lib/pq, which will panic if the following two ENV variables are
	// set.   Phi is forked from postgres, which sets them.
	os.Unsetenv("PGSYSCONFDIR")
	os.Unsetenv("PGLOCALEDIR")
	
	for rec := NextInput(); rec != nil; rec = NextInput() {
    	write_fake(-1)
	}

	Log("Output Input loop, write 0")
	write_fake(0)

	dg := xtable.Deepgreen {
		Host: "localhost",
		Port: "5432",
		Db: "tpch1f",
	}

	Log("Output Input loop, write 1")
	write_fake(1)
	err := dg.Connect()
	if err != nil {
		Log("Deepgreen connect failed, err %%v!", err) 
		panic("Cannot open connection")
	}
	defer dg.Disconnect()

	Log("Output Input loop, write 2")
	write_fake(2)
	ps, err := xtable.MakeXTable(&dg, "partsupp")
	if err != nil {
		Log("Deepgreen partsupp table  err %%v!", err) 
		panic("Cannot open xtable partsupp")
	}

	Log("Output Input loop, write 3")
	write_fake(3)
	rs, err := ps.Execute()
	if err != nil {
		Log("Deepgreen partsupp Execute err %%v!", err) 
		panic("Cannot run xtable")
	}
	defer rs.Close()

	Log("Output Input loop, write 4")
	write_fake(4)
	for rs.Next() {
		var pk, sk, avail int32
		var cost float32
		var cmt string
		rs.Scan(&pk, &sk, &avail, &cost, &cmt)

		write_fake(5)
		var outrec OutRecord
		outrec.Set_pk(pk)
		outrec.Set_sk(sk)
		outrec.Set_avail(avail)
		outrec.Set_cost(cost)
		outrec.Set_cmt(cmt)
		WriteOutput(&outrec)
	}

	Log("Output Input loop, write 6")
	write_fake(6)

	Log("Output Input loop, write nil")
	WriteOutput(nil)
}
$PHI$), 
-- The following is input the transducer, any sql works.
t.*
from ( select i::int from generate_series(1, 2) i ) t
)
SELECT count(*) FROM FOO;
-- SELECT * FROM FOO LIMIT 10;
