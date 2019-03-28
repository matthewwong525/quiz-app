from google.cloud import vision
from google.cloud.vision import types
from lib.Document import Document
from lib.Paragraph import ParagraphHelper
import io
import os
#image processing resources
from skimage import img_as_float
from skimage.io import imread, imshow, imsave
from skimage.filters import gaussian, threshold_otsu
from skimage.feature import canny
from skimage.transform import probabilistic_hough_line, rotate

import pdf2image

import numpy as np
from PIL import Image


def get_page_size(doc):
    # gets the size of the first page in document
    return doc.pages[0].width, doc.pages[0].height

def load_document(image, local=False):
    filename, file_extension = os.path.splitext(image.filename) if not local else os.path.splitext(image.name)
    file_extension = file_extension.replace('.', '')
    if file_extension.lower() == 'jpg':
        file_extension = 'jpeg'

    content = image.read()

    # converts pdf to jpg if it detects that the document is a pdf
    if file_extension.lower() == 'pdf':
        file_extension = 'jpeg'
        pdf_images = pdf2image.convert_from_bytes(content, fmt=file_extension)
        with io.BytesIO() as output:
            pdf_images[0].save(output, file_extension)
            content = output.getvalue()
        print('Converted PDF')


    rotated_content = deskew(content, file_extension)
    print('Rotated content')

    client = vision.ImageAnnotatorClient()
    image = types.Image(content=rotated_content)

    response = client.document_text_detection(image=image)
    if response.error.code != 0:
        return None
    print('Read image from vision API')
    return response.full_text_annotation

def get_width_height(bounding_box):
    width = abs(bounding_box.vertices[1].x - bounding_box.vertices[0].x)
    height = abs(bounding_box.vertices[2].y - bounding_box.vertices[1].y)

    return width, height

def deskew(content, ext):
    image = imread(content, plugin="imageio", as_gray=True)
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
        return content

    # Convert image to PIL image to be rotated
    original_image = Image.open(io.BytesIO(content))
    rotated_image = original_image.rotate(rotation_number, resample=Image.BICUBIC, expand=True)

    # Conver PIL obj to bytes
    with io.BytesIO() as output:
        rotated_image.save(output, format=ext)
        contents = output.getvalue()
    return contents

if __name__ == "__main__":
    path = "/Users/matt/Documents/quiz-app/photos of text/test.pdf"
    with io.open(path, 'rb') as image_file:
        doc = load_document(image_file)
    if not doc:
        print('Bad Image Data')
    
    p = ParagraphHelper(doc=doc)
    paragraph_list = p.get_paragraph_list()
    for paragraph in paragraph_list:
        print(paragraph['text'])
    p.print()
    document = Document(paragraph_list, p.avg_symbol_width, p.avg_symbol_height)
    document.print()
    
    #print(document.create_questions())

    #width, height = get_page_size(doc)
    #Document(paragraph_list, width, height).print()
