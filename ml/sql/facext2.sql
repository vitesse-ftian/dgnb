create table facext2 as
select trfilename, trframe, trtag, trscore, 
        trllx, trlly, trurx, trury, 
        s1, s2
from (
select 
dg_utils.transducer_column_text(1) as trfilename,
dg_utils.transducer_column_int4(2) as trframe, 
dg_utils.transducer_column_text(3) as trtag, 
dg_utils.transducer_column_float4(4) as trscore,
dg_utils.transducer_column_float4(5) as trllx, 
dg_utils.transducer_column_float4(6) as trlly, 
dg_utils.transducer_column_float4(7) as trurx, 
dg_utils.transducer_column_float4(8) as trury, 
dg_utils.transducer_column_float4(9) as s1, 
dg_utils.transducer_column_float4(10) as s2,
facedist(), vt.*
from (
    select * from videoevt
    where tag = 'person'
) vt 
) tmpt;

