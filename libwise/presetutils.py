import os
import matplotlib

RC_DEFAULTS = matplotlib.RcParams(matplotlib.rcParams.copy())

PRESETS_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'presets')


def set_rc_preset(preset_name, kargs={}):
    preset = RcPreset.load(preset_name)
    for key, value in kargs.items():
        preset.set_key(key, value)
    preset.apply()


def get_all_presets():
    presets_list = []
    for file in os.listdir(PRESETS_PATH):
        if file.endswith(".preset"):
            try:
                preset = RcPreset.load(file)
                presets_list.append(preset)
            except Exception, e:
                print "Error reading %s: %s" % (file, e)
    return presets_list


def print_all_rc_keys():
    conf = {}
    for key, value in matplotlib.rcParams.items():
        if "." in key:
            a, b = key.split(".", 1)
            if not a in conf:
                conf[a] = []
            conf[a].append([b, value])

    for key in sorted(conf.keys()):
        print "=======", key, "======="
        for el_key, el_value in conf[key]:
            print "%s: %s" % (el_key, el_value)
        print ""


class RcPreset(object):

    key_blacklist = ['backend', 'toolbar', 'backend_fallback',
                     'interactive', 'timezone', 'datapath']
    group_blacklist = ['agg', 'backend', 'cairo', 'docstring',
                       'examples', 'keymap', 'plugins', 'tk', 'verbose']

    def __init__(self, name):
        self.name = name
        self.rc_params = matplotlib.RcParams(RC_DEFAULTS.copy())
        self.preset_params = set()

    def __str__(self):
        return self.name

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def is_preset(self, group, setting):
        key = '.'.join([group, setting])
        # if key in self.preset_params and group == 'axes':
        #     print self.preset_params
        return key in self.preset_params

    def get_groups(self):
        families = set()
        for key, value in self.get_all():
            group, setting = key.split('.', 1)
            if not group in RcPreset.group_blacklist:
                families.add(group)
        return sorted(list(families))

    def get_settings(self, group):
        for key, value in self.get_all():
            g, setting = key.split('.', 1)
            if g == group:
                yield setting, value

    def get_all(self):
        for key, value in self.rc_params.items():
            if key in RcPreset.key_blacklist:
                continue
            yield (key, value)

    def get_key(self, key):
        if key in self.rc_params:
            return self.rc_params[key]
        return None

    def get(self, group, setting):
        key = '.'.join([group, setting])
        return self.get_key(key)

    def set_key(self, key, value):
        if key in self.rc_params:
            if isinstance(value, str) and value[0] == "[" and value[-1] == "]":
                str_value = value[1:-1]
                value = []
                for item in str_value.split(','):
                    value.append(item.strip('\'" '))
            self.rc_params[key] = value
            self.preset_params.add(key)

    def set(self, group, setting, value):
        key = '.'.join([group, setting])
        self.set_key(key, value)

    def has_default(self, group, setting):
        key = '.'.join([group, setting])
        return key in RC_DEFAULTS

    def set_default(self, group, setting):
        key = '.'.join([group, setting])
        if key in matplotlib.rcParams:
            self.set_key(key, RC_DEFAULTS[key])
            self.preset_params.remove(key)

    @staticmethod
    def get_filename(preset_name):
        return "%s.preset" % preset_name

    @staticmethod
    def load(preset_name):
        if preset_name.endswith(".preset"):
            filename = preset_name
            preset_name = preset_name[:-len(".preset")]
        else:
            filename = RcPreset.get_filename(preset_name)
        path = os.path.join(PRESETS_PATH, filename)
        preset = RcPreset(preset_name)
        with open(path) as fd:
            for line in fd.readlines():
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                preset.set_key(key, value)
        return preset

    def save(self):
        filename = RcPreset.get_filename(self.name)
        path = os.path.join(PRESETS_PATH, filename)

        l = ["name:%s\n" % self.name]
        for key, value in self.rc_params.items():
            if key in self.preset_params:
                l.append("%s:%s\n" % (key, value))

        with open(path, 'w') as fd:
            fd.writelines(sorted(l))

        print "Saved preset:", self.get_name()

    def apply(self, figure=None, figsize=None):
        print "Applying preset:", self.name
        matplotlib.rcParams.update(self.rc_params)
        if figure is not None:
            if figsize is None:
                figsize = self.rc_params['figure.figsize']
            figure.set_size_inches(*figsize)

