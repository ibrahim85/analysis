def context(context_name, term_type):
    if context_name is None or context_name == '':
        result = term_type
    elif term_type is None or term_type == '':
        result = context_name
    else:
        result ='{}, {}'.format(context_name, term_type)
    return result
