import os
os.environ['DISTUTILS_DEBUG'] = "1"
__dir__ = os.path.dirname(__file__)
os.chdir(os.path.realpath(__dir__))



from distutils.core import setup, Extension


def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

def get_packages(main_dir):
    #Copied / inspired from http://code.djangoproject.com/browser/django/trunk/setup.py#L45
    packages, data_files = [], []
    for dirpath, dirnames, filenames in os.walk(main_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
    return packages


def get_detour_files():
    ret = []
    detour_dir = os.path.join(__dir__, 'pydetour', 'pydetour')
    for dirpath, dirnames, filenames in os.walk(detour_dir):
        for name in (name for name in filenames if name.lower().endswith('.cpp')):
            fn = os.path.join(dirpath,  name)
            ret.append(fn)
    return ret


_detour = Extension('_detour', get_detour_files())


params = dict(
    packages = get_packages('pyhack'),
    #ext_modules=[_detour],
    #scripts = ['pyhack/bin/pyhack-admin.py'],

)


setup(
    name='pyhack',
    version='0.1',
    url='http://cbwhiz.com',
    author='CBWhiz',
    author_email='CBWhiz@gmail.com',
    description = 'A mid-level framework for modifying runtime behavior and memory of x86 processes under Windows.',
    download_url = '',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 2'
        'Programming Language :: Python :: 2.6',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Software Development :: Disassemblers'
    ],
    **params
)
