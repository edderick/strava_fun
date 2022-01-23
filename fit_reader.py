import struct
import gzip
from datetime import datetime, timedelta

_VERBOSE = False

_PRINT_HEADER = False
_PRINT_DATA = False
_PRINT_DATA_FIELDS = False
_PRINT_RECORD = False  # Print the fields if the data is of RECORD type
_PRINT_DEFINITIONS = False


def _get_bit(value, bit_index):
    return (value & (1 << bit_index)) >> bit_index


_GLOBAL_MESSAGE_NAMES = {
    0: "FILE_ID",
    2: "DEVICE_SETTINGS",
    3: "USER_PROFILE",
    7: "ZONES_TARGET",
    12: "SPORT",
    13: "UNKNOWN (13)",
    15: "GOAL",
    18: "SESSION",
    19: "LAP",
    20: "RECORD",
    21: "EVENT",
    22: "UNKNOWN (22)",
    23: "DEVICE_INFO",
    34: "ACTIVITY",
    49: "FILE_CREATOR",
    72: "TRAINING_FILE",
    78: "HRV",
    79: "UNKNOWN (79)",
    101: "LENGTH",
    104: "UNKNOWN (104)",
    113: "UNKNOWN (113)",
    125: "UNKNOWN (125)",
    140: "UNKNOWN (140)",
    141: "UNKNOWN (141)",
    142: "SEGMENT_LAP",
    147: "UNKNOWN (147)",
    195: "UNKNOWN (195)",
    206: "FIELD_DESCRIPTION",
    207: "DEVELOPER_DATA_ID",
    216: "UNKNOWN (216)",
}

_FIT_RECORD_FIELDS = {
    253: "TIMESTAMP",
    0: "POSITION_LAT",
    1: "POSITION_LON",
    5: "DISTANCE",
    11: "TIME_FROM_COURSE",
    19: "TOTAL_CYCLES",
    29: "ACCUMULATED_POWER",
    73: "ENHANCED_SPEED",
    78: "ENHANCED_ALTITUDE",
    2: "ALTITUDE",
    6: "SPEED",
    61: "UNKNOWN",
    66: "UNKNOWN",
    7: "POWER",
    9: "GRADE",
    3: "HEART_RATE",
    4: "CADENCE",
    13: "TEMPERATURE",
    50: "ZONE",
    53: "FRACTIONAL_CADENCE",
    62: "DEVICE_INDEX",
    88: "UNKNOWN",
}

_FIT_SESSION_FIELDS = {
    5: "SPORT",
}

_SPORT_TYPES = {
    0: "GENERIC",
    1: "RUNNING",
    2: "CYCLING",
    3: "TRANSITION",
    4: "FITNESS_EQUIPMENT",
    5: "SWIMMING",
    17: "HIKING",
    21: "E-BIKING",
}

_DATA_TYPES = {
    0: {"name": "enum", "string": "b", "size": 1},
    1: {"name": "sint8", "string": "b", "size": 1},
    2: {"name": "uint8", "string": "B", "size": 1},
    3: {"name": "sint16", "string": "h", "size": 2},
    4: {"name": "uint16", "string": "H", "size": 2},
    5: {"name": "sint32", "string": "i", "size": 4},
    6: {"name": "uint32", "string": "I", "size": 4},
    7: {"name": "string", "string": "s", "size": 1},
    8: {"name": "float32", "string": "f", "size": 4},
    9: {"name": "float64", "string": "d", "size": 8},
    10: {"name": "uint8z", "string": "B", "size": 1},
    11: {"name": "uint16z", "string": "H", "size": 2},
    12: {"name": "uint32z", "string": "I", "size": 4},
    13: {"name": "byte", "string": "b", "size": 1},
    14: {"name": "sint64", "string": "q", "size": 8},
    15: {"name": "uint64", "string": "Q", "size": 8},
    16: {"name": "unit64z", "string": "Q", "size": 8},
}


