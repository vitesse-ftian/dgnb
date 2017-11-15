-- Example of PHI Transducer.
-- The following SQL will generate some simulated stock price data.
-- 
CREATE TABLE stock AS 
select symbol, day, price from 
(
select 
--
-- Output columns 
--
dg_utils.transducer_column_text(1) as symbol, 
dg_utils.transducer_column_int4(2) as day, 
dg_utils.transducer_column_float8(3) as price,

--
-- Transuducer functions, $PHI$ is PostgreSQL dollar quoted string.  
--
dg_utils.transducer($PHI$PhiExec go 
// BEGIN INPUT TYPES
// i int32 
// END INPUT TYPES
//
// BEGIN OUTPUT TYPES
// symbol string
// day int32
// price float64
// END OUTPUT TYPES
//

package main

import (
	"fmt"
	"math/rand"
)

func main() {
	for rec := NextInput(); rec != nil; rec = NextInput() {
		i, _ := rec.Get_i()
		symbol := fmt.Sprintf("S%d", i)
		p := 100.0
		for n:=0; n<200; n++ {
			var outrec OutRecord
			outrec.Set_symbol(symbol)
			outrec.Set_day(int32(n))
			delta := rand.Float64() - 0.2
			p += delta
			outrec.Set_price(p)
			WriteOutput(&outrec)
		}
	}
	WriteOutput(nil)
}
$PHI$), 
-- input
t.*
from ( select i::int from generate_series(1, 4) i ) t
) foo
;
