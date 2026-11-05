"""Command registry for Pixoo device functions.

Drawing methods modify a buffer that requires push() to display.
Device control methods take immediate action on the device and are gated behind API key verification.
"""

DRAWING_COMMANDS = [
	"clear",
	"clear_rgb",
	"draw_character",
	"draw_character_at_location_rgb",
	"draw_filled_rectangle",
	"draw_filled_rectangle_from_top_left_to_bottom_right_rgb",
	"draw_image",
	"draw_image_at_location",
	"draw_line",
	"draw_line_from_start_to_stop_rgb",
	"draw_pixel",
	"draw_pixel_at_index",
	"draw_pixel_at_index_rgb",
	"draw_pixel_at_location_rgb",
	"draw_text",
	"draw_text_at_location_rgb",
	"fill",
	"fill_rgb",
	"push",
]

DEVICE_CONTROL_COMMANDS = [
	"find_local_device_ip",
	"get_all_device_configurations",
	"get_device_time",
	"play_local_gif",
	"play_local_gif_directory",
	"play_net_gif",
	"sound_buzzer",
	"reboot",
	"send_text",
	"send_text_at_location_rgb",
	"set_brightness",
	"set_channel",
	"set_clock",
	"set_face",
	"set_high_light_mode",
	"set_mirror_mode",
	"set_noise_status",
	"set_score_board",
	"set_screen",
	"set_screen_off",
	"set_screen_on",
	"set_visualizer",
	"set_white_balance",
	"set_white_balance_rgb",
	"validate_connection",
]

ADMIN_COMMANDS = DEVICE_CONTROL_COMMANDS
