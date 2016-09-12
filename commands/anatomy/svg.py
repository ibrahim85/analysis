from colour import Color
from copy import deepcopy
from spiderpig import msg
import os
import matplotlib
import pandas


class Context:

    def __init__(self, context_data, flashcards):
        self._context_data = deepcopy(context_data)
        self._flashcards = flashcards[flashcards['context_id'] == self._context_data['id']]
        self._paths = self._context_data['content']['paths']
        for path in self._paths:
            path['color'] = to_grayscale(path['color'])
            if 'stroke' in path:
                path['stroke'] = to_grayscale(path['color'])

    def set_color(self, term, color, ensure=True):
        success = False
        for path in self._paths:
            if path.get('term') == term:
                path['color'] = color
                success = True
        if not success and ensure:
            raise Exception('Can not set color for term {}'.format(term))

    def set_difficulty(self):
        colors = matplotlib.cm.get_cmap('RdYlGn')
        for term, difficulty in self._flashcards[['term_id', 'difficulty_prob']].values:
            color = Color(rgb=colors(difficulty)[:3]).get_hex()
            self.set_color(term, color, ensure=False)

    def set_number_colors(self, items_with_values, palette='Blues'):
        to_set = items_with_values[items_with_values['item'].isin(self._flashcards['item'].unique())]
        print('setting color for {} flashcards'.format(len(to_set)))
        max_value = to_set['value'].max()
        flashcards = pandas.merge(self._flashcards, to_set, on='item', how='inner')
        colors = matplotlib.cm.get_cmap(palette)
        for term, value in flashcards[['term_id', 'value']].values:
            color = Color(rgb=colors(value / max_value)[:3]).get_hex()
            self.set_color(term, color, ensure=False)

    def set_learning_rate(self, learning_rate):
        self.set_number_colors(learning_rate.rename(columns={'learning_rate': 'value'}), 'RdYlGn')

    def set_answers(self, answers):
        answers = answers[answers['flashcard_id_asked'].isin(self._flashcards['flashcard_id'])]
        colors = matplotlib.cm.get_cmap('Blues')
        max_answers = answers.groupby(['flashcard_id_asked']).apply(len).max()
        for flashcard, num in answers.groupby(['flashcard_id_asked']).apply(len).reset_index().values:
            term = self._flashcards['term_id'][self._flashcards['flashcard_id'] == flashcard].values[0]
            color = Color(rgb=colors(num / max_answers)[:3]).get_hex()
            self.set_color(term, color, ensure=False)

    def set_search_results(self, search_results):
        search_results = search_results[search_results['identifier'].isin(self._flashcards['term_id'])]
        colors = matplotlib.cm.get_cmap('Blues')
        max_results = search_results['search_results'].max()
        for term, num in search_results[['identifier', 'search_results']].values:
            color = Color(rgb=colors(num / max_results)[:3]).get_hex()
            self.set_color(term, color, ensure=False)

    def set_misanswers(self, term, misanswers):
        flashcard = self._flashcards['flashcard_id'][self._flashcards['term_id'] == term].values[0]
        misanswers = misanswers[misanswers['flashcard_id_asked'] == flashcard]
        misanswers = misanswers[misanswers['flashcard_id_answered'].isin(self._flashcards['flashcard_id'].unique())]
        max_mis = misanswers['misanswers'].max()
        colors = matplotlib.cm.get_cmap('Blues')
        for asked, answered, num in misanswers[['flashcard_id_asked', 'flashcard_id_answered', 'misanswers']].values:
            color = Color(rgb=colors(num / max_mis)[:3]).get_hex()
            term_answered = self._flashcards['term_id'][self._flashcards['flashcard_id'] == answered].values[0]
            self.set_color(term_answered, color, ensure=False)
        self.set_color(term, '#f42f1e')

    def to_file(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self))
        os.system("inkscape --verb=FitCanvasToDrawing --verb=FileSave --verb=FileClose {}".format(filename))
        msg.success(filename)

    def __str__(self):
        output = []
        for path in self._paths:
            output.append(
                '<path {}></path>'.format(
                    ' '.join(['{}="{}"'.format('fill' if key == 'color' else key, value) for key, value in path.items()])
                )
            )
        return """<svg width="100%" height="100%" version="1.1" xmlns="http://www.w3.org/2000/svg">{}</svg>""".format(''.join(output))


def is_gray(name):
    if name == 'none':
        return True
    try:
        rgb = Color(name).get_rgb()
        return max(abs(rgb[0] - rgb[1]), abs(rgb[0] - rgb[2])) < 0.05
    except:
        return True


def to_grayscale(name):
    if is_gray(name):
        return name
    rgb = Color(name).get_rgb()
    g = (3.7 / 3) * (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
    g = min(0.95, (g - 0.5) * 0.5 + 0.5)
    return Color(rgb=[(g * 18 + c) / 19 for c in rgb]).get_hex_l()
