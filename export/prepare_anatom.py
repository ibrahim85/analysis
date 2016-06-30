from geolite2 import geolite2
import numpy
import pandas


geolite_reader = geolite2.reader()


def get_country(ip):
    if not isinstance(ip, str):
        return numpy.nan
    lookup = geolite_reader.get(ip)
    return numpy.nan if lookup is None or 'country' not in lookup else lookup['country']['iso_code']


answers = pandas.read_csv('./answers.csv', delimiter=';')

answers['touch_device'] = answers['touch_device'].apply(lambda x: x == 't')
answers['correct'] = answers['correct'].apply(lambda x: x == 't')

countries = {ip: get_country(ip) for ip in answers['ip_address'].unique()}
ips_dict = {ip: i + 1 for i, ip in enumerate(answers['ip_address'].unique()) if isinstance(ip, str)}
answers['country'] = answers['ip_address'].apply(lambda ip: countries.get(ip))
answers['ip'] = answers['ip_address'].apply(lambda ip: ips_dict.get(ip))
del answers['ip_address']

del answers['experiment_id']

answers.to_csv('./anatom.csv', index=False)

pandas.read_csv('./contexts.csv', delimiter=';').to_csv('anatom.contexts.csv', index=False)
