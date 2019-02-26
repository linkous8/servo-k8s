from abc import ABC

import yaml

# Base exception
JavaOptsEncoderException = type('JavaOptsEncoderException', (BaseException,), {})

# Developr-related exceptions
SettingEncoderException = type('SettingEncoderException', (JavaOptsEncoderException,), {})
NoValueEncoderSettingException = type('NoValueEncoderSettingException',
                                      (SettingEncoderException,), {})
UnsupportedSettingException = type('UnsupportedSettingException', (SettingEncoderException,), {})

# User-related exceptions
EncoderConfigException = type('EncoderConfigException', (JavaOptsEncoderException,), {})
EncoderRuntimeException = type('EncoderRuntimeException', (JavaOptsEncoderException,), {})
SettingConfigException = type('SettingConfigException', (JavaOptsEncoderException,), {})
SettingRuntimeException = type('SettingRuntimeException', (JavaOptsEncoderException,), {})


def q(v):
    return '"{}"'.format(v)


class Setting:
    name = None
    type = None
    allowed_options = {'default'}

    def __init__(self, config):
        if not config:
            config = {}
        self.config = config
        self.check_class_defaults()
        self.check_config()

    def check_class_defaults(self):
        if self.name is None:
            raise NotImplementedError(
                'Setting with its handler class name {} must have '
                'attribute `name` defined.'.format(self.__class__.__name__))
        if self.type is None:
            raise NotImplementedError(
                'Setting with its handler class name {} must have '
                'attribute `type` defined.'.format(self.__class__.__name__))

    def check_config(self):
        if not isinstance(self.config, dict):
            raise SettingConfigException('Setting {} must have its configuration to be a dictionary or undefined. '
                                         'It is currently {}.'.format(q(self.name), self.config.__class__.__name__))
        for option in self.config.keys():
            if option not in self.allowed_options:
                raise SettingConfigException('Cannot recognize option {} for setting {}. '
                                             'Supported setting: {}.'.format(q(option), q(self.name),
                                                                             ', '.join(self.allowed_options)))

    def describe(self):
        raise NotImplementedError()

    def encode_option(self, values):
        raise NotImplementedError()

    def decode_option(self, data):
        raise NotImplementedError()


