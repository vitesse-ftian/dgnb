drop function imgmatch();

create function imgmatch () returns bigint 
as $BODY$ 
select dg_utils.transducer($PHI$PhiExec python2
import vitessedata.phi as phi
import vitessedata.phi.xdrive_pb2 as xdrive_pb2
import vitessedata.phi.server as server
import base64, cv2
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
// matchscore float32
// END OUTPUT TYPES
//
''')

def match(template, img):
    imgstr = base64.b64decode(img)
    imgarr = np.frombuffer(imgstr, np.uint8)
    imgdata = cv2.imdecode(imgarr, cv2.IMREAD_COLOR)
    imgdata = cv2.resize(imgdata, (128, 128))
    match = cv2.matchTemplate(template, imgdata, cv2.TM_CCOEFF_NORMED)
    return match[0][0]

     
if __name__ == '__main__':
    t = cv2.imread("/home/ftian/BJVideo/img/search2.png")
    t = cv2.resize(t, (128, 128))

    while True:
        rec = phi.NextInput()
        if not rec:
            break
        res = match(t, rec[8]) 
        rec[8] = res
        phi.WriteOutput(rec)
    phi.WriteOutput(None)
$PHI$)
$BODY$
language sql;

