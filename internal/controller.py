import os
import sys
import time
from pprint import pprint
from tabulate import tabulate
from loguru import logger

#SDE_PYTHON3 = os.path.join(os.environ["SDE_INSTALL"], "lib", "python3.8", "site-packages")
SDE_PYTHON3 = "/bfrt_packages/site-packages"
sys.path.append(SDE_PYTHON3)
sys.path.append(os.path.join(SDE_PYTHON3, "tofino"))
sys.path.append(os.path.join(SDE_PYTHON3, "tofino", "bfrt_grpc"))
import bfrt_grpc.client as gc
from bfrt_grpc.client import BfruntimeReadWriteRpcException

DEFAULT_GRPC_ADDRESS = "localhost:50052"
SLICE_IDENT_TABLE = "Ingress.slice_ident"
EGRESS_TABLE = "Ingress.egress_check"
VLAN_TABLE = "Ingress.vlan_exact"
FIREWALL_TABLE = "Ingress.firewall"
RETRY_ATTEMPTS = 3
PROBE_INTERVAL = 10
FROM_HW = False
PKT_GEN_PORT = 68

PARAM_NAME = {
    "bytes": [
        "$METER_SPEC_CIR_KBPS",
        "$METER_SPEC_PIR_KBPS",
        "$METER_SPEC_CBS_KBITS",
        "$METER_SPEC_PBS_KBITS",
    ],
    "packets": [
        "$METER_SPEC_CIR_PPS",
        "$METER_SPEC_PIR_PPS",
        "$METER_SPEC_CBS_PKTS",
        "$METER_SPEC_PBS_PKTS",
    ],
}
ANNOTATIONS = ["ipv4", "ipv6", "mac", "bytes"]


