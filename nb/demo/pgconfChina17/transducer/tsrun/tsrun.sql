-- Example of PHI Transducer.
-- The following SQL will produce run from stock data. 
-- 
select 
--
-- Output columns 
--
dg_utils.transducer_column_text(1) as symbol, 
dg_utils.transducer_column_int4(2) as d0,
dg_utils.transducer_column_float8(3) as p0,
dg_utils.transducer_column_int4(4) as d1,
dg_utils.transducer_column_float8(5) as p1,

--
-- Transuducer functions, $PHI$ is PostgreSQL dollar quoted string.  
--
dg_utils.transducer($PHI$PhiExec go 
// BEGIN INPUT TYPES
// symbol string
// day int32
// price float64
// END INPUT TYPES
//
// BEGIN OUTPUT TYPES
// symbol string
// start int32
// startprice float64
// end int32
// endprice float64
// END OUTPUT TYPES
//

package main

func main() {
	var outrec *OutRecord
	for rec := NextInput(); rec != nil; rec = NextInput() {
		symbol, _ := rec.Get_symbol()
		day, _ := rec.Get_day()
		price, _ := rec.Get_price()

		if day == 0 {
			if outrec != nil {
				WriteOutput(outrec)
			}
			outrec = new(OutRecord)
			outrec.Set_symbol(symbol)
			outrec.Set_start(day)
			outrec.Set_startprice(price)
			outrec.Set_end(day)
			outrec.Set_endprice(price)
		} else {
			// Check if it is a run, either up or down.
			isuprun := price >= outrec.GetValue_endprice() && outrec.GetValue_endprice() >= outrec.GetValue_startprice()
			isdownrun := price <= outrec.GetValue_endprice() && outrec.GetValue_endprice() <= outrec.GetValue_startprice()
			if isuprun || isdownrun {
				outrec.Set_end(day)
				outrec.Set_endprice(price)
			} else {
				oldrec := outrec
				outrec = new(OutRecord)
				outrec.Set_symbol(symbol)
				outrec.Set_start(oldrec.GetValue_end())
				outrec.Set_startprice(oldrec.GetValue_endprice())
				outrec.Set_end(day)
				outrec.Set_endprice(price)
				WriteOutput(oldrec) 
			}
		}
	}

	if outrec != nil {
		WriteOutput(outrec)
	}
	WriteOutput(nil)
}
$PHI$), 
-- input.  worth pointing out the the row_number() over (...) will force a partition and ordering by day
-- on the inputdata to transducer.   This is critical, as the run building in transducer assumes such partiion
-- and ordering.
t.symbol, t.day, t.price 
from (
	select row_number() over (partition by symbol order by day), symbol, day, price from stock
) t
;
