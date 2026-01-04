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