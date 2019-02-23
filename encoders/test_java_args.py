import pytest
from java_args import describe, encode, \
    JavaOptsEncoderException, \
    UnsupportedSettingException, \
    NoValueToEncodeException, \
    NoValueToDecodeException, \
    InvalidValueException, \
    InvalidTypeException, \
    NoLowerBoundException, \
    NoUpperBoundException, \
    UpperBoundViolationException, \
    LowerBoundViolationException, \
    BoundariesCollisionException, \
    NoStepException, \
    InvalidStepValueException, \
    ValueStepRemainderException, \
    MultipleSettingsException

"""
Describe helper
"""


def test_describe():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(config, ['-XX:MaxHeapSize=3072m',
                                   '-XX:GCTimeRatio=15'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 3, 'type': 'range', 'unit': 'gigabytes'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_no_current_value_with_default():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 15}}}
    descriptor = describe(config, [])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'default': 3, 'value': 3, 'type': 'range', 'unit': 'gigabytes'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'default': 15, 'value': 15, 'type': 'range', 'unit': ''}}


def test_describe_no_current_value_without_default():
    with pytest.raises(NoValueToDecodeException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}}, [])

    with pytest.raises(NoValueToDecodeException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}, [])


def test_describe_unsupported_settings_provided():
    config = {'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                           'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}}
    descriptor = describe(config, ['java', '-server',

                                   '-XX:MaxHeapSize=5120m',
                                   '-XX:GCTimeRatio=50',

                                   '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar'])
    assert descriptor == {
        'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1, 'value': 5, 'type': 'range', 'unit': 'gigabytes'},
        'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1, 'value': 50, 'type': 'range', 'unit': ''}}


def test_describe_no_config_provided():
    describe(None, ['-XX:MaxHeapSize=1024m'])


def test_describe_wrong_value_format():
    with pytest.raises(InvalidValueException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
                 ['-XX:MaxHeapSize=5.2g'])

    with pytest.raises(InvalidValueException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                 ['-XX:GCTimeRatio=None'])


def test_describe_multiple_duplicate_settings_provided():
    with pytest.raises(MultipleSettingsException):
        describe({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
                 ['-XX:MaxHeapSize=5120m', '-XX:MaxHeapSize=6144m'])

    with pytest.raises(MultipleSettingsException):
        describe({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                 ['-XX:GCTimeRatio=50', '-XX:GCTimeRatio=60'])


def test_describe_wrong_config_type_provided():
    with pytest.raises(JavaOptsEncoderException):
        describe('settings', ['-XX:MaxHeapSize=1024m'])


def test_describe_unsupported_setting_requested():
    with pytest.raises(UnsupportedSettingException):
        describe({'settings': {'UnsupportedSetting': {}}}, [])


"""
Encode helper
"""


def test_encode():
    encoded = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1},
                                   'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
                     {'MaxHeapSize': 4,
                      'GCTimeRatio': 59})
    assert sorted(encoded) == sorted(['-XX:MaxHeapSize=4096m',
                                      '-XX:GCTimeRatio=59'])


def test_encode_no_values_provided():
    with pytest.raises(NoValueToEncodeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {})

    with pytest.raises(NoValueToEncodeException):
        encode({'settings': {'GCTimeRatio': {'min': 9, 'max': 99, 'step': 1}}},
               {})


def test_encode_invalid_type_value_provided():
    with pytest.raises(InvalidTypeException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': '1'})


def test_encode_before_after_persist():
    encoded = encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}},
                      'before': ['java', '-server'],
                      'after': ['-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']},
                     {'MaxHeapSize': 4})
    assert encoded == ['java', '-server',
                       '-XX:MaxHeapSize=4096m',
                       '-javaagent:/tmp/newrelic/newrelic.jar', '-jar', '/app.jar']


def test_encode_value_conversion():
    assert encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': .125}}},
                  {'MaxHeapSize': 1.625}) == ['-XX:MaxHeapSize=1664m']


def test_encode_range_setting_value_validation():
    with pytest.raises(NoLowerBoundException):
        encode({'settings': {'MaxHeapSize': {'min': None, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 2})

    with pytest.raises(NoUpperBoundException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'step': 1}}},
               {'MaxHeapSize': 2})

    with pytest.raises(NoStepException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': None}}},
               {'MaxHeapSize': 2})

    with pytest.raises(InvalidStepValueException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 0}}},
               {'MaxHeapSize': 2})

    with pytest.raises(InvalidStepValueException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': -1}}},
               {'MaxHeapSize': 6})

    with pytest.raises(ValueStepRemainderException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 2.5})

    with pytest.raises(BoundariesCollisionException):
        encode({'settings': {'MaxHeapSize': {'min': 6, 'max': 1, 'step': 1}}},
               {'MaxHeapSize': 2})

    with pytest.raises(LowerBoundViolationException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 0})

    with pytest.raises(UpperBoundViolationException):
        encode({'settings': {'MaxHeapSize': {'min': 1, 'max': 6, 'step': 1}}},
               {'MaxHeapSize': 7})
