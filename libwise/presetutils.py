import os
import glob
import appdirs
import matplotlib

import nputils

import pkg_resources

RC_DEFAULTS = matplotlib.RcParams(matplotlib.rcParams.copy())

DEFAULT_PRESETS_PATH = 'presets'

USER_PRESETS_PATH = appdirs.user_data_dir('libwise')

mpl_1_5 = float(matplotlib.__version__[:3]) >= 1.5


def set_rc_preset(preset_name, kargs={}):
    preset = RcPreset.load(preset_name)
    for key, value in kargs.items():
        preset.set_key(key, value)
    preset.apply()


def set_color_cycles(colors):
    if mpl_1_5:
        matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler('color', colors)
    else:
        matplotlib.rcParams["axes.color_cycle"] = colors


def get_all_user_presets_names():
    return [os.path.basename(k) for k in glob.glob(os.path.join(USER_PRESETS_PATH, '*.preset'))]


def get_all_default_presets_names():
    return pkg_resources.resource_listdir(__name__, 'presets')


def get_all_presets():
    presets_list = dict()
    for file_name in get_all_default_presets_names():
        try:
            preset = RcPreset._load_default(file_name)
            presets_list[preset.get_name()] = preset
        except Exception, e:
            print "Error reading %s: %s" % (file_name, e)

    for file_name in get_all_user_presets_names():
        try:
            preset = RcPreset._load_user(file_name)
            presets_list[preset.get_name()] = preset
        except Exception, e:
            print "Error reading %s: %s" % (file_name, e)

    return nputils.get_values_sorted_by_keys(presets_list)


def print_all_rc_keys():
    conf = {}
    for key, value in matplotlib.rcParams.items():
        if "." in key:
            a, b = key.split(".", 1)
            if a not in conf:
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

    @staticmethod
    def compat(key, value):
        if isinstance(value, str) and value[0] == "[" and value[-1] == "]":
            str_value = value[1:-1]
            value = []
            for item in str_value.split(','):
                if item.startswith("u'") or item.startswith("u'"):
                    item = item[1:]
                value.append(item.strip('\'" '))
        if mpl_1_5 and key == 'axes.color_cycle':
            key = 'axes.prop_cycle'
            value = matplotlib.cycler('color', value)
        return key, value

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def is_preset(self, group, setting):
        key = '.'.join([group, setting])
        # if key in self.preset_params and group == 'axes':
        #     print self.preset_params
        return key in self.preset_params

    def get_groups(self, display=False):
        families = set()
        for key, value in self.get_all():
            group, setting = key.split('.', 1)
            if group not in RcPreset.group_blacklist:
                families.add(group)
        return sorted(list(families))

    def get_all(self, display=False):
        for key, value in self.rc_params.items():
            if key in RcPreset.key_blacklist:
                continue
            value = self.get_key(key, display=display)
            yield (key, value)

    def get_settings(self, group, display=False):
        for key, value in self.get_all(display=display):
            g, setting = key.split('.', 1)
            if g == group:
                yield setting, value

    def get(self, group, setting, display=False):
        key = '.'.join([group, setting])
        return self.get_key(key, display=display)

    def get_key(self, key, display=False):
        if key in self.rc_params:
            value = self.rc_params[key]
            if display and isinstance(value, list):
                value = ', '.join([str(k) for k in value])
                # for i in range(len(value)):
                #     if isinstance(value[i], unicode):
                #         value[i] = str(value[i])
            return value
        return None

    def set_key(self, key, value):
        key, value = self.compat(key, value)
        if key in self.rc_params:
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
    def _load_stream(preset_name, fd_or_stream):
        if preset_name.endswith(".preset"):
            preset_name = preset_name[:-len(".preset")]

        preset = RcPreset(preset_name)
        for line in fd_or_stream.readlines():
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            preset.set_key(key, value)

        return preset

    @staticmethod
    def _load_default(file_name):
        stream = pkg_resources.resource_stream(__name__, os.path.join('presets', file_name))
        return RcPreset._load_stream(file_name, stream)

    @staticmethod
    def _load_user(file_name):
        with open(os.path.join(USER_PRESETS_PATH, file_name)) as fd:
            return RcPreset._load_stream(file_name, fd)

    @staticmethod
    def load(preset_name):
        if preset_name.endswith(".preset"):
            filename = preset_name
        else:
            filename = RcPreset.get_filename(preset_name)

        if filename in get_all_user_presets_names():
            return RcPreset._load_user(filename)
        elif filename in get_all_default_presets_names():
            return RcPreset._load_default(filename)
        else:
            print "Preset name '%s' not found" % preset_name
            return None

    def save(self):
        filename = RcPreset.get_filename(self.name)
        if not os.path.exists(USER_PRESETS_PATH):
            os.makedirs(USER_PRESETS_PATH)
        path = os.path.join(USER_PRESETS_PATH, filename)

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


if __name__ == '__main__':
    print RcPreset.load('display').get('font', 'fantasy')
