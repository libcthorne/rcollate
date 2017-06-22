from setuptools import setup

setup(
    name='rcollate',
    packages=['rcollate'],
    include_package_data=True,
    install_requires=[
        'APScheduler==3.3.1',
        'emails==0.5.14',
        'Flask==0.12.2',
        'Jinja2==2.9.6',
        'praw==4.5.1',
    ],
)
