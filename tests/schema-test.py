from __future__ import print_function
import six
import unittest

from good import Schema, Invalid, MultipleInvalid, Required, Optional, Extra, Remove, Reject, Allow
from good.schema.util import get_type_name


class s:
    """ Shortcuts """
    # Type names
    t_none = get_type_name(None)
    t_bool = get_type_name(bool)
    t_int = get_type_name(int)
    t_float = get_type_name(float)
    t_str = get_type_name(six.binary_type)  # Binary string
    t_unicode = get_type_name(six.text_type)  # Unicode string
    t_list = get_type_name(list)
    t_dict = get_type_name(dict)

    es_type = u'Wrong type'
    es_value_type = u'Wrong value type'
    es_value = u'Invalid value'

    es_required = u'Required key not provided'
    es_extra = u'Extra keys not allowed'


class SchemaTest(unittest.TestCase):
    """ Test Schema """

    longMessage = True

    def assertInvalidError(self, actual, expected):
        """ Assert that the two Invalid exceptions are the same

        :param actual: Actual exception
        :type actual: Invalid
        :param expected: Expected exception
        :type expected: Invalid
        """
        repr(actual), six.text_type(actual)  # repr() works fine
        self.assertEqual(type(expected), type(actual))  # type matches

        if isinstance(actual, MultipleInvalid):
            return self.assertMultipleInvalidError(actual, expected)

        self.assertEqual(expected.path, actual.path)
        self.assertEqual(expected.validator, actual.validator)
        self.assertEqual(expected.message, actual.message)
        self.assertEqual(expected.provided, actual.provided)
        self.assertEqual(expected.expected, actual.expected)
        self.assertEqual(expected.info, actual.info)

    def assertMultipleInvalidError(self, actual, expected):
        """ Assert that the two MultipleInvalid exceptions are the same

        :param actual: Actual exception
        :type actual: MultipleInvalid
        :param expected: Expected exception
        :type expected: MultipleInvalid
        """
        # Match lists
        expected_errors = expected.errors[:]
        extra_errors = []
        raised_expectedly = []

        for actual_e in actual.errors:
            # Find the matching error
            for i, expected_e in enumerate(expected_errors):
                try:
                    # Matches?
                    self.assertInvalidError(actual_e, expected_e)
                except self.failureException:
                    pass
                else:
                    # Matches!
                    e = expected_errors.pop(i)
                    raised_expectedly.append(e)
                    break
            else:
                expected_e = None

            # No match
            if not expected_e:
                extra_errors.append(actual_e)

        # All ok?
        if not expected_errors and not extra_errors:
            return

        # Throw errors
        self.fail(
            u'MultipleError failed:\n' +
            u'\nNot raised:\n'
            u' * ' + '\n * '.join(map(repr, expected_errors)) +
            u'\nGot instead:\n' +
            u' * ' + '\n * '.join(map(repr, extra_errors)) +
            u'\nRaised expectedly:\n' +
            u' * ' + '\n * '.join(map(repr, raised_expectedly))
        )

    def assertValid(self, schema, value, validated_value=None):
        """ Try the given Schema against a value and expect that it's valid

        :type schema: Schema
        :param value: The value to validate
        :type validated_value: The expected validated value
        """
        self.assertEqual(
            schema(value),
            value if validated_value is None else validated_value,
            'Sanitized value is wrong'
        )

    def assertInvalid(self, schema, value, e):
        """ Try the given Schema against a value and expect that it's Invalid

        :type schema: Schema
        :param value: The value to validate
        :param e: Expected exception
        :type e: Invalid|MultipleInvalid
        """
        repr(schema), six.text_type(schema)  # no errors

        try:
            sanitized = schema(value)
            self.fail(u'False positive: {!r}\nExpected: {!r}'.format(sanitized, e))
        except Invalid as exc:
            self.assertInvalidError(exc, e)



    def test_literal(self):
        """ Test Schema(<literal>) """
        # None
        schema = Schema(None)
        self.assertValid(schema, None)
        self.assertInvalid(schema, True,  Invalid(s.es_value_type,  s.t_none,           s.t_bool,               [], None))

        # Bool
        schema = Schema(True)
        self.assertValid(schema, True)
        self.assertInvalid(schema, 1,     Invalid(s.es_value_type,  s.t_bool,            s.t_int,               [], True))
        self.assertInvalid(schema, False, Invalid(s.es_value,       u'True',             u"False",              [], True))

        # Integer
        schema = Schema(1)
        self.assertValid(schema, 1)
        self.assertInvalid(schema, True,  Invalid(s.es_value_type,  s.t_int,             s.t_bool,              [], 1))
        self.assertInvalid(schema, 1.0,   Invalid(s.es_value_type,  s.t_int,             s.t_float,             [], 1))
        self.assertInvalid(schema, 2,     Invalid(s.es_value,       u'1',                u'2',                  [], 1))

        # Float
        schema = Schema(1.0)
        self.assertValid(schema, 1.0)
        self.assertInvalid(schema,  1,    Invalid(s.es_value_type,  s.t_float,           s.t_int,               [], 1.0))
        self.assertInvalid(schema, 2.0,   Invalid(s.es_value,       u'1.0',              u'2.0',                [], 1.0))

        # String
        schema = Schema(b'1')
        self.assertValid(schema,   b'1')
        self.assertInvalid(schema,   1,   Invalid(s.es_value_type,  s.t_str,             s.t_int,               [], b'1'))
        self.assertInvalid(schema, u'1',  Invalid(s.es_value_type,  s.t_str,             s.t_unicode,           [], b'1'))
        self.assertInvalid(schema, b'2',  Invalid(s.es_value,       six.text_type(b'1'), six.text_type(b'2'),   [], b'1'))

        # Unicode
        schema = Schema(u'1')
        self.assertValid(schema, u'1')
        self.assertInvalid(schema,   1,   Invalid(s.es_value_type,  s.t_unicode,         s.t_int,               [], u'1'))
        self.assertInvalid(schema, b'1',  Invalid(s.es_value_type,  s.t_unicode,         s.t_str,               [], u'1'))
        self.assertInvalid(schema, u'2',  Invalid(s.es_value,       u'1',                u'2',                  [], u'1'))

    def test_type(self):
        """ Test Schema(<type>) """
        # NoneType
        schema = Schema(type(None))
        self.assertValid(schema, None)
        self.assertInvalid(schema, 1,    Invalid(s.es_type, s.t_none,    s.t_int,     [], type(None)))

        # Bool
        schema = Schema(bool)
        self.assertValid(schema, True)
        self.assertInvalid(schema, 1,    Invalid(s.es_type, s.t_bool,    s.t_int,     [], bool))
        self.assertInvalid(schema, None, Invalid(s.es_type, s.t_bool,    s.t_none,    [], bool))

        # Integer
        schema = Schema(int)
        self.assertValid(schema, 1)
        self.assertInvalid(schema, True, Invalid(s.es_type, s.t_int,     s.t_bool,    [], int))
        self.assertInvalid(schema, None, Invalid(s.es_type, s.t_int,     s.t_none,    [], int))

        # Float
        schema = Schema(float)
        self.assertValid(schema, 1.0)
        self.assertInvalid(schema, 1,    Invalid(s.es_type, s.t_float,   s.t_int,     [], float))

        # String
        schema = Schema(six.binary_type)
        self.assertValid(schema, b'a')
        self.assertInvalid(schema, u'a', Invalid(s.es_type, s.t_str,     s.t_unicode, [], six.binary_type))
        self.assertInvalid(schema, 1,    Invalid(s.es_type, s.t_str,     s.t_int,     [], six.binary_type))

        # Unicode
        schema = Schema(six.text_type)
        self.assertValid(schema, u'a')
        self.assertInvalid(schema, b'a', Invalid(s.es_type, s.t_unicode, s.t_str,     [], six.text_type))
        self.assertInvalid(schema, 1,    Invalid(s.es_type, s.t_unicode, s.t_int,     [], six.text_type))

    def test_iterable(self):
        """ Test Schema(<iterable>) """
        list_schema = [1, 2, six.text_type]

        # Test common cases
        schemas = (
            (tuple,     Schema(tuple(list_schema))),
            (list,      Schema(list(list_schema))),
            (set,       Schema(set(list_schema))),
            (frozenset, Schema(frozenset(list_schema))),
        )
        valid_inputs = (
            (),
            (1,),
            (u'a',),
            (1, 1, 2, u'a', u'b', u'c')
        )

        for type, schema in schemas:
            # Test valid inputs
            for v in valid_inputs:
                # Typecast to the correct value
                value = type(v)
                # Should be valid
                self.assertValid(schema, value)

        # Test specific cases
        schema = Schema(list_schema)
        self.assertInvalid(schema, (),      Invalid(s.es_value_type, u'List',             u'Tuple', [ ], list_schema))
        self.assertInvalid(schema, [True,], Invalid(s.es_value,      u'List[1|2|String]', u'True',  [0], list_schema))
        self.assertInvalid(schema, [1, 4],  Invalid(s.es_value,      u'List[1|2|String]', u'4',     [1], list_schema))
        self.assertInvalid(schema, [1, 4],  Invalid(s.es_value,      u'List[1|2|String]', u'4',     [1], list_schema))

    def test_callable(self):
        """ Test Schema(<callable>) """
        def intify(v):
            return int(v)

        def intify_ex(v):
            try:
                return int(v)
            except (TypeError, ValueError):
                raise Invalid(u'Must be a number', u'Number')

        # Simple callable
        schema = Schema(intify)

        self.assertValid(schema, 1)
        self.assertValid(schema, True, 1)
        self.assertValid(schema, b'1', 1)

        self.assertInvalid(schema, None, Invalid(u'TypeError: int() argument must be a string or a number, not \'NoneType\'',   u'intify()', s.t_none,  [], intify))
        self.assertInvalid(schema, u'a', Invalid(u'ValueError: invalid literal for int() with base 10: \'a\'',                  u'intify()', u'a',      [], intify))

        # Simple callable that throws Invalid
        schema = Schema(intify_ex)

        self.assertValid(schema, u'1', 1)
        self.assertInvalid(schema, u'a', Invalid(u'Must be a number', u'Number', u'a', [], intify_ex))

        # Nested callable
        str_or_int = [
            intify,
            six.text_type
        ]
        schema = Schema(str_or_int)

        self.assertValid(schema, [u'a'])
        self.assertValid(schema, [1])
        self.assertValid(schema, [u'1', 1], [1, 1])
        self.assertValid(schema, [b'1'], [1])

        self.assertInvalid(schema, [b'abc'], Invalid(u'Invalid value', u'List[intify()|String]', six.text_type(b'abc'), [0], str_or_int))

    @unittest.skip
    def test_schema_schema(self):
        """ Test Schema(Schema) """

    def test_mapping_literal(self):
        """ Test Schema(<mapping>), literal keys """
        structure = {
            'name': six.text_type,
            'age': int,
            'sex': u'f',  # girls only :)
        }
        schema = Schema(structure)

        # Okay
        self.assertValid(schema, {'name': u'A', 'age': 18, 'sex': u'f'})

        # Wrong type
        self.assertInvalid(schema, [],
                           Invalid(s.es_value_type, s.t_dict, s.t_list, [], structure))

        # Wrong 'sex'
        self.assertInvalid(schema, {'name': u'A', 'age': 18, 'sex': None},
                           Invalid(s.es_value_type, s.t_unicode,            s.t_none,               ['sex'],    u'f'))
        self.assertInvalid(schema, {'name': u'A', 'age': 18, 'sex': u'm'},
                           Invalid(s.es_value,      u'f',                   u'm',                   ['sex'],    u'f'))
        # Wrong 'name' and 'age'
        self.assertInvalid(schema, {'name': None, 'age': None, 'sex': u'f'}, MultipleInvalid([
                           Invalid(s.es_type,       s.t_unicode,            s.t_none,               ['name'],   six.text_type),
                           Invalid(s.es_type,       s.t_int,                s.t_none,               ['age'],    int),
        ]))

        # Missing key 'sex'
        self.assertInvalid(schema, {'name': u'A', 'age': 18},
                           Invalid(s.es_required,   six.text_type('sex'),   None,                   ['sex'],    Required('sex')))
        # Extra key 'lol'
        self.assertInvalid(schema, {'name': u'A', 'age': 18, 'sex': u'f', 'lol': 1},
                           Invalid(s.es_extra,      None,                   six.text_type('lol'),   ['lol'],    Extra))
        # Missing keys 'age', 'sex', extra keys 'lol', 'hah'
        self.assertInvalid(schema, {'name': u'A', 'lol': 1, 'hah': 2}, MultipleInvalid([
                           Invalid(s.es_required,   six.text_type('age'),   None,                   ['age'],    Required),
                           Invalid(s.es_required,   six.text_type('sex'),   None,                   ['sex'],    Required),
                           Invalid(s.es_extra,      None,                   six.text_type('lol'),   ['lol'],    Extra),
                           Invalid(s.es_extra,      None,                   six.text_type('hah'),   ['hah'],    Extra),
        ]))

    def test_mapping_type(self):
        """ Test Schema(<mapping>), type keys """
        schema = Schema({
            'name': 1,
            int: bool,
        })

        # Okay
        self.assertValid(schema, {'name': 1, 1: True, 2: True})

        # Wrong value type
        self.assertInvalid(schema, {'name': 1},
                           Invalid(s.es_required,   s.t_int,  None,        [],  Required(int)))
        self.assertInvalid(schema, {'name': 1, 1: True, 2: u'WROOONG'},
                           Invalid(s.es_type,       s.t_bool, s.t_unicode, [2], bool))

        # Wrong key type (meaning, `int` not provided, and extra key `'2'`)
        self.assertInvalid(schema, {'name': 1, u'1': True}, MultipleInvalid([
                           Invalid(s.es_extra,      None,     u'1',        [u'1'], Extra),
                           Invalid(s.es_required,   s.t_int,  None,        [],  Required(int)),
        ]))

    def test_mapping_callable(self):
        """ Test Schema(<mapping>), callable keys """
        def multikey(*keys):
            def multikey_validate(v):
                assert v in keys
                return v
            return multikey_validate

        def intify(v):
            try:
                return int(v)
            except ValueError as e:
                raise Invalid(u'Int failed')

        abc = multikey('a', 'b', 'c')
        schema = Schema({
            # Values for ('a', 'b', 'c') are int()ified
            abc: intify,
            # Other keys are int()ified and should be boolean
            intify: bool
        })

        # Okay
        self.assertValid(schema, {'a': 1, 'b': '2', 1: True},             {'a': 1, 'b': 2, 1: True})
        self.assertValid(schema, {'a': 1, 'b': '2', 1: True, '2': False}, {'a': 1, 'b': 2, 1: True, 2: False})

        # Wrong value for `multikey()`
        self.assertInvalid(schema, {'a': u'!', '1': True},
                           Invalid(u'Int failed', u'intify()', u'!', ['a'], intify))
        # Wrong value for `bool`
        self.assertInvalid(schema, {'a': 1, '1': None},
                           Invalid(s.es_type, s.t_bool, s.t_none, ['1'], bool))
        # `intify()` did not match
        self.assertInvalid(schema, {'a': 1},
                           Invalid(u'Required key not provided', u'intify()', None, [], Required(intify)))
        # `multikey()` did not match
        self.assertInvalid(schema, {1: True},
                           Invalid(u'Required key not provided', u'multikey_validate()', None, [], Required(abc)))
        # Both `intify()` and `multikey()` did not match
        self.assertInvalid(schema, {}, MultipleInvalid([
            Invalid(u'Required key not provided', u'intify()', None, [], Required(intify)),
            Invalid(u'Required key not provided', u'multikey_validate()', None, [], Required(abc)),
        ]))

    def test_mapping_markers(self):
        """ Test Schema(<mapping>), with Markers """
        # Required, literal
        schema = Schema({
            Required(u'a'): 1,
            u'b': 2,
            Required(int): bool,
        })

        # Optional
        schema = Schema({
            Optional(u'a'): 1,
            u'b': 2,
            Optional(int): bool,
        })

        # Remove
        schema = Schema({
            Remove(u'a'): 1,
            Remove(int): bool,
            u'b': 2
        })

        # Extra
        schema = Schema({
            u'a': 1,
            Extra: int
        })

        # Extra: Reject
        schema = Schema({
            u'a': 1,
            Extra: Reject
        })

        # Extra: Remove
        schema = Schema({
            u'a': 1,
        }, extra_keys=Remove)

        # Extra: Allow
        schema = Schema({
            u'a': 1,
        }, extra_keys=Allow)

        # Reject
        schema = Schema({
            u'a': 1,
            str: Reject,
        })