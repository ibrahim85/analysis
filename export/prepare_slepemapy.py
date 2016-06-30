from geolite2 import geolite2
import numpy
import pandas


experiments = {
    6: ('random-parts', 'R-A'),
    7: ('random-parts', 'R-R'),
    8: ('random-parts', 'A-A'),
    9: ('random-parts', 'A-R'),
    14: ('target-difficulty', '50'),
    15: ('target-difficulty', '35'),
    16: ('target-difficulty', '20'),
    17: ('target-difficulty', '5'),
    24: ('distractors', 'adjusted-random'),
    25: ('distractors', 'competitive-adjusted'),
    26: ('distractors', 'adjusted-adjusted'),
    27: ('distractors', 'adjusted-constant'),
    28: ('distractors', 'competitive-random'),
    29: ('distractors', 'competitive-constant'),
    30: ('max-options', '4'),
    31: ('max-options', '6'),
    32: ('max-options', '3'),
    33: ('max-options', '2'),
    34: ('max-options', '8'),
}


geolite_reader = geolite2.reader()


def get_country(ip):
    if not isinstance(ip, str):
        return numpy.nan
    lookup = geolite_reader.get(ip)
    return numpy.nan if lookup is None or 'country' not in lookup else lookup['country']['iso_code']


answers = pandas.read_csv('./answers.csv', delimiter=';')

answers['touch_device'] = answers['touch_device'].apply(lambda x: x == 't')
answers['correct'] = answers['correct'].apply(lambda x: x == 't')

contexts_dict = {c: i + 1 for i, c in enumerate(answers['context'].unique())}
answers['context'] = answers['context'].apply(lambda c: contexts_dict[c])

countries = {ip: get_country(ip) for ip in answers['ip_address'].unique()}
ips_dict = {ip: i + 1 for i, ip in enumerate(answers['ip_address'].unique()) if isinstance(ip, str)}
answers['country'] = answers['ip_address'].apply(lambda ip: countries.get(ip))
answers['ip'] = answers['ip_address'].apply(lambda ip: ips_dict.get(ip))
del answers['ip_address']

answers['experiment'] = answers['experiment_id'].apply(lambda i: numpy.nan if numpy.isnan(i) or i not in experiments else experiments[i][0])
answers['condition'] = answers['experiment_id'].apply(lambda i: numpy.nan if numpy.isnan(i) or i not in experiments else experiments[i][1])
del answers['experiment_id']

for experiment, data in answers.groupby('experiment'):
    if not isinstance(experiment, str):
        continue
    print(experiment, len(data))
    data.to_csv('./slepemapy-{}.csv'.format(experiment.replace('-', '_')), index=False)

answers.to_csv('./slepemapy.csv', index=False)


pandas.DataFrame([{'id': i, 'name': c} for c, i in contexts_dict.items()]).to_csv('./slepemapy.contexts.csv', index=False)