class Client:
    # Wrapper to a grpc client connected to the BF Runtime

    def __init__(self, grpc_addr=DEFAULT_GRPC_ADDRESS, client_id=0):
        # Add custom bfrt required packages to python path so they are usable
        device_id = 0
        try:
            self.interface = gc.ClientInterface(
                grpc_addr=grpc_addr,
                client_id=client_id,
                device_id=device_id,
                num_tries=RETRY_ATTEMPTS,
            )
            self.target = gc.Target(device_id=device_id, pipe_id=0xFFFF)
            self.bfrt_info = self.interface.bfrt_info_get()
            self.gc = gc
            logger.info(f"The target runs the program {self.bfrt_info.p4_name_get()}")
            self.interface.bind_pipeline_config(self.bfrt_info.p4_name_get())
            logger.info(f"Connected to BF Runtime Server as client {client_id}")
        except Exception:
            logger.exception(f"Could not connect to BF Runtime server - exiting")
            self.interface = None
            sys.exit(1)

    def get_table(self, table_name):
        return self.bfrt_info.table_get(table_name)

    def get_base_info(self):
        logger.info("Getting base info of tables")
        data = []
        for name in self.bfrt_info.table_dict.keys():
            if name.split(".")[0] == "pipe":
                t = self.bfrt_info.table_get(name)
                table_name = t.info.name_get()
                if table_name != name:
                    continue
                table_type = t.info.type_get()
                try:
                    result = t.usage_get(self.target)
                    table_usage = next(result)
                except:
                    table_usage = "n/a"
                table_size = t.info.size_get()
                data.append([table_name, table_type, table_usage, table_size])
        print(tabulate(data, headers=["Full Table Name", "Type", "Usage", "Capacity"]))
        return data

    def get_port_info(self):
        keys_enabled = []
        port_data = []
        logger.info("Ports that are enabled:")

        port_table = self.get_table("$PORT")
        resp = port_table.entry_get(self.target, [], {"from_hw": FROM_HW})
        for data, key in resp:
            key_dict = key.to_dict()
            data_dict = data.to_dict()
            if data_dict["$PORT_ENABLE"]:
                keys_enabled.append(key)
                port_data.append([key_dict, data_dict["$PORT_NAME"], data_dict["$PORT_ENABLE"], data_dict["$PORT_UP"], data_dict["$SPEED"]])

        port_stat_table = self.get_table("$PORT_STAT")
        resp = port_stat_table.entry_get(self.target, keys_enabled, {"from_hw": FROM_HW})
        for index, (data, _) in enumerate(resp):
            data_dict = data.to_dict()
            port_data[index] += [
                data_dict["$FramesReceivedAll"],
                data_dict["$FramesTransmittedAll"],
            ]
        print(tabulate(port_data, headers=["Key", "Name", "Enabled", "Up", "Speed", "FramesReceived", "FramesTransmitted"]))
        return port_data

    def info_table(self, table):
        logger.info(f"Getting Information on Table: {table.info.name_get()}")
        table_info = table.info
        table_name = table_info.name_get()
        table_size = table_info.size_get()
        table_type = table_info.type_get()
        print(f"\nName: {table_name}\nSize: {table_size}\nType: {table_type}\n")

        key_field_info = []
        for key_field in table_info.key_field_name_list_get():
            df_type = table_info.key_field_type_get(key_field)
            df_size = table_info.key_field_size_get(key_field)
            kf_match_type = table_info.key_field_match_type_get(key_field)
            key_field_info.append((key_field, df_type, df_size[1], kf_match_type))
        print(tabulate(key_field_info, headers=["Key Field Name", "Type", "Size (bits)", "Match Type"]))

        action_info = []
        for action in table_info.action_name_list_get():
            print(f"\nData fields for action: {action}")
            for data_field in table_info.data_field_name_list_get(action):
                df_type = table_info.data_field_type_get(data_field, action_name=action)
                df_size = table_info.data_field_size_get(data_field, action_name=action)
                df_required = table_info.data_field_mandatory_get(data_field, action_name=action)
                action_info.append((data_field, df_type, df_size[1], df_required))
            print(tabulate( action_info, headers=["Data Field Name", "Type", "Size (bits)", "Required"]))

    def dump_table(self, table):
        logger.info(f"Dumping Table: {table.info.name_get()}")
        resp = table.entry_get(self.target, [], {"from_hw": FROM_HW})
        for data, key in resp:
            key_dict = key.to_dict()
            data_dict = data.to_dict()
            pprint(key_dict)
            pprint(data_dict)

    def dump_entry(self, table, key):
        resp = table.entry_get(self.target, [key], {"from_hw": FROM_HW})
        for data, key in resp:
            key_dict = key.to_dict()
            data_dict = data.to_dict()
            pprint(key_dict)
            pprint(data_dict)

    def add_slice_entry(self, slice_id, src_addr, dst_addr, src_port, dst_port, protocol):
        if not self._valid_slice_id(slice_id):
            raise InvalidInputException("Invalid Slice ID")
        slice_ident_table = self.get_table(SLICE_IDENT_TABLE)
        slice_ident_table.info.key_field_annotation_add(field_name="src_addr", custom_annotation="ipv4")
        slice_ident_table.info.key_field_annotation_add(field_name="dst_addr", custom_annotation="ipv4")
        slice_ident_key = slice_ident_table.make_key(
            [
                gc.KeyTuple("hdr.ipv4.src_addr", src_addr),
                gc.KeyTuple("hdr.ipv4.dst_addr", dst_addr),
                gc.KeyTuple("meta.src_port", src_port),
                gc.KeyTuple("meta.dst_port", dst_port),
                gc.KeyTuple("hdr.ipv4.protocol", protocol),
            ]
        )
        slice_ident_data = slice_ident_table.make_data([gc.DataTuple("slice_id", slice_id)], "set_sliceid")
        return self.add_entry(slice_ident_table, slice_ident_key, slice_ident_data)

    def delete_slice_entry(self, src_addr, dst_addr, src_port, dst_port, protocol):
        slice_ident_table = self.get_table(SLICE_IDENT_TABLE)
        slice_ident_table.info.key_field_annotation_add(field_name="src_addr", custom_annotation="ipv4")
        slice_ident_table.info.key_field_annotation_add(field_name="dst_addr", custom_annotation="ipv4")
        slice_ident_key = slice_ident_table.make_key(
            [
                gc.KeyTuple("hdr.ipv4.src_addr", src_addr),
                gc.KeyTuple("hdr.ipv4.dst_addr", dst_addr),
                gc.KeyTuple("meta.src_port", src_port),
                gc.KeyTuple("meta.dst_port", dst_port),
                gc.KeyTuple("hdr.ipv4.protocol", protocol),
            ]
        )
        return self.delete_entry(slice_ident_table, slice_ident_key)

    def _valid_slice_id(self, slice_id):
        slice_ident = self.get_table(SLICE_IDENT_TABLE)
        max_slices = slice_ident.info.size_get()
        return slice_id >= 0 and slice_id < int(max_slices)

    def size_slice_ident(self):
        slice_ident = self.get_table(SLICE_IDENT_TABLE)
        return slice_ident.info.size_get()

    def add_vlan_entry(self, vlan_id, dst_addr, port):
        if not self._valid_slice_id(vlan_id):
            raise InvalidInputException("Invalid Slice ID")
        vlan_table = self.get_table(VLAN_TABLE)
        vlan_table.info.data_field_annotation_add(field_name="dst_addr", custom_annotation="mac", action_name="vlan_forward")
        vlan_table_key = vlan_table.make_key([gc.KeyTuple("hdr.vlan.vlan_id", vlan_id)])
        vlan_table_data = vlan_table.make_data([gc.DataTuple("dst_addr", dst_addr), gc.DataTuple("port", port)],"vlan_forward")
        return self.add_entry(vlan_table, vlan_table_key, vlan_table_data)

    def add_egress_entry(self, port):
        egress_table = self.get_table(EGRESS_TABLE)
        egress_table_key = egress_table.make_key([gc.KeyTuple("ig_tm_md.ucast_egress_port", port)])
        egress_table_data = egress_table.make_data([], "is_egress_border")
        return self.add_entry(egress_table, egress_table_key, egress_table_data)

    def add_firewall_entry(self, src_addr, prefix_len):
        firewall_table = self.get_table(FIREWALL_TABLE)
        firewall_table.info.key_field_annotation_add(field_name="src_addr", custom_annotation="ipv4")
        vlan_table_key = firewall_table.make_key([gc.KeyTuple(name="hdr.ipv4.src_addr", value=src_addr, prefix_len=prefix_len)])
        firewall_table_data = firewall_table.make_data([], "drop")
        return self.add_entry(firewall_table, vlan_table_key, firewall_table_data)

    def add_mfilter_entry(self, meter_tag):
        m_filter = self.get_table("Ingress.m_filter")
        m_filter_key = m_filter.make_key([gc.KeyTuple("meta.meter_tag", meter_tag)])
        m_filter_data = m_filter.make_data([], "drop")
        return self.add_entry(m_filter, m_filter_key, m_filter_data)

    def add_entry(self, table, key, data):
        try:
            name = table.info.name_get()
            table.entry_add(self.target, [key], [data])
        except BfruntimeReadWriteRpcException:
            logger.warning(f"Error adding table entry, likely already exists trying entry_mod()")
            table.entry_mod(self.target, [key], [data])
            logger.info("Modified entry succesfully!")
            logger.info(f"Programmed table {name} sucessfully with the following information:")
            self.dump_entry(table=table, key=key)
            return True
        except Exception:
            logger.exception(f"Adding entry failed!")
            return False
        else:
            logger.info(f"Programmed table sucessfully with the following information:")
            self.dump_entry(table=table, key=key)
            return True

    def delete_entry(self, table, key):
        try:
            table.entry_del(self.target, [key])
            logger.info(f"Deleted entry sucessfully!")
            return True
        except Exception:
            logger.exception(f"Deleting entry failed!")
            return False

    def program_meter(self, meter, meter_index, meter_type, cir, pir, cbs, pbs):
        key = meter.make_key([gc.KeyTuple("$METER_INDEX", meter_index)])
        data = meter.make_data(
            [
                gc.DataTuple(PARAM_NAME[meter_type][0], cir),
                gc.DataTuple(PARAM_NAME[meter_type][1], pir),
                gc.DataTuple(PARAM_NAME[meter_type][2], cbs),
                gc.DataTuple(PARAM_NAME[meter_type][3], pbs),
            ]
        )
        return self.add_entry(meter, key, data)

    def loop_digest(self, base_model):
        probe = {}
        t_end = time.time() + PROBE_INTERVAL
        while time.time() < t_end:
            digest = self.single_digest(base_model)
            if digest:
                hash_digest = hash(tuple(sorted(digest.items())))
                if not hash_digest in probe:
                    probe[hash_digest] = digest
        return probe

    def single_digest(self, base_model):
        """
        base_model = client.bfrt_info.learn_get("digest_inst")
        base_model.info.data_field_annotation_add("srcAddr", "ipv4")
        """
        try:
            digest = self.interface.digest_get(timeout=PROBE_INTERVAL)
            data_list = base_model.make_data_list(digest)

            for item in data_list:
                data_dict = item.to_dict()
                data_dict.pop('action_name', None)
                data_dict.pop('is_default_entry', None)
                return data_dict
        except RuntimeError:
            logger.info("No digest message received this cycle!")
            return None

    def generate_packets(self, packet, interval_nanoseconds=1000000000):
        logger.info("Configuring packet gen tables to generate Packets")
        pktgen_port = self.get_table("tf1.pktgen.port_cfg")
        pktgen_buffer = self.get_table("tf1.pktgen.pkt_buffer")
        pktgen_app = self.get_table("tf1.pktgen.app_cfg")

        logger.info(f"Sending out packets with length: {len(packet)}")
        pktgen_port_key = pktgen_port.make_key([gc.KeyTuple("dev_port", self.PKT_GEN_PORT)])
        pktgen_port_action_data = pktgen_port.make_data([gc.DataTuple("pktgen_enable", bool_val=True)])
        self.add_entry(pktgen_port, pktgen_port_key, pktgen_port_action_data)

        offset = 0
        pktgen_pkt_buf_key = pktgen_buffer.make_key(
            [
                gc.KeyTuple("pkt_buffer_offset", offset),
                gc.KeyTuple("pkt_buffer_size", len(packet)),
            ]
        )
        pktgen_pkt_buf_action_data = pktgen_buffer.make_data([gc.DataTuple("buffer", bytearray(bytes(packet)))])
        self.add_entry(pktgen_buffer, pktgen_pkt_buf_key, pktgen_pkt_buf_action_data)

        pktgen_app_key = pktgen_app.make_key([gc.KeyTuple("app_id", 0)])
        pktgen_app_action_data = pktgen_app.make_data(
            [
                gc.DataTuple("timer_nanosec", interval_nanoseconds),
                gc.DataTuple("app_enable", bool_val=True),
                gc.DataTuple("pkt_len", len(packet)),
                gc.DataTuple("pkt_buffer_offset", 0),
                gc.DataTuple("pipe_local_source_port", 68),
                gc.DataTuple("increment_source_port", bool_val=False),
                gc.DataTuple("batch_count_cfg", 0),
                gc.DataTuple("packets_per_batch_cfg", 1),
                gc.DataTuple("ibg", 10000),
                gc.DataTuple("ibg_jitter", 0),
                gc.DataTuple("ipg", 500),
                gc.DataTuple("ipg_jitter", 1000),
                gc.DataTuple("batch_counter", 0),
                gc.DataTuple("pkt_counter", 0),
                gc.DataTuple("trigger_counter", 0),
            ],
            "trigger_timer_periodic",
        )
        self.add_entry(pktgen_app, pktgen_app_key, pktgen_app_action_data)


class InvalidInputException(Exception):
    pass
