#!/usr/bin/env python
# ----------------------------------------------------------------------------
# A collection of functions that calls Galaxy API in order to perform and/or
# automatize various operations in the galaxy environment.
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.histories import HistoryClient
from bioblend.galaxy.users import UserClient

GALAXY_URL = 'http://localhost:8080/'
# TODO: for now the initial instance is retrieve through the admin API_KEY (TO BE CHANGED)
API_KEY = '3c602bf64a18247b2f892a28dd0a0b72 '
galaxy_instance = GalaxyInstance(url=GALAXY_URL, key=API_KEY)


def get_user_key():
    uc = UserClient(galaxy_instance)
    user_id = uc.get_current_user()['id']
    API_KEY = uc.get_api_key(user_id)


def delete_user_token():
    hi = HistoryClient(galaxy_instance)

    history = hi.get_most_recently_used_history()
    history_id = history['id']

    state = {}

    state = history['state_ids']
    current_datasets = state['ok']

    for ds in current_datasets:
        dataset = {}
        dataset = hi.show_dataset(history_id, ds)

        if dataset['name'] == 'User':
            if dataset['deleted'] == False: hi.delete_dataset(history_id, ds)
