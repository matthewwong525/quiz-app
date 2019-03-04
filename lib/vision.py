from google.cloud import vision
from google.cloud.vision import types
from lib.Document import Document
import io
import os
#image processing resources
from skimage import img_as_float
from skimage.io import imread, imshow, imsave
from skimage.filters import gaussian, threshold_otsu
from skimage.feature import canny
from skimage.transform import probabilistic_hough_line, rotate

import numpy as np
from PIL import Image


def get_page_size(doc):
    # gets the size of the first page in document
    return doc.pages[0].width, doc.pages[0].height


def detect_document(path):
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    filename, file_extension = os.path.splitext(path)
    file_extension = file_extension.replace('.', '')
    if file_extension.lower() == 'jpg':
        file_extension = 'jpeg'
    rotated_content = deskew(content, file_extension)
    return load_document(rotated_content)

def load_document(content):
    client = vision.ImageAnnotatorClient()
    image = types.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation
    return document

def seperate_to_paragraphs(doc):
    breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType
    paragraph_list = []

    for page in doc.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                paragraph_text = ''
                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text + ' ' if symbol.property.detected_break.type in [breaks.SPACE, breaks.EOL_SURE_SPACE] else symbol.text for symbol in word.symbols
                    ])
                    if word.property.detected_languages and word.property.detected_languages[0].language_code == 'en':
                        paragraph_text += word_text
                paragraph_list.append((paragraph_text, paragraph.bounding_box))
    return paragraph_list

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

    # Convert image to PIL image to be rotated
    original_image = Image.open(io.BytesIO(content))
    rotated_image = original_image.rotate(rotation_number, expand=True)

    # Conver PIL obj to bytes
    with io.BytesIO() as output:
        rotated_image.save(output, format=ext)
        contents = output.getvalue()
    return contents


if __name__ == "__main__":
    doc = detect_document("/Users/matt/Desktop/pic1.jpg")
    word_list = seperate_to_paragraphs(doc)
    print([word.text for word in word_list])
    width, height = get_page_size(doc)
    #print(paragraph_list)
    #Document(paragraph_list, width, height).print()
