from numpy import array

FIELD_RED_FLAG = (50.0, -24.0)
FIELD_BLUE_FLAG = (-58.0, -71.0)

FIELD_UPPER_LEFT_CORNER = (-83,-49)
FIELD_UPPER_RIGHT_CORNER = (56, 16)
FIELD_LOWER_LEFT_CORNER = (-53, -114)
FIELD_LOWER_RIGHT_CORNER = (82, -56)

FIELD_UL_NUMPY = array(FIELD_UPPER_LEFT_CORNER)
FIELD_UR_NUMPY = array(FIELD_UPPER_RIGHT_CORNER)
FIELD_LL_NUMPY = array(FIELD_LOWER_LEFT_CORNER)
FIELD_LR_NUMPY = array(FIELD_LOWER_RIGHT_CORNER)

FIELD_CORNERS = (
  FIELD_UPPER_RIGHT_CORNER,
  FIELD_UPPER_LEFT_CORNER,
  FIELD_LOWER_LEFT_CORNER,
  FIELD_LOWER_RIGHT_CORNER
)