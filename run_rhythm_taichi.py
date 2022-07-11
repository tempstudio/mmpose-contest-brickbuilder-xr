# Copyright (c) OpenMMLab. All rights reserved.

import array
import logging
import socket
import struct
import sys
from argparse import ArgumentParser
from enum import IntEnum
import threading
import time
from time import sleep
from itertools import zip_longest
from mmpose.core import imshow_bboxes, imshow_keypoints

from mmcv import Config, DictAction
from mmpose.apis.webcam import WebcamExecutor
from mmdet.apis import inference_detector, init_detector

from mmpose.apis import (get_track_id, inference_top_down_pose_model,
                         init_pose_model)
import cv2

sys.path.append('.')
from webcam_demo import *  # noqa


def parse_args():
    parser = ArgumentParser('Webcam executor configs')
    parser.add_argument('--config',
                        type=str,
                        default='configs/pose_estimation/pose_estimation.py')

    parser.add_argument(
        '--cfg-options',
        nargs='+',
        action=DictAction,
        default={},
        help='Override settings in the config. The key-value pair '
        'in xxx=yyy format will be merged into config file. For example, '
        "'--cfg-options executor_cfg.camera_id=1'")
    parser.add_argument('--debug',
                        action='store_true',
                        help='Show debug information')

    return parser.parse_args()


class TCP_MESSAGE_TYPE (IntEnum):
    STRING_MESSAGE = 100,
    KEEP_ALIVE_MESSAGE = 300,


def send_tcp_message(socket, payload, message_type):
    header = array.array('B')

    # 32 byte header -> payload -> padding to match 32 byte

    header.extend(struct.pack('i', int(message_type)))
    header.extend(struct.pack('q', len(payload)))
    header.extend(b"\0"*(32 - len(header))) 

    paddingByteCount = 32 - len(payload) % 32

    socket.sendall(header)
    socket.sendall(payload)
    socket.sendall(b"\0"*paddingByteCount)

def keep_alive_tcp(cfg, stop):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (cfg.server_ip, 9001)
    sock.connect(server_address)
    # First hand shake is string message
    send_tcp_message(sock, bytes("172.19.100.72", 'utf-8'), TCP_MESSAGE_TYPE.STRING_MESSAGE)
    sleep(1)

    keep_alive_payload = array.array('B')
    keep_alive_payload.extend(struct.pack('b', 5))
    while not stop(): 
        send_tcp_message(sock, keep_alive_payload, TCP_MESSAGE_TYPE.KEEP_ALIVE_MESSAGE)
        sleep(1)

def post_process_det(preds, classes, thr):
    """Post-process the predictions of MMDetection model."""
    if isinstance(preds, tuple):
        dets = preds[0]
        segms = preds[1]
    else:
        dets = preds
        segms = [[]] * len(dets)

    assert len(dets) == len(classes)
    assert len(segms) == len(classes)

    objects = []

    for i, (label, bboxes, masks) in enumerate(zip(classes, dets, segms)):

        for bbox, mask in zip_longest(bboxes, masks):
            if bbox[4] < thr or label != 'person':
                continue
            obj = {
                'class_id': i,
                'label': label,
                'bbox': bbox,
                'mask': mask,
            }
            objects.append(obj)

    return objects


def inverse_lerp( a, b, v):
    return (v - a) / (b - a)

def send_empty_message(sock, ip):
    buffer = array.array('B')
    buffer.extend(struct.pack('i', 0))
    buffer.extend(struct.pack('l',  time.time_ns()))

    buffer.extend(struct.pack('f',  0))
    buffer.extend(struct.pack('f',  0))
    buffer.extend(struct.pack('i',  -1))
    buffer.extend(struct.pack('f',  0))
    buffer.extend(struct.pack('f',  0))
    buffer.extend(struct.pack('i',  -1))
    sock.sendto(bytes(buffer), (ip, 9002))


# The webcam framework isn't fast enough for this (default 30fps cap, too many threads and sleeps)
# So unrolling everything by hand, below

