# import the necessary packages
import numpy as np
import cv2
 
def order_points(pts):

    pts = pts.reshape((4,2))
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype = "float32")
 
    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
 
    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
 
    # return the ordered coordinates
    return rect

def four_point_transform(image, pts):
    # obtain a consistent order of the points and unpack them
    # individually
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
 
    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
 
    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
 
    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = "float32")
 
    # compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
 
    # return the warped image
    return warped

def check_in_polygon(pt, polygon_pts):
    """
    Uses the ray casting algorithm to check if a point is in
    the polygon. 

    Args:
        pt (tuple): x,y coordinate of point to be analyzed
        polygon_pts (list): the points in the polygon
        image_scale (int): the scale the polygon box should be scaled to

    Returns:
        in_polygon (bool): a bool that indicates if the point is in the polygon
    """
    # get list of slopes connecting points
    slope_list = [ get_slope(polygon_pts, i) for i, poly_pt in enumerate(polygon_pts) ]
    # loops each slope and check if point crosses slope to the right
    slope_cross_list = []
    for slope in slope_list:
        if 'slope' in slope:
            is_cross_slope =  pt[0] < (pt[1]-slope['b'])/slope['slope'] < slope['max_x']
        else:
            if 'same_x' in slope:
                is_cross_slope = pt[0] < slope['same_x']
            else:
                is_cross_slope = False
        slope_cross_list.append(is_cross_slope)
        
    num_slope_cross = sum(slope_cross_list)
    in_polygon = False if num_slope_cross == 0 else bool(num_slope_cross%2)

    return in_polygon
    

def get_slope(polygon_pts, i, image_scale=1):
    """
    Finds slope from current to next point and returns object
    """
    sec_pt_idx = i+1 if i+1 != len(polygon_pts) else 0
    y2 = polygon_pts[sec_pt_idx][1]
    y1 = polygon_pts[i][1]
    x2 = polygon_pts[sec_pt_idx][0]
    x1 = polygon_pts[i][0]

    if x2 == x1:
        return { 'same_x': x1 }
    if y2 == y1:
        return { 'same_y': y1 }

    slope = (y2-y1)/(x2-x1)
    b = y1 - slope*x1 

    return { 'slope': slope, 'b': b, 'max_x': max(x1, x2) }
