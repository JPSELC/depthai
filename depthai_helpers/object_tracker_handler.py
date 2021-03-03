import cv2
import numpy as np
from datetime import datetime
import time
import math

t_prev = []
t_const = []

Trk_dict = {}
Seq_dict = {}

Diff = 10
Time_diff_ms = 800
seq = 1;

bot_min = 200

class Trk:
    def __init__(self, t_id, label,status,left,right,top,bottom):
        global seq
        self.t_id = t_id
        self.label = label
        self.status = status
        self.co = [left, right, top, bottom, (left+right)/2, (top+bottom)/2]
        self.ts = math.floor(time.time() * 1000.0)
        self.dt = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]
        if not self.t_id in Seq_dict:
            Seq_dict[self.t_id] = 1
        self.seq = Seq_dict[self.t_id];

    def pr(self):
         out_str = ("{7},{0},{8},{1},{2},{3},{4},{5},{6}\r\n"\
             .format(self.t_id, self.label, self.status, self.co[0], self.co[1], self.co[2], self.co[3], self.dt, self.seq))
         with open('my_csv.csv',mode = 'a+') as writer:
             writer.write(out_str)


def sigdiff(a,b):
    res = False
    if a>Diff:
        lo = a-Diff
        if b<lo:
            res = True
    if b>(a+Diff) :
        res = True
    return res

tlast = Trk(0,"NOTHING","LOST",0,0,0,0)

def incSeq(t_id):
    sn = Seq_dict[t_id]
    sn += 1
    if (sn>99):
        sn=1
    Seq_dict[t_id] = sn    

def checkValidVehicle(co):
    return (co[3]>200) or (co[0]<220 and co[3]>175)


def show_changes(t):
    global tlast
    global seq
    newDet = False
    if t.t_id >= 0:
        if (not t.t_id in Trk_dict):
            # Only add if not already there and not LOST
            if (t.status != "LOST"):
                Trk_dict[t.t_id] = t
        else:
            lost = False
            t_old = Trk_dict[t.t_id]
            if t.label != t_old.label:
                # Change the Seq if the label has changed
                incSeq(t.t_id)
            else:
                if t.status == "LOST":
                    # Delete LOST tracks
                    lost = True
                    # Update the seq number when LOST
                    incSeq(t.t_id)
                sd = False;
                for i in range(4):
                    if sigdiff(t.co[i],t_old.co[i]):
                        sd = True
                if sd:
                    #print("Coordinate Change")
                    # Only print if signicant left-right movement and 
                    if (    (t.label == "vehicle") and \
                            (t.label == t_old.label) and \
                            (t.seq == t_old.seq) and \
                            (sigdiff(t.co[4],t_old.co[4])) and \
                            checkValidVehicle(t.co) and checkValidVehicle(t_old.co) and \
                            (t.ts < (t_old.ts+Time_diff_ms))):
                        if ((tlast.ts != t_old.ts) and (tlast.seq != t.seq)) or \
                               (t.ts > tlast.ts+Time_diff_ms) or \
                               (t.t_id != tlast.t_id) or \
                               (t.label != tlast.label):
                            with open('my_csv.csv',mode = 'a+') as writer:
                                writer.write("\r\n")
                            t_old.pr()
                            newDet = True
                        t.pr()
                        tlast = t
            if lost:
                del Trk_dict[t.t_id]
            else:
                Trk_dict[t.t_id] = t
    return newDet                    
                
def show_tracklets(tracklets, frame, labels):
    # img_h = frame.shape[0]
    # img_w = frame.shape[1]

    # iterate through pre-saved entries & draw rectangle & text on image:
    tracklet_nr = tracklets.getNrTracklets()

    for i in range(tracklet_nr):
        tracklet        = tracklets.getTracklet(i)
        left_coord      = tracklet.getLeftCoord()
        top_coord       = tracklet.getTopCoord()
        right_coord     = tracklet.getRightCoord()
        bottom_coord    = tracklet.getBottomCoord()
        tracklet_id     = tracklet.getId()
        tracklet_label  = labels[tracklet.getLabel()]
        tracklet_status = tracklet.getStatus()

        t = Trk(tracklet_id, tracklet_label, tracklet_status, left_coord, right_coord, top_coord, bottom_coord)

        newDet = show_changes(t)

        #print("left: {0} top: {1} right: {2}, bottom: {3}, id: {4}, label: {5}, status: {6} "\
        #     .format(left_coord, top_coord, right_coord, bottom_coord, tracklet_id, tracklet_label, tracklet_status))
        
        pt1 = left_coord,  top_coord
        pt2 = right_coord,  bottom_coord
        color = (255, 0, 0) # bgr
        cv2.rectangle(frame, pt1, pt2, color)

        middle_pt = (int)(left_coord + (right_coord - left_coord)/2), (int)(top_coord + (bottom_coord - top_coord)/2)
        cv2.circle(frame, middle_pt, 0, color, -1)
        cv2.putText(frame, "ID {0}".format(tracklet_id), middle_pt, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        x1, y1 = left_coord,  bottom_coord


        pt_t1 = x1, y1 - 40
        cv2.putText(frame, tracklet_label, pt_t1, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        pt_t2 = x1, y1 - 20
        cv2.putText(frame, tracklet_status, pt_t2, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        if newDet:
            cv2.imwrite("img/img_" + t.dt + ".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY, 10])

        
    return frame
