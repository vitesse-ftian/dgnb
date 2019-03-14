#
# A server running yolov2 on FPGA. 
# Right now, it is a multi threaded server, but each thread locks the device
#
import os, sys, cv2, base64
import threading, multiprocessing

import numpy as np
import nms

import xfdnn.rt.xdnn as pyxfdnn
import xfdnn.rt.xdnn_io as pyxfdnn_io

import xdrive_pb2, server


fpga_lock = threading.RLock()

mlsuite = "/home/nimbix/oss/ml-suite"
config = {}

# assume video is 1280x720, 25 fps
# g_framew = 1280
# g_frameh = 720
# g_fps = 25

# yolo: input image is squre.
g_imgc = 3
g_imgh = 608 
g_imgw = 608 

# yolo: output shape
g_anchor_boxes = 5
g_objectness = 1
g_classes = 80
g_outc = 4 + 1 + 80 
g_outh = 608 / 32
g_outw = 608 / 32

g_batchSize = 1
g_skip = 25  

g_scorethresh = 0.1
g_iouthresh = 0.5

def init_fpga():
    # asw or nimbix
    config["device"] = "nimbix"
    config["xclbin"] = mlsuite + "/overlaybins/" + config["device"] + "/overlay_3.xclbin"
    config["xfdnn_library"] = mlsuite + "/xfdnn/rt/xdnn_cpp/lib/libxfdnn.so"

    ret = pyxfdnn.createHandle(config["xclbin"], "kernelSxdnn_0", config["xfdnn_library"])
    if ret:
        raise SystemExit("ERROR: Unable to create handle to FPGA")
    else:
        print("INFO: Sucessfully create handle to FPGA.")

    # magics
    config["fpgacommands"] = "./yolo/fpga.cmds"
    config["memory"] = 5 
    config["dsp"] = 56
    config["quantizecfg"] = "./yolo/quantization_params.json"
    config["bitwidths"] = [16,16,16]
    config["in_shape"] = [3, 608, 608]
    config["transpose"] = [2,0,1]
    config["channel_swap"] = [2,1,0]
    config["raw_scale"] = 1.0
    config["img_mean"] = [0.0, 0.0, 0.0]
    config["input_scale"] = 1.0
    config["calibration_size"] = 15
    config["calibration_directory"] = mlsuite + "/xfdnn/tools/quantize/calibration_directory"

    config["datadir"] = "./yolo/yolov2.caffemodel_data"
    config["scaleA"] = 10000
    config["scaleB"] = 30

    config["transform"] = "yolo"
    config["firstfpgalayer"] = "layer1-conv"

    # This one!   Comes from notebook example, but we will try to use -1 (auto select.)
    print ("Loading weights ...")
    config["PE"] = -1 
    (a, b, c) = pyxfdnn_io.loadWeights(config)
    config["weightsBlob"] = a
    config["fcWeight"] = b
    config["fcBias"] = c
    print ("Weights loaded.")

    # Allocate output memory.   See notebook example for all the dark magics.
    config["fpgaoutsz"] = g_anchor_boxes * g_outc * g_outh * g_outw 
    config["g_fpgaOutput"] = pyxfdnn_io.prepareOutput(config["fpgaoutsz"], g_batchSize)

def fpga_process(qin, qout):
    init_fpga()
    while True:
        inputs = qin.get()
        if inputs is None:
            break
        
        # print(" Prepare inputs for FPGA ...\n")
        fpgaInputs = pyxfdnn.prepareInputsForFpga(inputs, 
                config["quantizecfg"], config["scaleB"], -1, config["firstfpgalayer"]) 
        if not fpgaInputs:
            break

        # print(" Executing on FPGA!\n")
        pyxfdnn.execute(
                config["fpgacommands"],
                config["weightsBlob"],
                fpgaInputs,
                config["g_fpgaOutput"],
                g_batchSize, 
                config["quantizecfg"],
                config["scaleB"]
                )

        # print(" Done, put result back to q.\n")
        qout.put(config["g_fpgaOutput"])

    qout.put(None)
    pyxfdnn.closeHandle()

