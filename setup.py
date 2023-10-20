from distutils.core import setup
import py2exe

setup(
    console=['app.py'],
    options={
        'py2exe': {
            'packages': ['flask'],
            'includes': ['jinja2', 'werkzeug'],
        }
    },
    data_files=[
        ('templates', ['templates/index.html']),
    ]
)
