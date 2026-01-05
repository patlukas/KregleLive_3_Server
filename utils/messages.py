def extract_lane_id_from_incoming_message(msg: bytes, lane_count: int):
    """
    Extract lane id from incoming message.

    Returns:
        lane id (0..lane_count-1) or None if invalid.
    """
    if len(msg) < 4:
        return None
    lane = int(msg[3:4])
    if lane >= lane_count:
        return None
    return lane

def calculate_message_control_sum(message):
    """

    """
    sum_ascii = 0
    for x in message:
        sum_ascii += x
    checksum = bytes(hex(sum_ascii).split("x")[-1].upper()[-2:], 'utf-8')
    return checksum

def encapsulate_message(prepared_message, priority=5, time_wait=-1):
    """

    """
    return {"message": prepared_message, "time_wait": time_wait, "priority": priority}

def prepare_message_to_lane_and_encapsulate(lane_id, content, priority=5, time_wait=-1):
    """

    """
    message = prepare_message_to_lane(lane_id, content)
    return encapsulate_message(message, priority, time_wait)

def prepare_message_to_lane(lane_id, content):
    message = b"3" + bytes(str(lane_id), "cp1250") + b"38" + content
    message_with_control_sum = message + calculate_message_control_sum(message) + b"\r"
    return message_with_control_sum
