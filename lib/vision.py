from google.cloud import vision
from google.cloud.vision import types
import io


def detect_document(path):
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    return load_document(content)

def load_document(content):
    client = vision.ImageAnnotatorClient()
    image = types.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation
    print(document)
    return document.text