def run():
    args = parse_args()
    cfg = Config.fromfile(args.config)
    cfg.merge_from_dict(args.cfg_options)
    stop = False
    cfg = cfg.config
    tcp_worker = threading.Thread(target = keep_alive_tcp, args =(cfg, lambda : stop))
    tcp_worker.start()
    if args.debug:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

    det_model_config = cfg.det_model_config
    det_model_checkpoint = cfg.det_model_checkpoint
    det_model = init_detector(
        det_model_config,
        det_model_checkpoint)
    classes = det_model.CLASSES

    pose_model_config = cfg.pose_model_config
    pose_model_checkpoint = cfg.pose_model_checkpoint

    pose_model = init_pose_model(
            pose_model_config,
            pose_model_checkpoint)

    vcap = cv2.VideoCapture(cfg.camera_id)
    if not vcap.isOpened():
        print(f'Cannot open camera ')
        sys.exit()
    do_det = cfg.detection_interval
    objects_det = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    ip = cfg.server_ip
    
    width = 0
    height = 0
    smoothed_confidence = 1
    xScaling = 0.1
    ySclaing = 0.2
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    recorder = None
    try:
        while True:
            start = time.time()
            ret_val, frame = vcap.read()
            if (width == 0):
                width = frame.shape[1]
                height = frame.shape[0]
                recorder = cv2.VideoWriter(cfg.video_file_name, fourcc, 45, (width, height))
                print ((width, height))
            t1 = time.time()
            if ret_val:
                if do_det >= cfg.detection_interval:
                    preds = inference_detector(det_model, frame)
                    new_objects_det = post_process_det(preds, classes, cfg.bbox_thr)
                    if (len(new_objects_det) > 0): 
                        objects_det = new_objects_det
                    do_det = 0
                do_det += 1
                t2 = time.time()
                objects_pose, _ = inference_top_down_pose_model(
                    pose_model,
                    frame,
                    objects_det,
                    bbox_thr= cfg.bbox_thr,
                    format='xyxy')
                end = time.time()

                if (len(objects_pose) > 0 and len(objects_pose[0]['keypoints']) > 0):
                    keypoints = objects_pose[0]['keypoints']
                    leftHandPos = keypoints[9]
                    rightHandPos = keypoints[10]
                    confidence = min(leftHandPos[2], rightHandPos[2])
                    cv2.circle(frame, (int(leftHandPos[0]), int(leftHandPos[1])), 4,(255, 0, 0), -1)
                    cv2.circle(frame, (int(rightHandPos[0]), int(rightHandPos[1])), 4,(0, 0, 255), -1)

                    if cfg.block_face:
                        nosePos = keypoints[0]
                        startX = int(nosePos[0] - width / 8)
                        endX = int(nosePos[0] + width / 8)
                        startY = int(nosePos[1] - width / 8)
                        endY = int(nosePos[1] + width / 8)
                        cv2.rectangle(frame, (startX, startY), (endX, endY), (0,0,0),-1)

                    smoothed_confidence = smoothed_confidence * 0.9 + confidence * 0.1
                    if (smoothed_confidence < 0.2):
                        send_empty_message(sock, ip)
                        continue
                    leftX = 1 - inverse_lerp(xScaling, 1 - xScaling, leftHandPos[0] / width)


                    leftY = 1 - inverse_lerp(ySclaing, 1 - ySclaing, leftHandPos[1] / height)

                    rightX = 1 - inverse_lerp(xScaling, 1 - xScaling, rightHandPos[0] / width)
                    rightY = 1 - inverse_lerp(ySclaing, 1 - ySclaing, rightHandPos[1] / height)
                    
                    buffer = array.array('B')
                    buffer.extend(struct.pack('i', 0))
                    buffer.extend(struct.pack('l',  time.time_ns()))

                    buffer.extend(struct.pack('f',  leftX))
                    buffer.extend(struct.pack('f',  leftY))
                    buffer.extend(struct.pack('i',  0))
                    buffer.extend(struct.pack('f',  rightX))
                    buffer.extend(struct.pack('f',  rightY))
                    buffer.extend(struct.pack('i',  1))
                    sock.sendto(bytes(buffer), (ip, 9002))
                    touch_pending = True
                    #print((leftX, leftY, rightX, rightY))
                else:
                    send_empty_message(sock, ip)
                t4 = time.time()
                if cfg.record_video:
                    recorder.write(frame)
                cv2.imshow("frame", frame)
                cv2.waitKey(1)
                t5 = time.time()
                # print ((t1 - start, t2 - t1, end - t2, t4 - end, t5 - t4))
    except KeyboardInterrupt:
        pass
    stop = True
    recorder.release()


if __name__ == '__main__':
    run()