class RangeSetting(Setting, ABC):
    can_relax = True
    type = 'range'
    unit = ''

    def __init__(self, config):
        self.allowed_options.update({'min', 'max', 'step'})
        super().__init__(config)
        self.min = config.get('min', getattr(self, 'min', None))
        self.max = config.get('max', getattr(self, 'max', None))
        self.step = config.get('step', getattr(self, 'step', None))
        self.default = config.get('default', getattr(self, 'default', None))

    def check_config(self):
        super().check_config()
        default_min = getattr(self, 'min', None)
        default_max = getattr(self, 'max', None)
        default_step = getattr(self, 'step', None)
        minv = self.config.get('min', default_min)
        maxv = self.config.get('max', default_max)
        step = self.config.get('step', default_step)
        if minv is None:
            raise SettingConfigException(
                'No min value configured for setting {} in java-opts encoder.'.format(q(self.name)))
        if maxv is None:
            raise SettingConfigException(
                'No max value configured for setting {} in java-opts encoder.'.format(q(self.name)))
        if step is None:
            raise SettingConfigException(
                'No step value configured for setting {} in java-opts encoder.'.format(q(self.name)))
        if not isinstance(minv, (int, float)):
            raise SettingConfigException('Min value must be a number in setting {} of java-opts encoder. '
                                         'Found {}.'.format(q(self.name), q(minv)))
        if not isinstance(maxv, (int, float)):
            raise SettingConfigException('Max value must be a number in setting {} of java-opts encoder. '
                                         'Found {}.'.format(q(self.name), q(maxv)))
        if not isinstance(step, (int, float)):
            raise SettingConfigException('Step value must be a number in setting {} of java-opts encoder. '
                                         'Found {}.'.format(q(self.name), q(step)))
        if minv > maxv:
            raise SettingConfigException('Lower boundary is higher than upper boundary in setting {} '
                                         'of java-opts encoder.'.format(q(self.name)))
        if minv != maxv:
            if step < 0:
                raise SettingConfigException('Step for setting {} must be a positive number.'
                                             ''.format(q(self.name)))
            if step == 0:
                raise SettingConfigException(
                    'Step for setting {} cannot be zero when min != max.'.format(q(self.name)))
        if step != 0 and (maxv - minv) % step > 0:
            raise SettingConfigException(
                'Step value for setting {} must allow to get from {} to {} in equal steps. Its current value is {}. '
                'The size of the last step would be {}.'.format(q(self.name), minv, maxv, step, (maxv - minv) % step))
        # Relaxation of boundaries
        if self.can_relax is False:
            if default_min is None:
                raise NotImplementedError('Default min value for setting {} must be configured '
                                          'to disallow its relaxation.'.format(q(self.name)))
            elif minv < default_min:
                raise SettingConfigException('Min value for setting {} cannot be lower than {}. '
                                             'It is {} now.'.format(q(self.name),
                                                                    default_min, minv))
            if default_max is None:
                raise NotImplementedError('Default max value for setting {} must be configured '
                                          'to disallow its relaxation.'.format(q(self.name)))
            elif maxv > default_max:
                raise SettingConfigException('Max value for setting {} cannot be lower than {}. '
                                             'It is {} now.'.format(q(self.name), default_max, maxv))
            if default_step is None:
                raise NotImplementedError('Default step value for setting {} must be configured '
                                          'to disallow its change.'.format(q(self.name)))
            elif step % default_step > 0:
                raise SettingConfigException('Step value for setting {} must be multiple of provided default {}. '
                                             'It is {} now.'.format(q(self.name), default_step, step))

    def describe(self):
        descr = {
            'type': self.type,
            'min': self.min,
            'max': self.max,
            'step': self.step,
            'unit': self.unit,
        }
        if self.default is not None:
            descr['default'] = self.default
        return self.name, descr

    def validate_value(self, value):
        if value is None:
            raise SettingRuntimeException('No value provided for setting {}'.format(self.name))
        if not isinstance(value, (float, int)):
            raise SettingRuntimeException('Value in setting {} must be either integer or float. '
                                          'Found {}.'.format(q(self.name), q(value)))
        if value < self.min:
            raise SettingRuntimeException('Value {} is violating lower bound '
                                          'in setting {}'.format(q(value), q(self.name)))
        if value > self.max:
            raise SettingRuntimeException('Value {} is violating upper bound '
                                          'in setting {}'.format(q(value), q(self.name)))
        if self.min < self.max and self.step > 0 and (value - self.min) % self.step != 0:
            raise SettingRuntimeException('Value {} is violating step requirement '
                                          'in setting {}. Step is size {}'.format(q(value), q(self.name),
                                                                                  self.step))
        return value


class IntGbToStrPrefixMbEncoder:

    @staticmethod
    def encode(value):
        return '{}m'.format(int(round(value * 1024)))

    @staticmethod
    def decode(data):
        val = data.lower()
        if val[-1] != 'm':
            raise ValueError('Invalid value {} to decode from megabytes to gigabytes.'.format(q(data)))
        return int(val[:-1]) / 1024


class StrToIntEncoder:

    @staticmethod
    def encode(value):
        return str(value)

    @staticmethod
    def decode(data):
        return int(data)


