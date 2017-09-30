drop table linear_train;
drop table linear_eval;
create table linear_train (tag int, x float, y float) distributed randomly;
create table linear_eval (tag int, x float, y float) distributed randomly;
\copy linear_train from './linear_data_train.csv' with csv;
\copy linear_eval from './linear_data_eval.csv' with csv;

drop table moon_train;
drop table moon_eval;
create table moon_train (tag int, x float, y float) distributed randomly;
create table moon_eval (tag int, x float, y float) distributed randomly;
\copy moon_train from './moon_data_train.csv' with csv;
\copy moon_eval from './moon_data_eval.csv' with csv;

drop table saturn_train;
drop table saturn_eval;
create table saturn_train (tag int, x float, y float) distributed randomly;
create table saturn_eval (tag int, x float, y float) distributed randomly;
\copy saturn_train from './saturn_data_train.csv' with csv;
\copy saturn_eval from './saturn_data_eval.csv' with csv;

drop table tf_train;
drop table tf_evel;
create table tf_train(cat text, tag int, x float4, y float4) distributed randomly;
insert into tf_train 
select 'linear', tag, x::float4, y::float4 from linear_train
union all select 'moon', tag, x::float4, y::float4 from moon_train
union all select 'saturn', tag, x::float4, y::float4 from saturn_train;

create table tf_eval(cat text, tag int, x float4, y float4) distributed randomly;
insert into tf_eval 
select 'linear', tag, x::float4, y::float4 from linear_eval
union all select 'moon', tag, x::float4, y::float4 from moon_eval
union all select 'saturn', tag, x::float4, y::float4 from saturn_eval;

drop table dblp;
create table dblp(i int, j int) distributed randomly;
\copy dblp from './com-dblp.ungraph.txt' with csv delimiter '\t';

drop table dblpw;
create table dblpw as select i, j, random() as w from dblp;
