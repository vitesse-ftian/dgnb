drop function facedist();

create function facedist () returns bigint 
as $BODY$ 
select dg_utils.transducer($PHI$PhiExec python2
import vitessedata.phi as phi
import vitessedata.phi.xdrive_pb2 as xdrive_pb2
import vitessedata.phi.server as server
import base64, cv2 
import face_recognition as face
import numpy as np

phi.DeclareTypes('''
//
// BEGIN INPUT TYPES
// filename string
// frame int32
// tag string
// score float32
// llx float32
// lly float32
// urx float32
// ury float32
// img string
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
// s1score float32
// s2score float32
// END OUTPUT TYPES
//
''')

def match(te, img):
    imgstr = base64.b64decode(img)
    imgarr = np.frombuffer(imgstr, np.uint8)
    imgdata = cv2.imdecode(imgarr, cv2.IMREAD_COLOR)
    imgdata = cv2.cvtColor(imgdata, cv2.COLOR_BGR2RGB)
    ie = face.face_encodings(imgdata)
    if len(ie) == 0:
        return [100.0, 100.0] 
    res = face.face_distance(te, ie[0]) 
    return res

if __name__ == '__main__':
    s1 = cv2.imread("/data/ftian/xdrive/videos/img/search1.png") 
    s2 = cv2.imread("/data/ftian/xdrive/videos/img/search2.png") 
    s1 = cv2.cvtColor(s1, cv2.COLOR_BGR2RGB)
    s2 = cv2.cvtColor(s2, cv2.COLOR_BGR2RGB)
    s1 = face.face_encodings(s1)[0] 
    s2 = face.face_encodings(s2)[0] 

    while True:
        rec = phi.NextInput()
        if not rec:
            break
        res = match([s1, s2], rec[8]) 
        rec[8] = res[0]
        rec.append(res[1])
        phi.WriteOutput(rec)
    phi.WriteOutput(None)
$PHI$)
$BODY$
language sql;

