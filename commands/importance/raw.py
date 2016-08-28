from spiderpig import spiderpig
import numpy
import pandas
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from clint.textui import progress
from time import sleep


@spiderpig()
def load_search_results(n=None):
    result = []
    try:
        terms = load_terms()
        if n is not None:
            terms = terms.head(n=n)
        browser = webdriver.Firefox()
        for term_id, term_name in progress.bar(terms[['identifier', 'name']].values):
            if ';' in term_name:
                term_name = term_name.split(';')[0]
            while True:
                browser.get('https://www.google.com/search?q={}'.format(term_name))
                try:
                    stats = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, 'resultStats'))).text
                except TimeoutException:
                    browser.quit()
                    sleep(10)
                    browser = webdriver.Firefox()
                    continue
                try:
                    count = int(stats.split(':')[1].split('(')[0].replace(' ', ''))
                except Exception:
                    print(stats)
                    raise Exception()
                result.append({
                    'identifier': term_id,
                    'search_results': count,
                    'search_results_log': numpy.log(count),
                })
                break
    finally:
        browser.quit()
    return pandas.DataFrame(result)


@spiderpig()
def load_terms(data_dir='data'):
    difficulty = pandas.read_csv('{}/term_difficulty.csv'.format(data_dir), index_col=False)
    difficulty['difficulty_prob'] = difficulty['difficulty'].apply(lambda d: 1.0 / (1 + numpy.exp(d)))
    answers = pandas.read_csv('{}/term_answers.csv'.format(data_dir), index_col=False)
    return pandas.merge(difficulty, answers[['identifier', 'answers']], on=['identifier'])
