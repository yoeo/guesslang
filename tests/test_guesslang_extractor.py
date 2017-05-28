from guesslang import extractor


def test_split():
    text = """
        int * last(int *tab, int size)
        {
        \treturn tab + (size - 1);
        }
    """
    tokens = [
        '\n', 'int', '*', 'last', '(', 'int', '*', 'tab', ',', 'int', 'size',
        ')', '\n', '{', '\n', 'return', 'tab', '+', '(', 'size', '-', '1', ')',
        ';', '\n', '}', '\n'
    ]

    assert extractor.split(text) == tokens


def non_empty_indices(vector):
    return set(index for index, value in enumerate(vector) if value)


def test_extract():
    text = """
        int * last(int *tab, int size)
        {
        \treturn tab + (size - 1);
        }
    """
    tokens = ['int', '*', 'last', '(', 'tab', ',', 'size', ')', '\n', '{']

    values = extractor.extract(text)
    assert values

    text_indices = non_empty_indices(values)
    for token in tokens:
        token_values = extractor.extract(token)
        token_indices = non_empty_indices(token_values)

        assert len(token_indices) == 1
        assert text_indices.issuperset(token_indices)
