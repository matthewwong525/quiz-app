from google.cloud import vision
from google.cloud.vision import types
from Document import Document
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
    return document

def seperate_to_paragrpahs(doc):
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
                    paragraph_text += word_text
                paragraph_list.append((paragraph_text, paragraph.bounding_box))
    return paragraph_list


if __name__ == "__main__":
    doc = detect_document("/Users/matt/Documents/y-hack-2017/photos of text/pic1.jpg")
    paragraph_list = seperate_to_paragrpahs(doc)
    #print(paragraph_list)
    Document(paragraph_list).print()
