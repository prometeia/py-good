""" Misc utilities """

import six
import collections


__type_names = direct = {
    None:             _(u'None'),
    type(None):       _(u'None'),
    bool:       _(u'Boolean'),
    float:      _(u'Fractional number'),
    complex:    _(u'Complex number'),
    six.text_type:    _(u'String'),
    six.binary_type:  _(u'Binary String'),
    tuple:      _(u'Tuple'),
    list:       _(u'List'),
    set:        _(u'Set'),
    frozenset:  _(u'Frozen Set'),
    dict:       _(u'Dictionary'),
}


def register_type_name(t, name):
    """ Register a human-friendly name for the given type. This will be used in Invalid errors

    :param t: The type to register
    :type t: type
    :param name: Name for the type
    :type name: unicode
    """
    assert isinstance(t, type)
    assert isinstance(name, unicode)
    __type_names[t] = name


def get_literal_name(v):
    """ Get a human-friendly name for the given literal.

    :param v: Value
    :type v: *
    :rtype: unicode
    """
    return six.text_type(v)


def get_type_name(t):
    """ Get a human-friendly name for the given type.

    :type t: type|None
    :rtype: unicode
    """
    # Lookup in the mapping
    try:
        return __type_names[t]
    except:
        # Specific types
        if issubclass(t, six.integer_types):
            return _(u'Integer number')

        # Get name from the Type itself
        return six.text_type(t.__name__).capitalize()


def get_callable_name(c):
    """ Get a human-friendly name for the given callable.

    :param c: The callable to get the name for
    :type c: callable
    :rtype: unicode
    """
    if hasattr(c, 'name'):
        return six.text_type(c.name)
    elif hasattr(c, '__name__'):
        return six.text_type(c.__name__) + u'()'
    else:
        return six.text_type(c)


def get_primitive_name(schema):
    """ Get a human-friendly name for the given primitive.

    :param schema: Schema
    :type schema: *
    :rtype: unicode
    """
    try:
        return {
            const.COMPILED_TYPE.LITERAL: six.text_type,
            const.COMPILED_TYPE.TYPE: get_type_name,
            const.COMPILED_TYPE.CALLABLE: get_callable_name,
            const.COMPILED_TYPE.ITERABLE: lambda x: _(u'{type}[...]').format(type=get_type_name(list)),
            const.COMPILED_TYPE.MAPPING:  lambda x: _(u'{type}[...]').format(type=get_type_name(dict)),
        }[primitive_type(schema)](schema)
    except KeyError:
        return six.text_type(repr(schema))


class const:
    """ Misc constants """
    #: Types that are treated as literals
    literal_types = six.integer_types + (six.text_type, six.binary_type) + (bool, float, complex, object, type(None))

    #: Exception classes that are transformed into Invalid when thrown by a callable
    transformed_exceptions = (AssertionError, TypeError, ValueError,)


    class COMPILED_TYPE:
        """ Compiled schema types """

        LITERAL = 'literal'
        TYPE = 'type'
        SCHEMA = 'schema'
        CALLABLE = 'callable'

        ITERABLE = 'iterable'
        MAPPING = 'mapping'
        MARKER = 'marker'

    #: Prioritites for compiled types
    #: This is used for mappings to determine the sequence with which the keys are processed
    #: See _schema_priority()

    compiled_type_priorities = {
        COMPILED_TYPE.LITERAL:   100,
        COMPILED_TYPE.TYPE:      50,
        COMPILED_TYPE.SCHEMA:     0,
        COMPILED_TYPE.CALLABLE:   0,
        COMPILED_TYPE.ITERABLE:   0,
        COMPILED_TYPE.MAPPING:    0,
        COMPILED_TYPE.MARKER:   None,  # Markers have their own priorities
    }


def primitive_type(schema):
    """ Get schema type for the primitive argument.

    Note: it does treats markers & schemas as callables!

    :param s: Value of a primitive type
    :type s: *
    :return: const.COMPILED_TYPE.*
    :rtype: str|None
    """
    schema_type = type(schema)

    # Literal
    if schema_type in const.literal_types:
        return const.COMPILED_TYPE.LITERAL
    # Type
    elif issubclass(schema_type, six.class_types):
        return const.COMPILED_TYPE.TYPE
    # Mapping
    elif isinstance(schema, collections.Mapping):
        return const.COMPILED_TYPE.MAPPING
    # Iterable
    elif isinstance(schema, collections.Iterable):
        return const.COMPILED_TYPE.ITERABLE
    # Callable
    elif callable(schema):
        return const.COMPILED_TYPE.CALLABLE
    # Not detected
    else:
        return None

