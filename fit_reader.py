import struct

VERBOSE = False

PRINT_DATA = True
PRINT_DATA_FIELDS = False
PRINT_RECORD = True  # Print the fields if the data is of RECORD type
PRINT_DEFINITIONS = False

FILE_NAME = "./_Mild_.fit"
# FILE_NAME='./Activity.fit'


def get_bit(value, bit_index):
    return (value & (1 << bit_index)) >> bit_index


data_definitions = {}

global_message_names = {
    0: "FILE_ID",
    2: "DEVICE_SETTINGS",
    3: "USER_PROFILE",
    7: "ZONES_TARGET",
    12: "SPORT",
    13: "UNKNOWN",
    15: "GOAL",
    18: "SESSION",
    19: "LAP",
    20: "RECORD",
    21: "EVENT",
    22: "UNKNOWN",
    23: "DEVICE_INFO",
    34: "ACTIVITY",
    49: "FILE_CREATOR",
    78: "HRV",
    79: "UNKNOWN",
    104: "UNKNOWN",
    140: "UNKNOWN",
    147: "UNKNOWN",
    206: "FIELD_DESCRIPTION",
    207: "DEVELOPER_DATA_ID",
    216: "UNKNOWN",
}

fit_record_fields = {
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
}


def process_file_header(fit_file):
    header_size = fit_file.read(1)[0]
    header = fit_file.read(header_size - 1)

    protocol_version, profile_version, data_size, data_type, crc = struct.unpack(
        "<BHI4sH", header
    )

    print(f"=====================================")
    print(f"Header Size: {header_size}")
    print(f"Protocol Version: {protocol_version}")
    print(f"Profile Version: {profile_version}")
    print(f"Data Size: {data_size}")
    print(f"Data Type: {data_type}")
    print(f"CRC: {crc}")
    print(f"=====================================")

    return data_size  # TODO: Return something structured


def process_record(fit_file):
    record_header = fit_file.read(1)[0]

    normal_header = get_bit(record_header, 7)
    message_type = get_bit(record_header, 6)
    message_type_specific = get_bit(record_header, 5)
    local_message_num = record_header & 0xF

    if VERBOSE:
        if normal_header == 0:
            print(f"Header Type: Normal Header")
        else:
            print(f"Header Type: Compressed Timestamp Header")

    if normal_header == 1:
        # TODO: Support this
        raise "Encountered a compressed timestamp header!"

    if message_type == 0:
        process_data_message(fit_file, local_message_num)
    else:
        process_definition_message(fit_file, local_message_num, message_type_specific)
        if VERBOSE:
            print(f"Position: {fit_file.tell()}")


def process_data_message(fit_file, local_message_num):
    if VERBOSE:
        print(f"Message Type: Data Message")
        print(f"Local Message Num: {local_message_num}")

    data_definition = data_definitions[local_message_num]

    if PRINT_DATA:
        print(
            f'Message Type: {global_message_names[data_definition["global_message_num"]]}'
        )
    for i, field in enumerate(data_definition["fields"]):
        value = fit_file.read(field["field_size"])

        if field["is_developer_data"]:
            continue  # TODO: Support dev fields

        try:
            if field["field_size"] > field["base_size"]:
                # It's an array
                array_length = int(field["field_size"] / field["base_size"])
                unpack_string = f'{data_definition["endian_modifier"]}{array_length}{field["unpack_string"]}'
            else:
                unpack_string = (
                    f'{data_definition["endian_modifier"]}{field["unpack_string"]}'
                )

            unpacked = struct.unpack(unpack_string, value)

            if (
                PRINT_RECORD
                and global_message_names[data_definition["global_message_num"]]
                == "RECORD"
            ):
                print(
                    f'field[{i}/{fit_record_fields[field["field_definition_number"]]}] = {unpacked}'
                )
            elif VERBOSE or PRINT_DATA_FIELDS:
                print(f'field[{i}/{field["field_definition_number"]}] = {unpacked}')

        except Exception as e:
            if PRINT_DATA:
                print(
                    f"Failed to unpack value: {value} as {field['field_definition_number']} : {field['base_type_name']} with '{unpack_string}'. Size={field['field_size']}. Error: {e}"
                )


def process_field_definition(fit_file, local_message_num, is_developer_data=False):
    field = fit_file.read(3)

    field_definition_number, field_size, base_type = struct.unpack("BBB", field)

    base_type_number = 0x0F & base_type

    data_types = {
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

    base_type = data_types[base_type_number]
    base_type_name = base_type["name"]
    unpack_string = base_type["string"]
    base_size = base_type["size"]

    if VERBOSE or PRINT_DEFINITIONS:
        print(f"Field[-]: ", end="")
        print(f"Field Definition Number: {field_definition_number}, ", end="")
        print(f"Field Size: {field_size}, ", end="")
        print(f"Base Type: {base_type_name} ({base_type_number})", end="")
        print()

    data_definitions[local_message_num]["fields"].append(
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


def process_definition_message(fit_file, local_message_num, message_type_specific):
    if VERBOSE or PRINT_DEFINITIONS:
        print()
        print(f"Message Type: Definition Message")
        print(f"Local Message Num: {local_message_num}")
        print(f'Developer Data: {"Yes" if message_type_specific == 1 else "No"}')

    # This is a definition message
    record = fit_file.read(2)
    _, arch = struct.unpack("bb", record)

    if arch == 0:
        endian_modifier = "<"
        if VERBOSE:
            print(f"Endianness: Little")
    else:
        endian_modifier = ">"
        if VERBOSE:
            print(f"Endianness: Big")

    record = fit_file.read(3)
    global_message_num, num_fields = struct.unpack(f"{endian_modifier}hb", record)

    if VERBOSE or PRINT_DEFINITIONS:
        print(
            f"Global Message: {global_message_names[global_message_num]} ({global_message_num})"
        )
        print(f"Number of Fields: {num_fields}")

    data_definitions[local_message_num] = {
        "global_message_num": global_message_num,
        "num_fields": num_fields,
        "endian_modifier": endian_modifier,
        "fields": [],
    }

    for i in range(0, num_fields):
        process_field_definition(fit_file, local_message_num)

    # TODO: Untested but present to prevent Dev Fields biting us
    if message_type_specific == 1:
        dev_fields = fit_file.read(1)[0]
        print(f"Dev Fields: {dev_fields}")

        data_definitions[local_message_num]["num_fields"] += dev_fields

        for i in range(0, dev_fields):
            # print(f'****** Dev Field[{i}] = {field}')
            process_field_definition(fit_file, local_message_num, True)


with open(FILE_NAME, "rb") as fit_file:

    print(f"Processing: {FILE_NAME}")

    data_size = process_file_header(fit_file)

    while fit_file.tell() < data_size:
        if VERBOSE:
            print()

        process_record(fit_file)
