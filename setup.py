from distutils.core import setup

setup(name = "geogag_photos",
    version = "1.0",
    description = "Geotags photos, extract location using ExifTools and OpenMaps API and rename directories based on their location",
    author = "Radu Domnu",
    author_email = "radu.domnu@gmail.com",
    url="https://github.com/pypa/geotag",
    install_requires=[
          'exiftools',
          'requests',
          'pymongo'
      ],
    classifiers=[
     "Programming Language :: Python :: 3",
     "License :: OSI Approved :: MIT License",
     "Operating System :: OS Independent",
    ],
    long_description = """Exif Metadata, directory date, OpenMaps API URLs are stored in a MongoDB. 
    There is also an own cache implementation for ExifMetadata and OpenMaps URL responses""" ,
) 
