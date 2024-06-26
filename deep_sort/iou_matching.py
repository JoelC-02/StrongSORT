#GIoU
from __future__ import absolute_import
import numpy as np
from . import linear_assignment
import math
import paddle

def iou(bbox, candidates):
    """Compute intersection over union.

    Parameters
    ----------
    bbox : ndarray
        A bounding box in format `(top left x, top left y, width, height)`.
    candidates : ndarray
        A matrix of candidate bounding boxes (one per row) in the same format
        as `bbox`.

    Returns
    -------
    ndarray
        The intersection over union in [0, 1] between the `bbox` and each
        candidate. A higher score means a larger fraction of the `bbox` is
        occluded by the candidate.

    """
    bbox_x1, bbox_y1, bbox_w, bbox_h = bbox
    candidates_x1, candidates_y1, candidates_w, candidates_h = candidates[:, 0], candidates[:, 1], candidates[:, 2], candidates[:, 3]

    bbox_x1_tensor = paddle.to_tensor(bbox_x1)
    candidates_x1_tensor = paddle.to_tensor(candidates_x1)

    xkis1 = paddle.maximum(bbox_x1_tensor, candidates_x1_tensor)
    ykis1 = paddle.maximum(paddle.to_tensor(bbox_y1), paddle.to_tensor(candidates_y1))
    xkis2 = paddle.minimum(paddle.to_tensor(bbox_x1) + paddle.to_tensor(bbox_w), paddle.to_tensor(candidates_x1) + paddle.to_tensor(candidates_w))
    ykis2 = paddle.minimum(paddle.to_tensor(bbox_y1) + paddle.to_tensor(bbox_h), paddle.to_tensor(candidates_y1) + paddle.to_tensor(candidates_h))
    
    w_inter = paddle.clip(xkis2 - xkis1, min=0)
    h_inter = paddle.clip(ykis2 - ykis1, min=0)
    overlap = w_inter * h_inter

    area1 = bbox_w * bbox_h
    area2 = candidates_w * candidates_h
    union = area1 + area2 - overlap + 1e-7
    
    iou = overlap / union

    return iou

def iou_cost(tracks, detections, track_indices=None,
             detection_indices=None):
    """An intersection over union distance metric.

    Parameters
    ----------
    tracks : List[deep_sort.track.Track]
        A list of tracks.
    detections : List[deep_sort.detection.Detection]
        A list of detections.
    track_indices : Optional[List[int]]
        A list of indices to tracks that should be matched. Defaults to
        all `tracks`.
    detection_indices : Optional[List[int]]
        A list of indices to detections that should be matched. Defaults
        to all `detections`.

    Returns
    -------
    ndarray
        Returns a cost matrix of shape
        len(track_indices), len(detection_indices) where entry (i, j) is
        `1 - iou(tracks[track_indices[i]], detections[detection_indices[j]])`.

    """
    if track_indices is None:
        track_indices = np.arange(len(tracks))
    if detection_indices is None:
        detection_indices = np.arange(len(detections))

    cost_matrix = np.zeros((len(track_indices), len(detection_indices)))
    for row, track_idx in enumerate(track_indices):
        if tracks[track_idx].time_since_update > 1:
            cost_matrix[row, :] = linear_assignment.INFTY_COST
            continue

        bbox = tracks[track_idx].to_tlwh()
        candidates = np.asarray([detections[i].tlwh for i in detection_indices])
        cost_matrix[row, :] = 1. - iou(bbox, candidates)
    return cost_matrix
