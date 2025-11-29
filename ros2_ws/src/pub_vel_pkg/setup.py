from setuptools import find_packages, setup

package_name = 'pub_vel_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ivan',
    maintainer_email='ivan.rodriguez.perez.25@gmail.com',
    description='Publisher for velocity commands',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'vel_publisher_node = pub_vel_pkg.vel_publisher:main'
        ],
    },
)

