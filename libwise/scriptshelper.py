'''
Created on Feb 15, 2016

@author: fmertens
'''

import os
import re
import sys
import fnmatch


_SH_VERSION = None

_SH_USAGE = None

_SH_ARGS = None

c_red = "\x1b[31m"
c_green = "\x1b[32m"
c_yellow = "\x1b[33m"
c_blue = "\x1b[34m"
c_normal = "\x1b[0m"

ENABLE_COLOR = True


if sys.platform == "win32":
    ENABLE_COLOR = False


def usage(exit=False) :
    print _SH_USAGE
    if exit :
        sys.exit(0)

        
def version(exit=False) :
    print 'Version %s' % _SH_VERSION
    if exit :
        sys.exit(0)

    
def init(script_version, script_usage) :
    ''' Gestion des scipts : fonction d'initialisation. 
    
        Cette fonction gere les options --help, --version et --debug 
        
        Attention : L'option --debug est supprime de sys.argv si presente. 
        Utilisez get_debug() pour savoir si --debug a ete passe en option. 
        
        <code python>
        init(0.1, 'Utilisation : script -a -b VALEUR1 -c VALEUR2 ARG1 ARG2')
        a = get_opt_bool(None, 'a')
        b = get_opt_value(None, 'b')
        c = get_opt_value(None, 'c')
        args = scripts_helper_get_args()
        if len(args) != 2 :
            usage(True)
        </code> '''
    
    global _SH_USAGE, _SH_VERSION, _SH_ARGS
    _SH_USAGE = script_usage
    _SH_VERSION = script_version
    _SH_ARGS = sys.argv[1:]
    if '--help' in _SH_ARGS :
        usage(True)
    elif '--version' in _SH_ARGS :
        version(True)
    # elif "--debug" in _SH_ARGS :
    #     _SH_ARGS.remove("--debug")
    #     set_debug(True)
        

def get_opt_value(opt_name, opt_short_name, multiple = False, default=None) :
    ''' Gestion des scripts : retourne la valeur d'une option passe en argument
        du type --//opt_name//=value et/ou -//opt_short_name// value.
        
        //opt_short_name// doit etre une lettre.
        
        Si //multiple// = True : possibilte de passer plusieurs options en argument.
        La fonction retourne alors une liste de valeurs. 
        
        **init()** doit etre appelle avant d'utiliser cette fonction.'''
    
    global _SH_ARGS
    values = []
    i = len(_SH_ARGS) - 1
    while i >= 0 :
        if opt_name and fnmatch.fnmatch(_SH_ARGS[i], '--' + opt_name + '=*') :
            values.append(_SH_ARGS[i].split('=', 1)[1])
            del _SH_ARGS[i]
        elif opt_short_name and _SH_ARGS[i] == '-' + opt_short_name :
            if _SH_ARGS[i + 1][0] == ('-') :
                raise Exception, "Wrong value after option '-%s'" % opt_short_name
            values.append(_SH_ARGS[i + 1])
            del _SH_ARGS[i + 1]
            del _SH_ARGS[i]
        i -= 1
    if multiple :
        values.reverse()
        return values
    if len(values) == 0 :
        return default
    elif len(values) == 1 :
        return values[0]
    raise Exception, "Too much values for option '%s'" % opt_name


def get_opt_bool(opt_name, opt_short_name) :
    ''' Gestion des scripts : retourne si oui ou non (True/False) une option
        du type --//opt_name// et/ou -//opt_short_name// a ete passe en argument.
        
        //opt_short_name// doit etre une lettre.
        
        **init()** doit etre appelle avant d'utiliser cette fonction.'''
    
    global _SH_ARGS
    value = False
    i = len(_SH_ARGS) - 1
    while i >= 0 :
        if (opt_short_name and _SH_ARGS[i] == '-' + opt_short_name) \
                or (opt_name and _SH_ARGS[i] == '--' + opt_name ) :
            value = True
            del _SH_ARGS[i]
        i -= 1
    return value

def get_args(min_nargs=0) :
    ''' Gestion des scripts : retourne les arguments. C'est a dire tous ce qui n'est pas
        option. 
        
        Toutes les options doivent avoir ete gere par **get_opt_value()**
        et **get_opt_bool()**. 
        
        Si il reste des options en argument non gere, cette fonction generera une exception.
        
        **init()** doit etre appelle avant d'utiliser cette fonction.'''
    
    global _SH_ARGS
    opts = [ k for k in _SH_ARGS if k[0] == '-' ]
    if opts :
        raise Exception, "Unknow options (%s)" % ', '.join(opts)
    args = _SH_ARGS
    _SH_ARGS = []
    if len(args) < min_nargs:
        print "Error: At least %s arguments are required.\n" % min_nargs
        usage(True)

    return args


def check(arg_or_args, test, error_msg):
    if isinstance(arg_or_args, list):
        t = all(map(test, arg_or_args))
    else:
        t = test(arg_or_args)
    if t is False:
        print "Error: %s\n" % error_msg
        sh.usage(True)


def cwrite(msg, color=c_normal) :
    if not ENABLE_COLOR or color == c_normal :
        sys.stdout.write(msg)
    else :
        sys.stdout.write("%s%s%s" % (color, msg, c_normal))
    sys.stdout.flush()


def cinput(prompt) :
    cwrite(prompt, c_yellow)
    return raw_input()


def asklist(prompt, list) :
    ok = False
    assert len(list) > 0
    cwrite("%s\n" % prompt, c_yellow)
    check_list = []
    for i in range(len(list)) :
        check_list.append(i)
        cwrite(' %i : %s\n' % (i, list[i]))
    prompt = "Choice: "
    if len(list) == 1 :
        cwrite("%s\n" % prompt, c_yellow)
        if multiple :
            return [0]
        return 0
    while not ok :
        s = cinput(prompt)
        try :
            s = int(s)
            ok = bool(s in check_list)
        except ValueError :
            ok = False
        if not ok :
            cwrite("Incorrect choice\n")
    return s
    

def ask(prompt, check_fct=False, check_re=False, check_list=False, default=None) :
    ok = False
    while not ok :
        ok = True
        s = cinput(prompt + " ")
        if default is not None and s == '':
            return default
        if check_fct :
            ok = check_fct(s)
        if check_re :
            ok = re.match(check_re, s)
        if check_list :
            ok = bool(s in check_list)
        if not ok :
            cwrite("Incorrect input\n")
    return s


def askbool(prompt, default=False):
    if not default :
        choice = " (Yes/[No])"
    else :
        choice = " ([Yes]/No)"

    def check_bool(v):
        return v.lower() in ["yes", "true", "y", "1", "no", "n", "false", "0"]

    ret = ask(prompt + choice, check_fct=check_bool, default=str(default))
    return ret.lower() in ["yes", "true", "1", "y"]
