import six
from .errors import Invalid, MultipleInvalid


class Marker(object):
    #: Marker priority
    priority = 0

    def __init__(self, key):
        #: The original key
        self.key = key
        #: Human-readable marker representation
        self.name = None
        #: CompiledSchema for the key
        self.key_schema = None
        #: CompiledSchema for value (if the Marker was used as a key in a mapping)
        self.value_schema = None

    def on_compiled(self, name=None, key_schema=None, value_schema=None):
        """ When CompiledSchema compiles this marker, it sets informational values onto it.

        Note that arguments may be provided in two incomplete sets,
        e.g. (name, key_schema, None) and then (None, None, value_schema).
        Thus, all assignments must be handled individually.

        It is possible that a marker may have no `value_schema` at all:
        e.g. in the case of { Extra: Reject } -- `Reject` will have no value schema,
        but `Extra` will have compiled `Reject` as the value.

        :param key_schema: Compiled key schema
        :type key_schema: CompiledSchema|None
        :param value_schema: Compiled value schema
        :type value_schema: CompiledSchema|None
        :param name: Human-friendly marker name
        :type name: unicode|None
        :rtype: Marker
        """
        if self.name is None:
            self.name = name
        if self.key_schema is None:
            self.key_schema = key_schema
        if self.value_schema is None:
            self.value_schema = value_schema

        return self

    def __repr__(self):
        return '{cls}({0})'.format(
            self.name,
            cls=type(self).__name__)

    #region Marker is a Proxy

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == (other.key if isinstance(other, Marker) else other)

    def __str__(self):
        return six.binary_type(self.key)

    def __unicode__(self):
        return six.text_type(self.key)

    if six.PY3:
        __bytes__, __str__ = __str__, __unicode__

    #endregion

    def __call__(self, v):
        """ Validate a key using this Marker's schema """
        return self.key_schema(v)

    def execute(self, input, matches):
        """ Execute the marker against the input and the matching values

        :param input: The whole input object
        :type input: dict
        :param matches: List of (input-key, sanitized-input-key, input-value) triples that matched the given marker
        :type matches: list[tuple]
        :returns: The list of matches, potentially modified
        :rtype: list[tuple]
        :raises: Invalid|MultipleInvalid
        """
        return matches  # No-op by default

#region Dictionary keys behavior

class Required(Marker):

    def execute(self, input, matches):
        # If a Required() key is present -- it expects to ALWAYS have one or more matches
        if not matches:
            raise Invalid(_(u'Required key not provided'), self.name, None, [self.key])
        return matches


class Optional(Marker):
    pass


class Remove(Marker):
    priority = 1000  # We always want to remove keys prior to any other actions

    def execute(self, input, matches):
        # Remove all matching keys from the input
        for k, sanitized_k, v in matches:
            del input[k]
        return matches

class Reject(Marker):

    def execute(self, input, matches):
        # Complain on all values it gets
        if matches:
            errors = []
            for k, sanitized_k, v in matches:
                errors.append(Invalid(_(u'Value rejected'), None, six.text_type(v), [k]))
            raise MultipleInvalid.if_multiple(errors)
        return matches

class Allow(Marker):
    pass

class Extra(Marker):
    """ Catch-all marker for extra mapping keys """
    priority = -1000  # Extra should match last

    def on_compiled(self, name=None, key_schema=None, value_schema=None):
        return super(Extra, self).on_compiled(name, key_schema, value_schema)

    def execute(self, input, matches):
        # Delegate the decision to the value.

        # If the value is a marker -- call execute() on it
        # This is for Reject() so it has a chance to raise exceptions
        if isinstance(self.value_schema.compiled, Marker):
            return self.value_schema.compiled.execute(input, matches)

        # Otherwise, it's a schema, which must be called on every value.
        # However, CompiledSchema does this anyway as the next step, so do nothing
        return matches

#endregion

__all__ = ('Required', 'Optional', 'Remove', 'Reject', 'Allow', 'Extra')
