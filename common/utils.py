import numpy as np
import scipy.io as sio
from common.camera import Camera
from common.motion_capture import MotionCapture


def convert_world_points_to_image_points(camera, world_points):
    """Convert world 3D points to image plane points.

    :param camera: camera's params
    :type camera: Camera
    :param world_points: World points (size, 3)
    :type world_points: np.ndarray
    :return: image plane points (size, 2)
    :rtype: np.ndarray of ints
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


def read_motion_capture_data(motion_capture_data_path, movement_number):
    """Read motion capture data.

    :param motion_capture_data_path: path to the motion capture data
    :type motion_capture_data_path: str
    :param movement_number: number of the motion capture movement
    :type movement_number: int
    :return: motion capture data
    :rtype: MotionCapture
    """
    assert movement_number - 1 >= 0, 'Movement number has to start from 1.'

    motion_capture_data = sio.loadmat(motion_capture_data_path, simplify_cells=True)
    key = [key for key in motion_capture_data.keys() if key.startswith('Subject')][0]
    motion_capture_data = motion_capture_data[key]['move'][movement_number - 1]
    joints = motion_capture_data['jointsLocation_amass']
    skeleton = motion_capture_data['jointsParent']
    fps = 120  # Based on MoVi dataset description
    return MotionCapture(joints, skeleton, fps)