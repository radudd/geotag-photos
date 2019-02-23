#!/usr/bin/env python

import yaml
from pymongo import MongoClient


class MongoConnector():
    """Description:
            Implements Context managers, by specifying __enter__ and __exit__
            The DB name 'photos' and collection name 'metadata' are hardcoded!

       Usage:
            mongo = MongoConnector()
            with mongo:
                ...

       Raises:

    """
    def __init__(self):
        with open('config.yaml', 'rt') as f:
            config = yaml.load(f)
        self.mongo_uri = 'mongodb://{}:{}@{}/{}'.format(
                    config['mongo_user'],
                    config['mongo_pass'],
                    config['mongo_host'],
                    config['mongo_db']
                    )

    def __enter__(self):
        # try:
        self.connector = MongoClient(self.mongo_uri)
        self.connector.photos.metadata.ensure_index('date', unique=True)
        return self.connector.photos.metadata

    def __exit__(self, type, value, tb):
        self.connector.close()