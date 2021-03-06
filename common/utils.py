import re
import glob
import numpy as np
import skvideo.io
from pathlib import Path
from common.camera import Camera
from common.motion_capture import MotionCapture


def convert_world_points_to_image_points(camera, world_points):
    """Convert world 3D points to image plane points.

    :param camera: camera's params
    :type camera: Camera
    :param world_points: World points (size, 3)
    :type world_points: numpy.ndarray
    :return: image plane points (size, 2)
    :rtype: numpy.ndarray of ints
    """
    translation_vector_expand = np.expand_dims(camera.translation_vector, axis=0)
    rot_tran_matrix = np.concatenate((camera.rotation_matrix, translation_vector_expand), axis=0)
    camera_matrix = np.dot(rot_tran_matrix, camera.intrinsic_matrix)
    image_points = np.zeros((world_points.shape[0], 2), dtype=int)

    for idx, val in enumerate(world_points):
        temp_matrix = np.append(val, 1)
        result = np.dot(temp_matrix, camera_matrix)
        u = result[0] / result[2]
        v = result[1] / result[2]
        image_points[idx, :] = [u, v]

    return image_points


def adapt_motion_data_for_video(motion_capture_data, camera, fps=30):
    """Adapt motion capture (MoCap) data for the video.

    :param motion_capture_data: motion capture data
    :param motion_capture_data: MotionCapture
    :param camera: camera's params
    :type camera: Camera
    :param fps: video frames per second
    :type fps: int
    :return: image plane points (video frames, motion points, 2)
    :rtype: np.ndarray
    """
    markers = motion_capture_data.get_joints_reduced_by_fps(fps)
    image_points = np.full((markers.shape[0], markers.shape[1], 2), 0, dtype=int)

    for i in range(0, markers.shape[1]):
        world_points = np.squeeze(markers[:, i, :])
        image_points[:, i] = convert_world_points_to_image_points(camera, world_points)

    return image_points


def read_camera_params(extrinsic_data_path, camera_data_path):
    """Read camera's parameters.

    :param extrinsic_data_path: path of the extrinsic data
    :param camera_data_path: path of the camera's data
    :return: camera's params
    :rtype: Camera
    """
    extrinsic_data = np.load(extrinsic_data_path)
    rotation_matrix = extrinsic_data['rotationMatrix']
    translation_vector = extrinsic_data['translationVector']

    camera_data = np.load(camera_data_path)
    intrinsic_matrix = camera_data['IntrinsicMatrix']
    return Camera(rotation_matrix, translation_vector, intrinsic_matrix)


def read_motion_capture_data(motion_capture_data_path):
    """Read motion capture data.

    :param motion_capture_data_path: path to the motion capture data
    :type motion_capture_data_path: str
    :return: motion capture data
    :rtype: MotionCapture
    """
    motion_capture_data = np.load(motion_capture_data_path, allow_pickle=True)
    joints = motion_capture_data['joints_location']
    skeleton = motion_capture_data['joints_parent']
    fps = 120  # Based on MoVi dataset description
    return MotionCapture(joints, skeleton, fps)


def read_video(video_path):
    """Read video data.

    :param video_path: path to the video
    :type video_path: str
    :return: video as array
    :rtype: numpy.ndarray
    """
    video = skvideo.io.vread(video_path)
    return video


def get_details_from_path(path):
    """Get details from the path.

    :param path: path to the file
    :type path: str
    :return:
        - name - usually it is 'Subject'
        - number - which subject is it
        - sub_number - which subject's movement is it
    """
    file_name = Path(path).stem
    numbers = [int(s) for s in file_name.split('_') if s.isdigit()]

    name = file_name[8:15]
    number = numbers[0]
    sub_number = numbers[1]
    return name, number, sub_number


def read_dataset(videos_dir, amass_dir):
    """Read dataset.

    :param videos_dir: videos directory
    :type videos_dir: str
    :param amass_dir: amass files directory
    :type amass_dir: str
    :return:
        - paths of the video
        - paths of the motion capture files
        - sub_number - which subject's movement is it
    """
    video_paths = glob.glob(videos_dir + '/*.avi')
    amass_paths = glob.glob(amass_dir + '/*.npz')

    videos_list = []
    motion_captures_list = []
    for path in amass_paths:
        name, number, sub_number = get_details_from_path(path)

        pattern = '.*{}_{}_.*_{}\.'.format(name, number, sub_number)
        r = re.compile(pattern)
        found_video_paths = list(filter(r.match, video_paths))
        if len(found_video_paths) == 1:
            # video = read_video(found_video_paths[0])
            # amass = read_motion_capture_data(path)
            videos_list.append(found_video_paths[0])
            motion_captures_list.append(path)

    return np.array(videos_list), np.array(motion_captures_list)
