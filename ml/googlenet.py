#
# 
# A server running googlenet on FPGA.  See Xilinx ml-suite tutorial notebook
# Right now, it is a multi threaded server, but each thread locks the device
#
import os, sys, cv2
import threading

import numpy as np

import xfdnn.rt.xdnn as pyxfdnn
import xfdnn.rt.xdnn_io as pyxfdnn_io

import xdrive_pb2, server

fpga_lock = threading.RLock()
mlsuite = "/home/nimbix/oss/ml-suite"
config = {}

g_imgc = 3
g_imgh = 224
g_imgw = 224
g_batchSize = 1

g_cInputBuffer = None
g_cFpgaInputBuffer = None

def init_fpga():
    # asw or nimbix
    config["device"] = "nimbix" 
    config["xclbin"] = mlsuite + "/overlaybins/" + config["device"] + "/overlay_3.xclbin"
    config["xfdnn_library"] = mlsuite + "/xfdnn/rt/xdnn_cpp/lib/libxfdnn.so"

    print(" --- INIT FPGA ------\n")
    print("xclbin: {0}.\n".format(config["xclbin"]))
    print("xfdnn_library: {0}.\n".format(config["xfdnn_library"])) 

    ret = pyxfdnn.createHandle(config["xclbin"], "kernelSxdnn_0", config["xfdnn_library"])
    if ret:
        raise SystemExit("ERROR: Unable to create handle to FPGA")
    else:
        print("INFO: Sucessfully create handle to FPGA.")

    # magics.   See ml-suite/notebooks tutorial.
    config["quantizecfg"] = "./gnet/quantization_params.json"
    config["bitwidths"] = [16, 16, 16]
    # config["in_shape"] = [3, 224, 224], g_img c/h/w
    config["transpose"] = [2, 0 , 1]
    config["channel_swap"] = [2, 1, 0]
    config["raw_scale"] = 255.0
    config["img_mean"] = [104.007, 116.669, 122.679]
    config["input_scale"] = 1.0
    config["calibration_size"] = 15
    config["calibration_directory"] = mlsuite + "/xfdnn/tools/quantize/calibration_directory"
    config["datadir"] = "./gnet/bvlc_googlenet_without_lrn.caffemodel_data"
    config["scaleA"] = 10000
    config["scaleB"] = 30
    config["PE"] = -1 
    config["transform"] = "resize"

    config["firstfpgalayer"] = "conv1/7x7_s2"

    config["fpgacommands"] = "./gnet/fpga.cmds"
    config["fpgaoutsz"] = 1024
    config["outsz"] = 1000
    config["useblas"] = True
    config["labels"] = mlsuite + "/examples/classification/synset_words.txt"

    (a, b, c) = pyxfdnn_io.loadWeights(config)
    config["weightsBlob"] = a
    config["fcWeight"] = b
    config["fcBias"] = c

    config["labelarray"] = []
    with open(config["labels"], 'r') as f:
        for line in f:
            config["labelarray"].append(line.strip())

    # prepare inputs, inputbuf, see ml-suite examples batch_classify.py
    config["g_inputs"] = np.zeros((g_batchSize, g_imgc*g_imgh*g_imgw), dtype=np.float32)
    # g_inputbuf = np.zeros((g_batchSize, g_imgc, g_imgh, g_imgw), dtype=np.float32)
    config["g_fpgaOutput"] = pyxfdnn_io.prepareOutput(config["fpgaoutsz"], g_batchSize) 

def get_classification(output, fn, args):
    # See xdnn_io.py, but the code there will just print to stdout.
    # We return the values.
    if isinstance (output, np.ndarray):
        output = output.flatten().tolist()

    ret = []
    idxArr = []
    for i in range(args['outsz']):
        idxArr.append(i)

    l_batchsz = len(output) / args['outsz']
    for i in range(l_batchsz):
        inputImage = fn 
        startIdx = i * args['outsz']
        vals = output[startIdx:startIdx + args['outsz']]
        top5 = sorted(zip(vals, idxArr), reverse=True)[:5]
        for j in range(len(top5)):
            ret.append((inputImage, j, top5[j][0], config['labelarray'][top5[j][1]]))

    # print("get_classification: {0}.\n".format(ret))
    return ret

