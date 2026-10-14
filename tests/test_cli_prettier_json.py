"""cli.prettier_json (#832): the indented JSON a consumer's prettier
check (printWidth 80, its default) leaves unchanged. Every expected text
below was checked byte for byte with `prettier --check` 3.3.3."""
import unittest

from cli import prettier_json


class TestPrettierJson(unittest.TestCase):
    def check(self, value, text):
        self.assertEqual(prettier_json(value), text)

    def test_objects_are_indented_two_with_a_trailing_newline(self):
        self.check({"a": 1, "b": {"c": None, "d": True}},
                   '{\n  "a": 1,\n  "b": {\n    "c": null,\n'
                   '    "d": true\n  }\n}\n')

    def test_empty_arrays_and_objects_stay_on_their_key_line(self):
        self.check({"a": [], "b": {}, "c": [{}, []]},
                   '{\n  "a": [],\n  "b": {},\n  "c": [{}, []]\n}\n')

    def test_an_array_that_fits_is_kept_on_one_line(self):
        self.check({"errors": ["x", 2, None], "n": [[1], [2, 3]]},
                   '{\n  "errors": ["x", 2, null],\n'
                   '  "n": [[1], [2, 3]]\n}\n')

    def test_a_line_of_exactly_eighty_fits_and_eighty_one_breaks(self):
        # 2 indent + '"k": ' + the array + "," = 80, then 81.
        self.check({"k": ["a" * 68], "z": 0},
                   '{\n  "k": ["' + "a" * 68 + '"],\n  "z": 0\n}\n')
        self.check({"k": ["a" * 69], "z": 0},
                   '{\n  "k": [\n    "' + "a" * 69 + '"\n  ],\n'
                   '  "z": 0\n}\n')

    def test_the_last_key_has_no_comma_to_count(self):
        self.check({"k": ["a" * 69]},
                   '{\n  "k": ["' + "a" * 69 + '"]\n}\n')

    def test_an_array_holding_an_object_breaks_one_item_a_line(self):
        self.check({"d": [{"tool": "Bash"}, 1]},
                   '{\n  "d": [\n    {\n      "tool": "Bash"\n    },\n'
                   '    1\n  ]\n}\n')

    def test_an_array_of_arrays_each_longer_than_one_breaks(self):
        self.check({"h": [[1, 2], [3, 4]]},
                   '{\n  "h": [\n    [1, 2],\n    [3, 4]\n  ]\n}\n')

    def test_a_long_number_array_fills_its_lines(self):
        self.check({"ids": list(range(40))},
                   '{\n  "ids": [\n'
                   '    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,'
                   ' 15, 16, 17, 18, 19, 20,\n'
                   '    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,'
                   ' 34, 35, 36, 37, 38, 39\n  ]\n}\n')

    def test_exponents_lose_their_plus_and_leading_zeros(self):
        self.check({"a": 1e21, "b": 1e-07, "c": 1.5e16, "d": 1.0},
                   '{\n  "a": 1e21,\n  "b": 1e-7,\n  "c": 1.5e16,\n'
                   '  "d": 1.0\n}\n')


if __name__ == "__main__":
    unittest.main()
