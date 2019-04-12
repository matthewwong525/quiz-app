from google.cloud import vision
from google.cloud.vision import types
from lib.Document import Document
from lib.Paragraph import ParagraphHelper
from lib.scripts import mapper

import pdf2image
import cv2
import io
import os

import numpy as np
from PIL import Image

#image processing resources
from skimage import img_as_float
from skimage.io import imread, imshow, imsave
from skimage.filters import gaussian, threshold_otsu
from skimage.feature import canny
from skimage.transform import probabilistic_hough_line


class Vision():
    def __init__(self, img_file, local=False):
        """
        Initalizes the Vision object

        Args:
            img_file (obj): the image object read from the server or locally
            local (bool): flag to determine if image is read locally

        TODO:
            * Make it get multiple pages of PDF documents later!!!
        """

        # finds file extension here
        file_name, file_ext = os.path.splitext(img_file.filename) if not local else os.path.splitext(img_file.name)
        file_ext = file_ext.replace('.', '')
        if file_ext.lower() == 'jpg':
            file_ext = 'jpeg'

        content = img_file.read()

        # converts pdf to jpg if it detects that the document is a pdf
        if file_ext.lower() == 'pdf':
            file_ext = 'jpeg'
            pdf_images = pdf2image.convert_from_bytes(content, fmt=file_ext)
            with io.BytesIO() as output:
                # gets first page of pdf document!
                pdf_images[0].save(output, file_ext)
                content = output.getvalue()

        self.file_ext = file_ext
        self.file_name = file_name
        self.orig_img_bytes = content
        self.process_img_bytes = content

        paragraph_helper = self.get_paragraph_helper()
        if paragraph_helper and hasattr(paragraph_helper, 'word_list'):
            self.word_list = paragraph_helper.word_list
        else:
            return None

        # image pre-processing done here
        self.image_scale = 1
        self.doc_border = self.get_doc_border()
        if self.all_words_in_doc():
            self.correct_perspective()
        self.deskew()


    def get_paragraph_helper(self):
        """
        Gets a list of words from the vision API

        Returns:
            word_list (list): a list of words from the vision API
        """

        # initializes client and sends request to Vision API
        client = vision.ImageAnnotatorClient()
        image = types.Image(content=self.process_img_bytes)
        response = client.document_text_detection(image=image)

        # THROW ERROR FLASK here
        if response.error.code != 0:
            return None

        return ParagraphHelper(doc=response.full_text_annotation)

    def get_doc_border(self):
        """
        Gets the borders around the page in the image using edge detection

        Returns:
            rect(list): 4 points representing polygon containing the document
        """

        # read in the image
        nparr = np.frombuffer(self.orig_img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # cv2.IMREAD_COLOR in OpenCV 3.1

        # resizing because opencv does not work well with bigger images
        # add logic to resize only if greater than certain size
        height, width = image.shape[:2]
        max_pix_area = 1000*1000

        if height*width > max_pix_area:
            while (height*width)/self.image_scale > max_pix_area: self.image_scale += 1
            # find image scale by finding an integer value taht
            image=cv2.resize(image,(int(width/self.image_scale),int(height/self.image_scale)))

        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)  #RGB To Gray Scale
        blurred=cv2.GaussianBlur(gray,(5,5),0)  #(5,5) is the kernel size and 0 is sigma that determines the amount of blur
        
        # find OTSU threshold for Canny edge detection
        ret, thres = cv2.threshold(blurred,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # Canny edge
        edged=cv2.Canny(blurred,ret*0.2,ret)  

        # Find external contours only
        contours, hierarchy=cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  #retrieve the contours as a list, with simple apprximation model
        largest_contour = max(contours,key=lambda c: cv2.arcLength(c,True))

        # Create a hull from the contours (draws a polygon around the points to reduce it to 4 points)
        hull = cv2.convexHull(largest_contour, False)

        pts=cv2.approxPolyDP(hull, 0.02*cv2.arcLength(hull, True), True)
        if len(pts) != 4:
            return None

        rect = mapper.order_points(pts)
        return rect * self.image_scale

    def correct_perspective(self):
        """
        Performs perspective transform and updates orig_img_bytes attribute
        """

        nparr = np.frombuffer(self.orig_img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        persp_pic = mapper.four_point_transform(image, self.doc_border)
        persp_pic = cv2.cvtColor(persp_pic,cv2.COLOR_BGR2RGB)

        persp_img = Image.fromarray(persp_pic, 'RGB')
        with io.BytesIO() as output:
            persp_img.save(output, format=self.file_ext)
            self.process_img_bytes = output.getvalue()

    def all_words_in_doc(self):
        """
        Checks if all words from word list are in document border
        """

        if self.doc_border is None:
            return False
        for word in self.word_list:
            for p in word['bounding_box'].vertices:
                if not mapper.check_in_polygon((p.x, p.y), self.doc_border):
                    print("%s.%s" % (self.file_name, self.file_ext))
                    print(word['text'])
                    print(p)
                    return False
        return True


    def deskew(self):
        """
        Deskews the image so that the text is aligned upright.
        The skew process does not take into account images that are
        skewed more than 45 degrees.

        Args:
            content (bytes): image content in bytes
            ext (string): extension of the image

        Returns:
            contents (bytes): rotated image in bytes
        """
        image = imread(self.process_img_bytes, plugin="imageio", as_gray=True)

        #threshold to get rid of extraneous noise
        thresh = threshold_otsu(image)
        normalize = image > thresh

        # gaussian blur
        blur = gaussian(normalize, 3)

        # canny edges in scikit-image
        edges = canny(blur)

        # hough lines
        hough_lines = probabilistic_hough_line(edges)

        # hough lines returns a list of points, in the form ((x1, y1), (x2, y2))
        # representing line segments. the first step is to calculate the slopes of
        # these lines from their paired point values
        slopes = [(y2 - y1)/(x2 - x1) if (x2-x1) else 0 for (x1,y1), (x2, y2) in hough_lines]

        # it just so happens that this slope is also y where y = tan(theta), the angle
        # in a circle by which the line is offset
        rad_angles = [np.arctan(x) for x in slopes]

        # and we change to degrees for the rotation
        deg_angles = [np.degrees(x) for x in rad_angles]

        # which of these degree values is most common?
        histo = np.histogram(deg_angles, bins=180)
        
        # correcting for 'sideways' alignments
        rotation_number = histo[1][np.argmax(histo[0])]

        if rotation_number > 45:
            rotation_number = -(90-rotation_number)
        elif rotation_number < -45:
            rotation_number = 90 - abs(rotation_number)

        if abs(rotation_number) < 0.3:
            return True

        # Convert image to PIL image to be rotated
        original_image = Image.open(io.BytesIO(self.process_img_bytes))
        rotated_image = original_image.rotate(rotation_number, resample=Image.BICUBIC, expand=True)

        # Convert PIL obj to bytes
        with io.BytesIO() as output:
            rotated_image.save(output, format=self.file_ext)
            self.process_img_bytes = output.getvalue()



if __name__ == "__main__":
    path = "/Users/matt/Documents/quiz-app/photos of text/test12.jpg"
    with io.open(path, 'rb') as image_file:
        v = Vision(image_file, True)
    if not v:
        print('Bad Image Data')

