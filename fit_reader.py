import struct

VERBOSE = False

PRINT_DATA = True
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
        try:
            (unpacked,) = struct.unpack(
                f'{data_definition["endian_modifier"]}{field["unpack_string"]}', value
            )
            if VERBOSE:
                print(f'field[{i}/{field["field_definition_number"]}] = {unpacked}')
        except:
            if PRINT_DATA:
                print(
                    f"Failed to unpack value: {value} as {field['base_type_name']} with {field['unpack_string']}. Size={field['field_size']}"
                )


def process_field_definition(fit_file, local_message_num):
    field = fit_file.read(3)

    field_definition_number, field_size, base_type = struct.unpack("BBB", field)

    base_type_number = 0x0F & base_type

    data_types = {
        0: {"name": "enum", "string": "b"},
        1: {"name": "sint8", "string": "b"},
        2: {"name": "uint8", "string": "B"},
        3: {"name": "sint16", "string": "h"},
        4: {"name": "uint16", "string": "H"},
        5: {"name": "sint32", "string": "i"},
        6: {"name": "uint32", "string": "I"},
        7: {"name": "string", "string": f"{field_size}s"},
        8: {"name": "float32", "string": "f"},
        9: {"name": "float64", "string": "d"},
        10: {"name": "uint8z", "string": "B"},
        11: {"name": "uint16z", "string": "H"},
        12: {"name": "uint32z", "string": "I"},
        13: {"name": "byte", "string": "b"},
        14: {"name": "sint64", "string": "q"},
        15: {"name": "uint64", "string": "Q"},
        16: {"name": "unit64z", "string": "Q"},
    }

    base_type_name = data_types[base_type_number]["name"]
    unpack_string = data_types[base_type_number]["string"]

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
            process_field_definition(fit_file, local_message_num)


with open(FILE_NAME, "rb") as fit_file:

    print(f"Processing: {FILE_NAME}")

    data_size = process_file_header(fit_file)

    while fit_file.tell() < data_size:
        if VERBOSE:
            print()

        process_record(fit_file)
