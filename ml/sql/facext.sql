create table facext as
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
facedist(), tmpt.*
from (
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
            select dir || '/' || basename as fn, 0::float4, 10::float4
            from videofiles where basename like 'bj-_.mp4' 
        ) t
    ) tr 
) tmpt
) tmptt
;

