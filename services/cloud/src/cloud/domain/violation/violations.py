# Class names of the exp02 YOLO model (weights/ppe). Read from model.names at runtime; these are the
# names the rest of the code relies on.
VIOLATION_CLASSES: tuple[str, ...] = ("no_helmet", "no_vest", "no_gloves", "no_safety_boots")
PERSON_CLASS = "person"

ZONE_INTRUSION = "zone_intrusion"  # someone walked into a forbidden zone (reported by the edge, not a class of the model)
EVENT_TYPES: tuple[str, ...] = (*VIOLATION_CLASSES, ZONE_INTRUSION)  # what an event may be
