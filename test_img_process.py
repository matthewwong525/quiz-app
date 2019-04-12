from os import walk, system
from os.path import isfile, join, splitext


import io
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib.Vision import Vision
from lib.Document import Document
from lib.Paragraph import ParagraphHelper
from lib.Quizlet import Quizlet

from anytree import RenderTree
from anytree.exporter import DictExporter
import requests


env = Environment(
    loader=FileSystemLoader(searchpath="./frontend"),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template('test_result_template.html')




def test_case(path):
    results = {}
    tests = [False, False, False, False, False]
    test_defs = ['Created vision object', 'Create and initialized paragraph_list', 'Created Document object',
                'Found terms and definitions', 'Called Quizlet API']

    results = {
        'file_name' : '',
        'file_ext': '',
        'image_scale': 1,
        'avg_symbol_width': 0,
        'avg_symbol_height': 0,
        'doc_structure': '',
        'annotation_list': [],
        'error': '',
        'terms': [],
        'definitions': [],
        'quizlet_url': ''
    }

    with io.open(path, 'rb') as image_file:
        file_name, file_ext = splitext(image_file.name)
        results['file_name'] = file_name
        results['file_ext'] = file_ext

        vis = Vision(image_file, True)

    results['orig_pic'] = vis.orig_img_bytes
    results['process_pic'] = vis.process_img_bytes

    print('--------------------------- BEGIN TEST FOR %s' % (file_name+file_ext))


    tests[0] = True

    if not hasattr(vis, 'word_list'):
        results['error'] = "No `word_list` created from Vision Class"
        print_tests(tests, test_defs)
        return results

    results['image_scale'] = vis.image_scale
    #results['doc_border'] = vis.doc_border

    p = vis.get_paragraph_helper()
    paragraph_list = p.get_paragraph_list()

    tests[1] = True

    d = Document(paragraph_list, p.avg_symbol_width, p.avg_symbol_height)
    results['avg_symbol_width'] = d.symbol_width
    results['avg_symbol_height'] = d.symbol_height
    #results['doc_structure'] = DictExporter().export(d.root_node)
    results['doc_structure'] = RenderTree(d.root_node).by_attr("text")
    results['annotation_list'] = d.annotation_list


    tests[2] = True

    terms, definitions = d.create_questions()
    if not (terms and definitions):
        results['error'] = "No terms and definitions from Document.create_questions()"
        print_tests(tests, test_defs)
        return results

    tests[3] = True
    results['terms'] = terms
    results['definitions'] = definitions

    quizlet_client = Quizlet(terms, definitions)
    resp = quizlet_client.create_set(vis.file_name + " Question Set")

    if not resp or resp.status_code >= 400:
        results['error'] = "Quizlet failed to send response to creating test set"
        print_tests(tests, test_defs)
        return results

    tests[4] = True

    results['quizlet_url'] = resp.json()['url']


    print_tests(tests, test_defs)

    print('--------------------------- END TEST')
    print('')

    return results

def print_tests(tests, test_defs):
    for test, test_def in zip(tests, test_defs):
        print("***%s: %s" % (test_def, test)) if test else print("|||%s: %s" % (test_def, test))



if __name__ == "__main__":
    mypath = 'test_imgs/'
    files = []

    ignore_dirs = ['processed', 'not_working']

    for (dirpath, dirnames, filenames) in walk(mypath):
        if dirpath.replace(mypath, '').split('/')[0] not in ignore_dirs:
            files.extend([ dirpath+'/'+file for file in filenames if file != '.DS_Store'])
        

    result_list = []
    for file in files:
        result = test_case(file)
        result['orig_file_path'] = '../' + file
        result['process_file_path'] = mypath + "processed%s" % (file.replace(mypath,'/'))
        result['terms_n_defs'] = zip(result['terms'], result['definitions'])
        with open(result['process_file_path'], "wb+") as fh:
            fh.write(result['process_pic'])
        result['process_file_path'] = '../' + result['process_file_path']
        result_list.append(result)


    output = template.render(results=result_list, zip=zip)
    with open("frontend/test_results.html", "w") as fh:
        fh.write(output)
        
"""
    with open('results.json', 'w') as outfile:
        json.dump(result, outfile, sort_keys=True, indent=4)
"""

        

