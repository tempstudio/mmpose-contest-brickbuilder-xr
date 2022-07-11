# Copyright (c) OpenMMLab. All rights reserved.
executor_cfg = dict(
    # Basic configurations of the executor
    name='Pose Estimation',
    camera_id="http://192.168.31.175:56000/mjpeg",
    # Define nodes.
    # The configuration of a node usually includes:
    #   1. 'type': Node class name
    #   2. 'name': Node name
    #   3. I/O buffers (e.g. 'input_buffer', 'output_buffer'): specify the
    #       input and output buffer names. This may depend on the node class.
    #   4. 'enable_key': assign a hot-key to toggle enable/disable this node.
    #       This may depend on the node class.
    #   5. Other class-specific arguments
    nodes=[
        # 'DetectorNode':
        # This node performs object detection from the frame image using an
        # MMDetection model.
          dict(
               type='DetectorNode',
               name='detector',
               model_config='model_configs/mmdet/'
               'ssdlite_mobilenetv2_scratch_600e_onehand.py',
               model_checkpoint='https://download.openmmlab.com/mmpose/'
               'mmdet_pretrained/'
               'ssdlite_mobilenetv2_scratch_600e_onehand-4f9f8686_20220523.pth',
               input_buffer='_input_',
               output_buffer='det_result',
               multi_input=True),
        dict(type='TopDownPoseEstimatorNode',
             name='human pose estimator',
             model_config='model_configs/mmpose/hand/2d_kpt_sview_rgb_img/topdown_heatmap/coco_wholebody_hand/'
             'mobilenetv2_coco_wholebody_hand_256x256.py',
             model_checkpoint='https://download.openmmlab.com/mmpose/hand/mobilenetv2/mobilenetv2_coco_wholebody_hand_256x256-06b8c877_20210909.pth',
             labels=['hand'],
             smooth=False,
             input_buffer='det_result',
             output_buffer='animal_pose'),
        # 'ObjectAssignerNode':
        # This node binds the latest model inference result with the current
        # frame. (This means the frame image and inference result may be
        # asynchronous).
        dict(
            type='ObjectAssignerNode',
            name='object assigner',
            frame_buffer='_frame_',  # `_frame_` is an executor-reserved buffer
            object_buffer='animal_pose',
            output_buffer='frame'),
        # 'ObjectVisualizerNode':
        # This node draw the pose visualization result in the frame image.
        # Pose results is needed.
        dict(type='ObjectVisualizerNode',
             name='object visualizer',
             enable_key='v',
             enable=True,
             show_bbox=True,
             must_have_keypoint=False,
             show_keypoint=True,
             input_buffer='frame',
             output_buffer='vis_notice'),
        dict(type='UdpSenderNode',
             name='udp_sender',
             enable=True,
             ip='172.19.96.1',
             port=10001,
             input_buffer='vis_notice',
             output_buffer='sender',
             camera_id = 0),
        # 'MonitorNode':
        # This node show diagnostic information in the frame image. It can
        # be used for debugging or monitoring system resource status.
        dict(type='MonitorNode',
             name='monitor',
             enable_key='m',
             enable=False,
             input_buffer='sender',
             output_buffer='display'),
        # 'RecorderNode':
        # This node save the output video into a file.
        dict(type='RecorderNode',
             name='recorder',
             out_video_file='webcam_demo.mp4',
             input_buffer='display',
             output_buffer='_display_'
             # `_display_` is an executor-reserved buffer
             )
    ])