class FitFileReader:
    def __init__(self):
        self._data_definitions = {}
        self._records = []

    def process_fit_file(self, filename):
        self.reset()

        if filename[-2:] == "gz":
            open_func = gzip.open
        else:
            open_func = open

        with open_func(filename, "rb") as self._fit_file:
            if _VERBOSE:
                print(f"Processing: {self._fit_file.name}")

            self._process_file_header()

            while self._fit_file.tell() < self._data_size:
                self._process_record()

        return self._records

    def _process_file_header(self):
        self._header_size = self._fit_file.read(1)[0]
        header = self._fit_file.read(self._header_size - 1)

        if self._header_size == 14:
            (
                self._protocol_version,
                self._profile_version,
                self._data_size,
                self._data_type,
                self._crc,
            ) = struct.unpack("<BHI4sH", header)
        elif self._header_size == 12:
            (
                self._protocol_version,
                self._profile_version,
                self._data_size,
                self._data_type,
            ) = struct.unpack("<BHI4s", header)

        if _VERBOSE or _PRINT_HEADER:
            print(f"=====================================")
            print(f"Header Size: {self._header_size}")
            print(f"Protocol Version: {self._protocol_version}")
            print(f"Profile Version: {self._profile_version}")
            print(f"Data Size: {self._data_size}")
            print(f"Data Type: {self._data_type}")
            print(f"CRC: {self._crc}")
            print(f"=====================================")

    def _process_record(self):
        if _VERBOSE:
            print()

        record_header = self._fit_file.read(1)[0]

        normal_header = _get_bit(record_header, 7)
        message_type = _get_bit(record_header, 6)
        message_type_specific = _get_bit(record_header, 5)
        local_message_num = record_header & 0xF

        if normal_header == 0:
            if _VERBOSE:
                print(f"Header Type: Normal Header")
        else:
            if _VERBOSE:
                print(f"Header Type: Compressed Timestamp Header")
            # TODO: Support this
            raise "Encountered a compressed timestamp header!"

        if message_type == 0:
            self._process_data_message(local_message_num)
        else:
            self._process_definition_message(local_message_num, message_type_specific)

    def _process_data_message(self, local_message_num):
        if _VERBOSE:
            print(f"Message Type: Data Message")
            print(f"Local Message Num: {local_message_num}")

        data_definition = self._data_definitions[local_message_num]
        endian_modifier = data_definition["endian_modifier"]
        message_type = _GLOBAL_MESSAGE_NAMES[data_definition["global_message_num"]]

        if _PRINT_DATA:
            print(
                f'Message Type: {_GLOBAL_MESSAGE_NAMES[data_definition["global_message_num"]]}'
            )

        fields = {}

        for i, field in enumerate(data_definition["fields"]):
            value = self._fit_file.read(field["field_size"])

            if field["is_developer_data"]:
                continue  # TODO: Support dev fields

            field_size = field["field_size"]
            base_size = field["base_size"]
            unpack_string = field["unpack_string"]

            try:
                if field_size > base_size:
                    # It's an array
                    array_length = int(field_size / base_size)
                    unpack_string = f"{endian_modifier}{array_length}{unpack_string}"
                else:
                    unpack_string = f"{endian_modifier}{unpack_string}"

                unpacked = struct.unpack(unpack_string, value)

                if _VERBOSE or _PRINT_DATA_FIELDS:
                    print(f'field[{i}/{field["field_definition_number"]}] = {unpacked}')

                if message_type == "RECORD":
                    fields[
                        _FIT_RECORD_FIELDS[field["field_definition_number"]]
                    ] = unpacked

                if message_type == "SESSION":
                    if _FIT_SESSION_FIELDS[field["field_definition_number"]] == "SPORT":
                        self._sport_type = _SPORT_TYPES[unpacked[0]]

            except Exception as e:
                if _PRINT_DATA:
                    print(
                        f"Failed to unpack value={value} as {field['field_definition_number']} : {field['base_type_name']} "
                        f"with '{unpack_string}'. "
                        f"Size={field_size}. Error: {e}"
                    )
        if message_type == "RECORD":
            self._process_record_message(fields)

    def _process_record_message(self, fields):
        # Hooray for overloading the term 'record'
        if _PRINT_RECORD:
            print(f"RECORD: {fields}")

        try:
            timestamp = fields["TIMESTAMP"][0]
            position_lat = fields["POSITION_LAT"][0]
            position_lon = fields["POSITION_LON"][0]

            time = datetime(1989, 12, 31)
            time += timedelta(seconds=timestamp)

            lat = position_lat * (180 / pow(2, 31))
            lon = position_lon * (180 / pow(2, 31))

            self._records.append((time, lat, lon))
        except KeyError as e:
            if _PRINT_RECORD or _VERBOSE:
                print(f"Skipping record due to missing {e}")

    def _process_field_definition(self, local_message_num, is_developer_data=False):
        field = self._fit_file.read(3)

        field_definition_number, field_size, base_type = struct.unpack("BBB", field)

        base_type_number = 0x0F & base_type

        base_type = _DATA_TYPES[base_type_number]
        base_type_name = base_type["name"]
        unpack_string = base_type["string"]
        base_size = base_type["size"]

        if _VERBOSE or _PRINT_DEFINITIONS:
            print(f"Field[-]: ", end="")
            print(f"Field Definition Number: {field_definition_number}, ", end="")
            print(f"Field Size: {field_size}, ", end="")
            print(f"Base Type: {base_type_name} ({base_type_number})", end="")
            print()

        self._data_definitions[local_message_num]["fields"].append(
            {
                "field_definition_number": field_definition_number,
                "field_size": field_size,
                "base_type": base_type_number,
                "base_type_name": base_type_name,
                "unpack_string": unpack_string,
                "base_size": base_size,
                "is_developer_data": is_developer_data,
            }
        )

    def _process_definition_message(self, local_message_num, message_type_specific):
        if _VERBOSE or _PRINT_DEFINITIONS:
            print()
            print(f"Message Type: Definition Message")
            print(f"Local Message Num: {local_message_num}")
            print(f'Developer Data: {"Yes" if message_type_specific == 1 else "No"}')

        # This is a definition message
        record = self._fit_file.read(2)
        _, arch = struct.unpack("bb", record)

        if arch == 0:
            endian_modifier = "<"
            if _VERBOSE:
                print(f"Endianness: Little")
        else:
            endian_modifier = ">"
            if _VERBOSE:
                print(f"Endianness: Big")

        record = self._fit_file.read(3)
        global_message_num, num_fields = struct.unpack(f"{endian_modifier}hb", record)

        if _VERBOSE or _PRINT_DEFINITIONS:
            print(
                f"Global Message: {_GLOBAL_MESSAGE_NAMES[global_message_num]} ({global_message_num})"
            )
            print(f"Number of Fields: {num_fields}")

        self._data_definitions[local_message_num] = {
            "global_message_num": global_message_num,
            "num_fields": num_fields,
            "endian_modifier": endian_modifier,
            "fields": [],
        }

        for i in range(0, num_fields):
            self._process_field_definition(local_message_num)

        # TODO: Untested but present to prevent Dev Fields biting us
        if message_type_specific == 1:
            dev_fields = self._fit_file.read(1)[0]
            if _VERBOSE or _PRINT_DEFINITIONS:
                print(f"Dev Fields: {dev_fields}")

            self._data_definitions[local_message_num]["num_fields"] += dev_fields

            for i in range(0, dev_fields):
                self._process_field_definition(local_message_num, True)

    def reset(self):
        self._data_definitions = {}
        self._records = []

    @property
    def sport_type(self):
        return self._sport_type


if __name__ == "__main__":
    processor = FitFileReader()

    records = processor.process_fit_file("./_Mild_.fit")
    print(len(records))
    print(records[0])
    print(processor.sport_type)

    # records = processor.process_fit_file("all_data/export_14668556/activities/1157017534.fit.gz")
    # print(len(records))

    # processor.process_fit_file("./Activity.fit")
    # print(len(processor.records))
