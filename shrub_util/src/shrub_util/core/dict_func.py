from collections import OrderedDict


def flatten_dictionary(dict_data) -> OrderedDict:
    flattened_dict = OrderedDict()

    def add_keys(dict_data):
        for key, value in dict_data.items():
            if isinstance(value, dict):
                add_keys(value)
            else:
                flattened_dict[key] = value

    add_keys(dict_data)
    return flattened_dict