# See xdnn_io.py loadYoloImageBlobFromFile
def load_yoloimg(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, c = img.shape
    # What are we doing here?  Oh my.
    newdim = max(h, w)
    scalew = float(w) / newdim
    scaleh = float(h) / newdim
    neww = int (g_imgw * scalew)
    newh = int (g_imgh * scaleh)
    reduced_img = cv2.resize(img, (neww, newh))
    reduced_img_float = np.zeros((g_imgw, g_imgw, c), np.float)
    reduced_img_float = reduced_img/255.0
    newdim = max(newh, neww)
    diffh = newdim - newh
    diffw = newdim - neww
    letter_image_float = np.zeros((newdim, newdim, c), np.float)
    letter_image_float[:,:,:] = 0.5
    letter_image_float[diffh/2:newh+diffh/2, diffw/2:neww+diffw/2] = reduced_img_float
    return np.transpose(letter_image_float, (2, 0, 1)).flatten()

def sigmoid(x):
    pos_mask = (x >= 0)
    neg_mask = (x < 0)
    z = np.zeros_like(x)
    z[pos_mask] = np.exp(-x[pos_mask])
    z[neg_mask] = np.exp(x[neg_mask])
    top = np.ones_like(x)
    top[neg_mask] = z[neg_mask]
    return top / (1 + z)

def softmax(x):
    e_x = np.exp(x-np.max(x))
    return e_x / (e_x.sum(axis=0,keepdims=True))

def coconames(cid):
    # the stuff we care.
    names = ['person', 'bicycle', 'car', 'motorbike', 'aeroplane', 
            'bus', 'train', 'truck', 'boat', 'traffic light']
    if cid < len(names):
        return names[cid]
    else:
        return None

def obj_detect(msg):
    global g_qIn, g_qOut
    rs = msg.rowset
    if len(rs.columns) == 0 or rs.columns[0].nrow == 0:
        print("Obj deection req size is 0.\n")
        return None

    # Input, will be a video file, start time, for how long.
    fname = rs.columns[0].sdata[0]
    start = rs.columns[1].f32data[0]
    duration = rs.columns[2].f32data[0]

    ret = []

    # use opencv to get frames
    print ("Obj dectect on file {0}:  start {1}, length {2}.\n", fname, rs.columns[1].f32data[0], rs.columns[2].f32data[0])
    vc = cv2.VideoCapture(fname)
    # 5: fps.
    fps = vc.get(5)

    if start > 1.0: 
        # set 0: position to milissec.
        # set 1: postiion to frame number
        vc.set(0, start * 1000)

    i = 0
    while i <= duration * fps:
        i += 1
        ok, frame = vc.read()
        if not ok:
            break

        if (i - 1) % g_skip == 0:
            # got a frame, do some transformation, then send it to FPGA.
            inputs = np.zeros((g_batchSize, g_imgc*g_imgh*g_imgw), dtype = np.float32)
            inputs[0] = load_yoloimg(frame) 

            fpga_lock.acquire()
            g_qIn.put(inputs)
            outputs = g_qOut.get()
            fpga_lock.release()

            # running the rest of yolo layer in CPU.
            outputs = outputs.reshape(g_anchor_boxes, g_outc, g_outh, g_outw)
            # sigmoid
            outputs[:,0:2,:,:] = sigmoid(outputs[:,0:2,:,:]) 
            outputs[:,4,:,:] = sigmoid(outputs[:,4,:,:])

            for box in range(g_anchor_boxes):
                outputs[box,5:,:,:] = softmax(outputs[box,5:,:,:])

            bboxes = nms.do_baseline_nms(outputs.flat,
                    frame.shape[1], frame.shape[0],
                    g_imgw, g_imgh,
                    g_outw, g_outh, 
                    g_anchor_boxes, g_classes,
                    g_scorethresh, g_iouthresh
                    )

            for j in range(len(bboxes)):
                cls = coconames(bboxes[j]['classid'])
                if cls is None:
                    continue

                llx = bboxes[j]['ll']['x']
                lly = bboxes[j]['ll']['y']
                urx = bboxes[j]['ur']['x']
                ury = bboxes[j]['ur']['y']

                # very tall/wide objects, we don't want to covering bbox
                if ((urx-llx) > frame.shape[1] * 0.5) or ((lly - ury) > frame.shape[0] * 0.5):
                    continue 

                # and avoid objects less than 30x30.   
                if (urx-llx > 30) and (lly-ury > 30): 
                    objimg = frame[ury:lly, llx:urx]
                    objimg_str = cv2.imencode('.jpg', objimg)[1].tostring()
                    objimg_str = base64.b64encode(objimg_str)

                    ret.append((i, cls, bboxes[j]['prob'], 
                        llx, lly, urx, ury, 
                        objimg_str))
    vc.release()

    # return resuts
    retmsg = xdrive_pb2.XMsg()
    rs = retmsg.rowset
    col1 = rs.columns.add()
    col2 = rs.columns.add()
    col3 = rs.columns.add()
    col4 = rs.columns.add()
    col5 = rs.columns.add()
    col6 = rs.columns.add()
    col7 = rs.columns.add()
    col8 = rs.columns.add()
    col1.nrow = len(ret)
    col2.nrow = len(ret)
    col3.nrow = len(ret)
    col4.nrow = len(ret)
    col5.nrow = len(ret)
    col6.nrow = len(ret)
    col7.nrow = len(ret)
    col8.nrow = len(ret)
    for r in ret:
        col1.nullmap.append(False)
        col1.i32data.append(r[0])
        col2.nullmap.append(False)
        col2.sdata.append(r[1])
        col3.nullmap.append(False)
        col3.f32data.append(r[2])
        col4.nullmap.append(False)
        col4.f32data.append(r[3])
        col5.nullmap.append(False)
        col5.f32data.append(r[4])
        col6.nullmap.append(False)
        col6.f32data.append(r[5])
        col7.nullmap.append(False)
        col7.f32data.append(r[6])
        col8.nullmap.append(False) 
        col8.sdata.append(r[7])
            
    return retmsg
    
if __name__=='__main__':
    global g_qIn, g_qOut

    # Test: an echo server.
    if len(sys.argv) != 3:
        raise SystemExit("Usage: yolov2.py [server|client] addr")

    if sys.argv[1] == "server":
        qIn = multiprocessing.Queue(1)
        qOut = multiprocessing.Queue(1)
        fpgaProc = multiprocessing.Process(target=fpga_process, args=(qIn, qOut))
        fpgaProc.start()
        g_qIn = qIn
        g_qOut = qOut
        server.server_start(sys.argv[2], obj_detect) 
    elif sys.argv[1] == "client":
        sock = server.cli_connect(sys.argv[2])
        xmsg = xdrive_pb2.XMsg()
        col1 = xmsg.rowset.columns.add()
        col1.nrow = 1
        col1.nullmap.append(False)
        col1.sdata.append("/home/ftian/BJVideo/24-converted.mp4") 
        col2 = xmsg.rowset.columns.add()
        col2.nrow = 1
        col2.nullmap.append(False)
        col2.f32data.append(0.0) 
        col3 = xmsg.rowset.columns.add()
        col3.nrow = 1
        col3.nullmap.append(False)
        col3.f32data.append(10.0) 

        server.writeXMsg(sock, xmsg)
        ret = server.readXMsg(sock)
        col1 = ret.rowset.columns[0]
        col2 = ret.rowset.columns[1]
        col3 = ret.rowset.columns[2]
        col4 = ret.rowset.columns[3]
        col5 = ret.rowset.columns[4]
        col6 = ret.rowset.columns[5]
        col7 = ret.rowset.columns[6]
        nrow = ret.rowset.columns[0].nrow
        # for i in range(nrow):
        #     print("Frame {0}, Class {1}, Score: {2}\n".format(col1.i32data[i], col2.sdata[i], col3.f32data[i]))
        #     print("    Bounding Box: [{0}, {1}, {2}, {3}]\n".format(
        #                 col4.f32data[i],
        #                 col5.f32data[i],
        #                 col6.f32data[i],
        #                 col7.f32data[i]
        #                 ))
    else:
        raise SystemExit("Usage: server.py [server|client] addr")

    print("Done!")

