
import asyncio
import configparser
import time

from sagemcom_api.enums import EncryptionMethod
from sagemcom_api.client import SagemcomClient
from prometheus_client import start_http_server, Gauge

config = configparser.ConfigParser()
config.read('config.ini')

HOST = config['router']['host']
USERNAME = "admin"
PASSWORD = config['router']['pass']
ENCRYPTION_METHOD = EncryptionMethod.MD5 # or EncryptionMethod.SHA512

ip_interfaces_keys = [
    "broadcast_packets_received",
    "broadcast_packets_sent",
    "bytes_received",
    "bytes_sent",
    "discard_packets_received",
    "discard_packets_sent",
    "errors_received",
    "errors_sent",
    "multicast_packets_received",
    "multicast_packets_sent",
    "packets_received",
    "packets_sent",
    "unicast_packets_received",
    "unicast_packets_sent",
    "unknown_proto_packets_received"
]
hosts_keys = [
    "lease_duration",
    "lease_start",
    "lease_time_remaining"
]
line_keys = [
    "average_far_end_interarrival_jitter",
    "average_receive_interarrival_jitter",
    "average_round_trip_delay",
    "bytes_received",
    "bytes_sent",
    "calls_dropped",
    "far_end_interarrival_jitter",
    "far_end_packet_loss_rate",
    "incoming_calls_answered",
    "incoming_calls_connected",
    "incoming_calls_failed",
    "incoming_calls_received",
    "outgoing_calls_answered",
    "outgoing_calls_attempted",
    "outgoing_calls_connected",
    "outgoing_calls_failed",
    "overruns",
    "packets_lost",
    "packets_received",
    "packets_sent",
    "receive_interarrival_jitter",
    "receive_packet_loss_rate",
    "reset_statistics",
    "round_trip_delay",
    "server_down_time",
    "total_call_time",
    "underruns"
]
interfaces = {}
for key in ip_interfaces_keys:
    interfaces["ip_interfaces_" + key] = Gauge('ip_interfaces_' + key, '', ['alias', 'type', 'status'])
    interfaces["ppp_interfaces_" + key] = Gauge('ppp_interfaces_' + key, '', ['alias', 'ifc_name', 'status'])
    interfaces["sfp_interfaces_" + key] = Gauge('sfp_interfaces_' + key, '', ['alias', 'ifc_name', 'status'])
    interfaces["ethernet_interfaces_" + key] = Gauge('ethernet_interfaces_' + key, '', ['alias', 'ifc_name', 'status'])

for key in hosts_keys:
    interfaces["host_" + key] = Gauge('host_' + key, '', ['alias', 'host_name', 'interface_type', 'ip_address', 'phys_address', 'active'])

for key in line_keys:
    interfaces["voice_line_" + key] = Gauge('voice_line_' + key, '', ['status', 'name'])

async def interfaces_metrics(client, key, xpath, l2):
    result = await client.get_value_by_xpath(xpath)
    for inf in result:
        for if_key in ip_interfaces_keys:
            if if_key in inf['stats']:
                interfaces[key + "_interfaces_" + if_key].labels(inf['alias'], inf[l2], inf['status']).set(inf['stats'][if_key])


async def hosts_metrics(client):
    result = await client.get_value_by_xpath('Device/Hosts/Hosts')
    for host in result:
        for if_key in hosts_keys:
            if if_key in host:
                interfaces["host_" + if_key].labels(host['alias'], host['host_name'], host['interface_type'], host['ip_address'], host['phys_address'], host['active']).set(host[if_key])

async def voice_metrics(client):
    result = await client.get_value_by_xpath('Device/Services/VoiceServices/VoiceService[@uid=1]/VoiceProfiles/VoiceProfile[@uid=1]/Lines')
    for line in result:
        for if_key in line_keys:
            if if_key in line['stats']:
                interfaces["voice_line_" + if_key].labels(line['status'], line['name']).set(line['stats'][if_key])

async def scrape() -> None:
    async with SagemcomClient(HOST, USERNAME, PASSWORD, ENCRYPTION_METHOD) as client:
        try:
            await client.login()
        except Exception as exception:  # pylint: disable=broad-except
            print(exception)
            return

        await interfaces_metrics(client, 'ip', 'Device/IP/Interfaces', 'type')
        await interfaces_metrics(client, 'ppp', 'Device/PPP/Interfaces', 'ifc_name')
        await interfaces_metrics(client, 'sfp', 'Device/SFP/Interfaces', 'ifc_name')
        await interfaces_metrics(client, 'ethernet', 'Device/Ethernet/Interfaces', 'ifc_name')
        await hosts_metrics(client)
        await voice_metrics(client)

if __name__ == '__main__':
    start_http_server(int(config['prometheus']['port']))

    while True:
        asyncio.run(scrape())
        time.sleep(10)
