from .raw import load_and_merge
from metric import binomial_confidence_mean
from spiderpig import spiderpig
import json
import output
import pandas
import seaborn as sns


def filter_size(practice_filter_content):
    pfilter = json.loads(practice_filter_content)

    def _size(xs):
        if len(xs) == 0:
            return 0
        if isinstance(xs[0], list):
            return max(map(lambda x: len(x), xs))
        else:
            return len(xs)
    return max([_size(pfilter['categories']), _size(pfilter['contexts']), _size(pfilter['types'])])


def filter_combined(practice_filter_content):
    pfilter = json.loads(practice_filter_content)
    cats = [c[0].isdigit() for c in pfilter['categories']]
    return len(cats) > 0 and any(cats) and not all(cats)


def chapter_part(practice_filter_content):
    pfilter = json.loads(practice_filter_content)
    cats = pfilter['categories']
    if len(cats) == 0:
        return '', ''
    if not isinstance(cats[0], list):
        chapters = [c for c in cats if c.isdigit()]
        parts = [c for c in cats if not c.isdigit()]
        return chapters[0] if len(chapters) > 0 else '', parts[0] if len(parts) > 0 else ''
    else:
        chapters = [c for cs in cats for c in cs if c.isdigit()]
        parts = [c for cs in cats for c in cs if not c.isdigit()]
        return chapters[0] if len(chapters) > 0 else '', parts[0] if len(parts) > 0 else ''


@spiderpig()
def chapter_part_survival(length):
    data = load_and_merge()
    data['practice_filter_size'] = data['practice_filter_content'].apply(filter_size)
    data = data[data['practice_filter_size'] <= 1]
    data['chapter_part'] = data['practice_filter_content'].apply(chapter_part)

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return binomial_confidence_mean(xs)
    result = []
    for (chapter, part), d in data.groupby('chapter_part'):
        user_answers = d.groupby('user').apply(len).reset_index()[0]
        for i in range(length):
            result.append({
                'chapter': chapter,
                'part': part,
                'chapter_part': '{}, {}'.format(chapter, part),
                'value': _progress_confidence(i, user_answers)[0],
                'i': i,
                'size': len(d),
            })
    return pandas.DataFrame(result)


def execute():
    data = chapter_part_survival(100)
    data = data[data['size'] > 10000]
    g = sns.FacetGrid(data, col="chapter_part", col_wrap=4, margin_titles=True, ylim=(0, 1))
    g.map(sns.pointplot, "i", "value", markers='')
    g.set(xticks=[1, 50, 100])
    output.savefig('filter')
