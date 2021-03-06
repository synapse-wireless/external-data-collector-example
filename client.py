#!/usr/bin/env python

# Copyright (C) 2016 Synapse Wireless, Inc.
"""Data Collector MQTT Client script for use with Example 1"""
from __future__ import print_function

import logging

from synapse_data_collector.simple_client import simple_data_collector_client

LOG = logging.getLogger(__name__)

# Set this to point to your E20.
E20_HOSTNAME = 'localhost'


def print_poll_results(poll):
    """Print out the poll results.

    Prints out the data for each successful node.
    Prints out error codes for each failed node.
    """

    for node, data in poll['successful'].items():
        # Parse the CSV string from the node
        poll_counter, temp_dC, ps_mV, ext_temp, photo_val = [int(v) for v in data.split(',')]

        # Print out the data, converting to more common units
        print("{} {} [{}]: Int. Temp. = {} degC, Ext. Temp. = {}, PS Voltage = {} V, Light Reading = {}".format(
            poll['timestamp'], node, poll_counter, temp_dC * 0.1, ext_temp, ps_mV * 0.001, photo_val))

    for node, err_code in poll['failed'].items():
        # For failed nodes, just print out the error code.
        print("{} {}: ERROR {}".format(poll['timestamp'], node, err_code))


if __name__ == '__main__':
    logging.basicConfig()

    client = simple_data_collector_client(
        poll_cb=print_poll_results,
        metrics_cb=print,
        status_cb=print,
        host=E20_HOSTNAME,
    )
    print("Polling until CTRL-C is pressed")
    client.loop_forever()
