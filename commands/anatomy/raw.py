from clint.textui import progress
from spiderpig import spiderpig
import json
import numpy
import pandas
from commands.all.raw import load_flashcards as load_flashcards_data
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from fma.graph import load_graph, load_ontology
import random


BROWSER = None


@spiderpig()
def load_term_id_mapping(data_dir):
    fma_ontology = load_ontology()
    fma_mapping = {}
    fma_name_fields = [
        'http://purl.org/sig/ont/fma/non-English_equivalent',
        'http://purl.org/sig/ont/fma/TA_ID',
    ]
    for fma_id, fma_term in fma_ontology['terms'].items():
        for name_field in fma_name_fields:
            for name in fma_term['info'].get(name_field, []):
                fma_mapping[name] = fma_id.replace('http://purl.org/sig/ont/fma/fma', '')
    flashcards = load_flashcards()
    terms = []
    for term in flashcards['terms']:
        to_save = {}
        fma_id = fma_mapping.get(term['id'])
        if fma_id is not None:
            to_save['fma_id'] = fma_id
        else:
            for v in term['name-la'].split(';'):
                fma_id = fma_mapping.get(v)
                if fma_id is None:
                    continue
                if 'fma_id' in to_save and to_save['fma_id'] != fma_id:
                    raise Exception('FMA ID is not unique based on latin name.')
                to_save['fma_id'] = fma_id
        for key, value in term.items():
            to_save['anatom_{}'.format(key.replace('-', '_'))] = value
        if 'fma_id' in to_save:
            to_save['fma_name'] = fma_ontology['terms']['http://purl.org/sig/ont/fma/fma{}'.format(to_save['fma_id'])]['info']['http://purl.org/sig/ont/fma/preferred_name'][0]
        terms.append(to_save)
    return pandas.DataFrame(terms)


@spiderpig()
def load_flashcards(data_dir):
    with open('{}/flashcards.json'.format(data_dir)) as f:
        return json.load(f)


@spiderpig()
def load_context(context_id):
    data = load_flashcards()
    context = [c for c in data['contexts'] if c['id'] == context_id][0]
    context['content'] = json.loads(context['content'])
    context['flashcards'] = [f for f in data['flashcards'] if f['context'] == context['id']]
    return context


@spiderpig()
def load_search_results(context_id=None):
    flashcards = load_flashcards_data()
    if context_id is not None:
        flashcards = flashcards[flashcards['context_id'] == context_id]
    to_process = list(flashcards[['term_id', 'term_name']].drop_duplicates().dropna(subset=['term_name']).values)
    random.shuffle(to_process)
    global BROWSER
    BROWSER = Firefox()
    try:
        result = []
        for term_id, term_name in progress.bar(to_process):
            result.append(_load_search_results_apply(term_id, term_name))
        return pandas.DataFrame(result)
    finally:
        BROWSER.quit()


@spiderpig()
def _load_search_results_apply(term_id, term_name):
    if ';' in term_name:
        term_name = term_name.split(';')[0]
    global BROWSER
    BROWSER.get('https://www.google.com/search?q={}'.format(term_name))
    while True:
        try:
            stats = WebDriverWait(BROWSER, 60).until(EC.presence_of_element_located((By.ID, 'resultStats'))).text
            if 'About' in stats:
                count = int(stats.split(' ')[1].replace(',', ''))
            else:
                count = int(stats.split(':')[1].split('(')[0].replace(' ', ''))
            return {
                'identifier': term_id,
                'search_results': count,
                'search_results_log': numpy.log(count),
            }
        except Exception as e:
            import traceback
            traceback.print_exc(e)
            sleep(5)
