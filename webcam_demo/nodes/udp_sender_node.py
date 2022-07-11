# Copyright (c) OpenMMLab. All rights reserved.
from dataclasses import dataclass
from typing import List, Optional, Union

from mmpose.apis.webcam.utils import get_config_path
from mmpose.apis.webcam.nodes.node import Node
from mmpose.apis.webcam.nodes.registry import NODES

import socket
import struct
import array

@NODES.register_module()
class UdpSenderNode(Node):
    """
    Send a pose estimator result over UDP to target IP and port.
    Format:
    version - int32 (0)
    cameraid - int32
    number of objects - int32
    each object:
    [
        number of nodes - int32
        each node:
        [x coord (float), y coord (float)]
    ]

    Args:
        name (str): The node name (also thread name)
        input_buffer (str): The name of the input buffer
        ip: string
        port: int
        camera_id: int
        enable: bool
    """

    def __init__(self,
                 name: str,
                 input_buffer: str,
                 output_buffer: Union[str, List[str]],
                 ip: str,
                 port: int,
                 camera_id: int,
                 enable: bool = True):

        super().__init__(name=name, enable=enable)

        # Register buffers
        self.register_input_buffer(input_buffer, 'input', trigger=True)
        self.register_output_buffer(output_buffer)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.ip = ip
        self.port = port
        self.enable = enable
        self.camera_id = camera_id

    def process(self, input_msgs):
        input_msg = input_msgs['input']
        objects = input_msg.get_objects(lambda x: 'pose_model_cfg' in x)


        buffer = array.array('B')
        buffer.extend(struct.pack('i', 0))
        buffer.extend(struct.pack('i', self.camera_id))
        buffer.extend(struct.pack('i', len(objects)))
        for obj in objects :
            keypoints = obj['keypoints']
            buffer.extend(struct.pack('i', len(keypoints)))
            for keypoint in keypoints:
                buffer.extend(struct.pack('f',  keypoint[0]))
                buffer.extend(struct.pack('f',  keypoint[1]))
        
        self.sock.sendto(bytes(buffer), (self.ip, self.port))
        return input_msg