def img_classify(msg):
    global g_cInputBuffer
    global g_cFpgaInputBuffer

    # message is a rowset, one col, a list of file names.
    rs = msg.rowset
    if len(rs.columns) == 0 or rs.columns[0].nrow == 0:
        print("Img classify request size is 0.\n") 
        return None
    print("Img classify request size is {0}.\n".format(rs.columns[0].nrow))
    # Lock the fpga device.   config is protected by this lock as well.

    fpga_lock.acquire()
    ret = None
    
    for i in range(rs.columns[0].nrow):
        fname = rs.columns[0].sdata[i]
        print("Running classification for images: {0}\n".format(fname))
        print("Prepare inputs ...\n")
        # g_batchSize = 1, for now.
        config["g_inputs"][0] = pyxfdnn_io.loadImageBlobFromFile(fname, config["img_mean"], g_imgh, g_imgw)

        print("Quantize inputs ...\n") 
        quantizeInputs = pyxfdnn.quantizeInputs(config["firstfpgalayer"], config["g_inputs"], g_cInputBuffer, g_cFpgaInputBuffer, 
                config["quantizecfg"], config["scaleB"])
        print("Prepare inputs for fpga inputs ...\n") 
        fpgaInputs = pyxfdnn.prepareInputsForFpga(quantizeInputs, config["quantizecfg"], config["scaleB"], -1, config["firstfpgalayer"])

        print("Run FPGA commands ...\n") 
        pyxfdnn.execute(
                config["fpgacommands"],
                config["weightsBlob"],
                fpgaInputs,
                config["g_fpgaOutput"],
                g_batchSize, 
                config["quantizecfg"],
                config["scaleB"]
                # 
                # This is freaking insane.  What is PE?
                #
                # Xilinx notebook uses PE = 0, which works for a few images then crash.
                # Xilinx example batch_classify.py says do not supply this PE paramenter, 
                # then default is -1.   Runs fine for many images.
                #
                # , config["PE"]
                #
                )

        print("Compute FC ...\n")
        fcOut = pyxfdnn.computeFC(
                config["fcWeight"],
                config["fcBias"],
                config["g_fpgaOutput"],
                g_batchSize,
                config["outsz"],
                config["fpgaoutsz"],
                config["useblas"]
                )

        print("Softmax ...\n")
        softmaxOut = pyxfdnn.computeSoftmax(fcOut, g_batchSize) 
        ret = get_classification(softmaxOut, fname, config)

    fpga_lock.release()

    # Now construct return msg
    if ret == None:
        print("Return None: ???\n")
        return None

    retmsg = xdrive_pb2.XMsg()
    rs = retmsg.rowset
    # return 4 columns, (filename, ordinal, score, class)
    col1 = rs.columns.add()
    col2 = rs.columns.add()
    col3 = rs.columns.add()
    col4 = rs.columns.add()
    col1.nrow = len(ret)
    col2.nrow = len(ret)
    col3.nrow = len(ret)
    col4.nrow = len(ret)

    for i in range(len(ret)):
        (a, b, c, d) = ret[i]
        # print("Return {0}, {1}, {2}, {3}.\n".format(a, b, c, d))
        col1.nullmap.append(False)
        col1.sdata.append(a)
        col2.nullmap.append(False)
        col2.i32data.append(b)
        col3.nullmap.append(False)
        col3.f64data.append(c)
        col4.nullmap.append(False)
        col4.sdata.append(d)

    return retmsg


if __name__=='__main__':
    # Test: an echo server.
    if len(sys.argv) != 3:
        raise SystemExit("Usage: googlenet.py [server|client] addr")

    if sys.argv[1] == "server":
        init_fpga()
        server.server_start(sys.argv[2], img_classify)
    elif sys.argv[1] == "client":
        imgs = ["apple.jpeg", "banana.jpeg", "beer.jpeg", "coffee.jpeg", "egg.jpeg", "salad.jpeg"]
        sock = server.cli_connect(sys.argv[2])
        for ii in range(6):
            xmsg = xdrive_pb2.XMsg()
            col = xmsg.rowset.columns.add()
            col.nrow = 1
            col.nullmap.append(False)
            col.sdata.append("/data/ftian/xdrive/images/" + imgs[ii]) 

            server.writeXMsg(sock, xmsg)
            ret = server.readXMsg(sock)
            col1 = ret.rowset.columns[0]
            col2 = ret.rowset.columns[1]
            col3 = ret.rowset.columns[2]
            col4 = ret.rowset.columns[3]

            nrow = ret.rowset.columns[0].nrow
            for i in range(nrow):
                print("Ret {0}: ({1}, {2}, {3}, {4}).\n".format(
                    i, 
                    col1.sdata[i], 
                    col2.i32data[i], 
                    col3.f64data[i], 
                    col4.sdata[i]))
    else:
        raise SystemExit("Usage: server.py [server|client] addr")

    print("Done!")

