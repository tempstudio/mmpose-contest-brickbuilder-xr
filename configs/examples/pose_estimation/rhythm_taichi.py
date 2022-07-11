config = dict(
    camera_id="http://192.168.31.129:9002/video",
    det_model_config = "model_configs/mmdet/ssdlite_mobilenetv2_scratch_600e_coco.py",
    det_model_checkpoint = "https://download.openmmlab.com/mmdetection/v2.0/ssd/ssdlite_mobilenetv2_scratch_600e_coco/ssdlite_mobilenetv2_scratch_600e_coco_20210629_110627-974d9307.pth",
    pose_model_config = 'model_configs/mmpose/body/2d_kpt_sview_rgb_img/topdown_heatmap/coco/mobilenetv2_coco_384x288.py',
    pose_model_checkpoint = 'https://download.openmmlab.com/mmpose/top_down/mobilenetv2/mobilenetv2_coco_384x288-26be4816_20200727.pth',
    detection_interval = 10,
    bbox_thr = 0.2,
    server_ip = '172.19.96.1',
    record_video = True,
    block_face = True,
    video_file_name = "recording.mp4"
)
