from .raw import load_answers


def execute(upper_bound=30):
    answers = load_answers()

    def _apply(data):
        return data['response_time'].apply(lambda x: min(x / 1000.0, upper_bound)).mean()

    print(answers.groupby('experiment_setup_name').apply(_apply))
