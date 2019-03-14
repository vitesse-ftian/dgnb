drop function yolov2();

create function yolov2 () returns bigint 
as $BODY$ 
select dg_utils.transducer($PHI$PhiExec python2
import vitessedata.phi as phi
import vitessedata.phi.xdrive_pb2 as xdrive_pb2
import vitessedata.phi.server as server

phi.DeclareTypes('''
//
// BEGIN INPUT TYPES
// fn string 
// begin float32
// duration float32
// END INPUT TYPES
//
// BEGIN OUTPUT TYPES
// filename string
// frame int32
// tag string
// score float32
// llx float32
// lly float32
// urx float32
// ury float32
// img string
// END OUTPUT TYPES
//
''')

def yolov2(sock, fn, start, duration):
    xmsg = xdrive_pb2.XMsg()
    col1 = xmsg.rowset.columns.add()
    col1.nrow = 1
    col1.nullmap.append(False)
    col1.sdata.append(fn)
    col2 = xmsg.rowset.columns.add()
    col2.nrow = 1
    col2.nullmap.append(False)
    col2.f32data.append(start) 
    col3 = xmsg.rowset.columns.add()
    col3.nrow = 1
    col3.nullmap.append(False)
    col3.f32data.append(duration) 

    server.writeXMsg(sock, xmsg)
    ret = server.readXMsg(sock)
    nrow = ret.rowset.columns[0].nrow

    result = []
    for i in range(nrow):
        result.append([fn, 
            ret.rowset.columns[0].i32data[i], 
            ret.rowset.columns[1].sdata[i], 
            ret.rowset.columns[2].f32data[i], 
            ret.rowset.columns[3].f32data[i], 
            ret.rowset.columns[4].f32data[i], 
            ret.rowset.columns[5].f32data[i], 
            ret.rowset.columns[6].f32data[i], 
            ret.rowset.columns[7].sdata[i]]) 
    return result
     
if __name__ == '__main__':
    sock = server.cli_connect('/tmp/ml.socket')
    while True:
        rec = phi.NextInput()
        if not rec:
            break

        res = yolov2(sock, rec[0], rec[1], rec[2])
        for r in res:
            phi.WriteOutput(r)
    phi.WriteOutput(None)
$PHI$)
$BODY$
language sql;

