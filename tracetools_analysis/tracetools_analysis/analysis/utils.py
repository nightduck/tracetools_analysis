# Copyright 2019 Robert Bosch GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module for data model utility class."""

from typing import Any
from typing import Mapping
from typing import Union

from pandas import DataFrame

from .data_model import DataModel


class DataModelUtil():
    """
    Data model utility class.

    Provides functions to get info on a data model.
    """

    def __init__(self, data_model: DataModel) -> None:
        """
        Constructor.

        :param data_model: the data model object to use
        """
        self._data = data_model

    def get_callback_symbols(self) -> Mapping[int, str]:
        """
        Get mappings between a callback object and its resolved symbol.

        :return: the map
        """
        callback_instances = self._data.callback_instances
        callback_symbols = self._data.callback_symbols

        # Get a list of callback objects
        callback_objects = set(callback_instances['callback_object'])
        # Get their symbol
        return {obj: callback_symbols.loc[obj, 'symbol'] for obj in callback_objects}

    def get_callback_durations(self, callback_obj: int) -> DataFrame:
        """
        Get durations of callback instances for a given callback object.

        :param callback_obj: the callback object value
        :return: a dataframe containing the durations of all callback instances for that object
        """
        return self._data.callback_instances.loc[
            self._data.callback_instances.loc[:, 'callback_object'] == callback_obj,
            :
        ]

    def get_callback_owner_info(self, callback_obj: int) -> Union[str, None]:
        """
        Get information about the owner of a callback.

        Depending on the type of callback, it will give different kinds of info:
          * subscription: node name, topic name
          * timer: tid, period of timer
          * service/client: node name, service name

        :param callback_obj: the callback object value
        :return: information about the owner of the callback, or `None` if it fails
        """
        # Get handle corresponding to callback object
        handle = self._data.callback_objects.loc[
            self._data.callback_objects['callback_object'] == callback_obj
        ].index.values.astype(int)[0]

        type_name = None
        info = None
        # Check if it's a timer first (since it's slightly different than the others)
        if handle in self._data.timers.index:
            type_name = 'Timer'
            info = self.get_timer_handle_info(handle)
        elif handle in self._data.publishers.index:
            type_name = 'Publisher'
            info = self.get_publisher_handle_info(handle)
        elif handle in self._data.subscriptions.index:
            type_name = 'Subscription'
            info = self.get_subscription_handle_info(handle)
        elif handle in self._data.services.index:
            type_name = 'Service'
            info = self.get_subscription_handle_info(handle)
        elif handle in self._data.clients.index:
            type_name = 'Client'
            info = self.get_client_handle_info(handle)

        if info is not None:
            info = f'{type_name} -- {self.format_info_dict(info)}'
        return info

    def get_timer_handle_info(self, timer_handle: int) -> Union[Mapping[str, Any], None]:
        """
        Get information about the owner of a timer.

        :param timer_handle: the timer handle value
        :return: a dictionary with name:value info, or `None` if it fails
        """
        # TODO find a way to link a timer to a specific node
        if timer_handle not in self._data.timers.index:
            return None

        tid = self._data.timers.loc[timer_handle, 'tid']
        period_ns = self._data.timers.loc[timer_handle, 'period']
        period_ms = period_ns / 1000000.0
        return {'tid': tid, 'period': f'{period_ms:.0f} ms'}

    def get_publisher_handle_info(self, publisher_handle: int) -> Union[Mapping[str, Any], None]:
        """
        Get information about a publisher handle.

        :param publisher_handle: the publisher handle value
        :return: a dictionary with name:value info, or `None` if it fails
        """
        if publisher_handle not in self._data.publishers.index:
            return None
        
        node_handle = self._data.publishers.loc[publisher_handle, 'node_handle']
        node_handle_info = self.get_node_handle_info(node_handle)
        topic_name = self._data.publishers.loc[publisher_handle, 'topic_name']
        publisher_info = {'topic': topic_name}
        return {**node_handle_info, **publisher_info}

    def get_subscription_handle_info(self, subscription_handle: int) -> Union[Mapping[str, Any], None]:
        """
        Get information about a subscription handle.

        :param subscription_handle: the subscription handle value
        :return: a dictionary with name:value info, or `None` if it fails
        """
        subscriptions_info = self._data.subscriptions.merge(
            self._data.nodes,
            left_on='node_handle',
            right_index=True)
        if subscription_handle not in self._data.subscriptions.index:
            return None

        node_handle = subscriptions_info.loc[subscription_handle, 'node_handle']
        node_handle_info = self.get_node_handle_info(node_handle)
        topic_name = subscriptions_info.loc[subscription_handle, 'topic_name']
        subscription_info = {'topic': topic_name}
        return {**node_handle_info, **subscription_info}

    def get_service_handle_info(self, service_handle: int) -> Union[Mapping[str, Any], None]:
        """
        Get information about a service handle.

        :param service_handle: the service handle value
        :return: a dictionary with name:value info, or `None` if it fails
        """
        if service_handle not in self._data.services:
            return None
        
        node_handle = self._data.services.loc[service_handle, 'node_handle']
        node_handle_info = self.get_node_handle_info(node_handle)
        service_name = self._data.services.loc[service_handle, 'service_name']
        service_info = {'service': service_name}
        return {**node_handle_info, **service_info}

    def get_client_handle_info(self, client_handle: int) -> Union[Mapping[str, Any], None]:
        """
        Get information about a client handle.

        :param client_handle: the client handle value
        :return: a dictionary with name:value info, or `None` if it fails
        """
        if client_handle not in self._data.clients:
            return None
        
        node_handle = self._data.clients.loc[client_handle, 'node_handle']
        node_handle_info = self.get_node_handle_info(node_handle)
        service_name = self._data.clients.loc[client_handle, 'service_name']
        service_info = {'service': service_name}
        return {**node_handle_info, **service_info}

    def get_node_handle_info(self, node_handle: int) -> Union[Mapping[str, Any], None]:
        """
        Get information about a node handle.

        :param node_handle: the node handle value
        :return: a dictionary with name:value info, or `None` if it fails
        """
        if node_handle not in self._data.nodes.index:
            return None

        node_name = self._data.nodes.loc[node_handle, 'name']
        tid = self._data.nodes.loc[node_handle, 'tid']
        return {'node': node_name, 'tid': tid}

    def format_info_dict(self, info_dict: Mapping[str, Any]) -> str:
        return ', '.join([f'{key}: {val}' for key, val in info_dict.items()])
