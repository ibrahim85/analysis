from .raw import load_school_usage, load_answers
from pylab import rcParams
import matplotlib.pyplot as plt
import output
import pandas
import seaborn as sns


def execute(school_threshold=10, time_unit='hour'):
    rcParams['figure.figsize'] = 7.5, 4
    answers = load_answers()
    # answers = pandas.merge(load_answers(), load_school_usage(school_threshold=school_threshold).reset_index().rename(columns={'ip_address': 'school'}), on='user_id', how='inner')
    answers_per_time = answers.set_index('time').groupby(lambda x: getattr(x, time_unit)).apply(len).reset_index().rename(columns={'index': 'Time', 0: 'Answers'})
    print(answers)
    in_school = answers[answers['school']].copy().set_index('time').groupby(lambda x: getattr(x, time_unit)).apply(len).reset_index().rename(columns={'index': 'Time', 0: 'Answers'})
    total_answers = answers_per_time['Answers'].sum()
    answers_per_time['Answers'] = answers_per_time['Answers'].apply(lambda a: 100 * a / total_answers)
    in_school['Answers'] = in_school['Answers'].apply(lambda a: 100 * a / total_answers)
    sns.barplot(x='Time', y='Answers', data=in_school, label='Detected schools', color=output.palette()[0])
    sns.barplot(x='Time', y='Answers', data=answers_per_time, label='Rest', color=output.palette()[1])
    sns.barplot(x='Time', y='Answers', data=in_school, color=output.palette()[0])
    plt.ylabel('Answers (%)')
    plt.xlabel('Hour')
    plt.legend(loc='upper left')
    print(in_school['Answers'].sum())
    output.savefig('answers_per_{}'.format(time_unit))