class JavaOptionSetting(RangeSetting):
    value_encoder = None

    def __init__(self, config):
        super().__init__(config)
        if self.value_encoder is None:
            raise NotImplementedError('You must provide value encoder for setting {} '
                                      'handled by class {}'.format(q(self.name), self.__class__.__name__))

    def encode_option(self, value):
        """
        Encodes single primitive value into a list of primitive values (zero or more).

        :param value: Single primitive value
        :return list: List of multiple primitive values
        """
        value = self.validate_value(value)
        return ['-XX:{}={}'.format(self.name, self.value_encoder.encode(value))]

    def validate_data(self, data):
        found_opts = list(filter(lambda arg: arg.startswith('-XX:{}'.format(self.name)), data))
        if len(found_opts) > 1:
            raise SettingRuntimeException('Received multiple values for setting {}, only one value is allowed '
                                          'on decode'.format(q(self.name)))
        if not found_opts and self.default is None:
            raise SettingRuntimeException('No value found to decode for setting {} and no '
                                          'default value was configured.'.format(q(self.name)))
        return found_opts

    def decode_option(self, data):
        """
        Decodes list of primitive values back into single primitive value

        :param data: List of multiple primitive values
        :return: Single primitive value
        """
        opts = self.validate_data(data)
        if opts:
            opt = opts[0]
            try:
                return self.value_encoder.decode(opt.split('=', 1)[1])
            except ValueError as e:
                raise SettingRuntimeException('Invalid value to decode for setting {}. '
                                              'Error: {}. Arg: {}'.format(q(self.name), str(e), opt))
        return self.default


class MaxHeapSizeSetting(JavaOptionSetting):
    value_encoder = IntGbToStrPrefixMbEncoder()
    name = 'MaxHeapSize'
    unit = 'GiB'
    min = .5
    step = .125


class GCTimeRatioSetting(JavaOptionSetting):
    value_encoder = StrToIntEncoder()
    name = 'GCTimeRatio'
    min = 9
    max = 99
    step = 1
    can_relax = False


class Encoder:

    def __init__(self, config):
        if config is None:
            config = {}
        if not isinstance(config, dict):
            raise EncoderConfigException('Configuration object for java-opts encoder is expected to be '
                                         'of a dictionary type')
        self.config = config
        self.settings = {}

        requested_settings = self.config.get('settings') or {}
        for name, setting in requested_settings.items():
            try:
                setting_class = globals()['{}Setting'.format(name)]
            except KeyError:
                raise EncoderConfigException('Setting "{}" is not supported in java-opts encoder.'.format(name))
            self.settings[name] = setting_class(setting or {})

    def describe(self):
        settings = []
        for setting in self.settings.values():
            settings.append(setting.describe())
        return dict(settings)

    def encode_multi(self, values):
        ret = []
        values_to_encode = values.copy()

        ret.extend(self.config.get('before', []))

        for name, setting in self.settings.items():
            ret.extend(setting.encode_option(values_to_encode.pop(name, None)))

        ret.extend(self.config.get('after', []))

        if values_to_encode:
            raise EncoderRuntimeException(
                'We received settings to encode we do not support {}'.format(list(values_to_encode.keys())))

        return ret


def encode(config, values):
    encoder = Encoder(config)
    settings = encoder.describe()
    setting_values_to_encode = {}
    for setting_name in settings.keys():
        if setting_name in values:
            setting_values_to_encode[setting_name] = values[setting_name]
    return encoder.encode_multi(setting_values_to_encode), settings.keys()


def describe(config, data):
    encoder = Encoder(config)
    descr = encoder.describe()
    for name, setting in encoder.settings.items():
        value = setting.decode_option(data)
        descr[name]['value'] = value
    return descr


if __name__ == '__main__':
    encoder_section = yaml.load(open('../config.yaml'))['k8s']['deployments']['d1']['command']['encoder']

    # Describe
    current_data = ['java', '-server',
                    '-XX:MaxHeapSize=1024m',
                    '-XX:GCTimeRatio=92',
                    '-javaagent:/tmp/newrelic/newrelic.jar', '-Dnewrelic.environment=l1', '-jar', '/app.jar']
    desc = describe(encoder_section, current_data)
    print('Described', desc)

    # Encode
    data_to_encode = {'MaxHeapSize': 13, 'GCTimeRatio': 99}  # , 'GCTimeRatio': 10}
    encoded = encode(encoder_section, data_to_encode)
    print('Encoded', encoded)
