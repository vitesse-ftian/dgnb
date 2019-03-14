-- explain analyze 
drop table video30;

create table video30 as
select filename, frame, tag, score, llx, lly, urx, ury, img
from (
select 
dg_utils.transducer_column_text(1) as filename,
dg_utils.transducer_column_int4(2) as frame, 
dg_utils.transducer_column_text(3) as tag, 
dg_utils.transducer_column_float4(4) as score,
dg_utils.transducer_column_float4(5) as llx, 
dg_utils.transducer_column_float4(6) as lly, 
dg_utils.transducer_column_float4(7) as urx, 
dg_utils.transducer_column_float4(8) as ury, 
dg_utils.transducer_column_text(9) as img, 
yolov2(), t.*
from (
    select dir || '/' || basename as fn, 0.0::float4, 30.0::float4
    from videofiles where basename like 'bj-%.mp4'
) t
) tmpt
;

