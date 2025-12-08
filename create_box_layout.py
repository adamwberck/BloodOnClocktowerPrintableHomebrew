import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
DPI = 150  # Dots Per Inch
PAPER_WIDTH_INCHES = 25
PAPER_HEIGHT_INCHES = 25
MARGIN_INCHES = 0.5
OUTPUT_DIR = 'box_print_sheets'

# --- Calculations (inches to pixels) ---
PAPER_WIDTH_PX = int(PAPER_WIDTH_INCHES * DPI)
PAPER_HEIGHT_PX = int(PAPER_HEIGHT_INCHES * DPI)
MARGIN_PX = int(MARGIN_INCHES * DPI)

PRINTABLE_WIDTH_PX = PAPER_WIDTH_PX - 2 * MARGIN_PX
PRINTABLE_HEIGHT_PX = PAPER_HEIGHT_PX - 2 * MARGIN_PX


def create_new_sheet():
    """Creates a new blank letter-sized sheet with a white background."""
    return Image.new('RGBA', (PAPER_WIDTH_PX, PAPER_HEIGHT_PX), 'white')



def create_box_layout_sheet(filename, box_w, box_d, box_h, is_lid=False):
    """Generates a printable sheet for one part of the box (tray or lid)."""
    sheet = create_new_sheet()
    draw = ImageDraw.Draw(sheet)

    # Dimensions in pixels
    w_px, d_px, h_px = int(box_w * DPI), int(box_d * DPI), int(box_h * DPI)
    tab_offset = int(0.5 * DPI)


    name_lid = (0, 0, w_px, h_px) # lid with the name on it 
    
    bottom_side = ( 0, h_px, w_px, h_px + d_px) # this will be under the name lid
    bottom_side_layer_2 = (0, h_px + d_px, w_px, h_px + d_px + d_px) # this will be under bottom side
    attatch_tab_bottom = [
        (0, h_px + d_px + d_px),
        (0, h_px + d_px + d_px + tab_offset//2),
        (tab_offset//2, h_px + d_px + d_px + tab_offset),
        (w_px - tab_offset//2, h_px + d_px + d_px + tab_offset),
        (w_px, h_px + d_px + d_px + tab_offset//2),
        (w_px, h_px + d_px + d_px)
    ] # this will be bellow bottom

    top_side = (0, 0, w_px, -d_px) # this will be above the name lid
    top_side_layer_2 = (0, -d_px, w_px, -d_px - d_px) # this will be above top side

    attatch_tab_top = [
        (0, -d_px - d_px),
        (0, -d_px - d_px - tab_offset//2),
        (tab_offset//2, -d_px - d_px - tab_offset),
        (w_px - tab_offset//2, -d_px - d_px - tab_offset),
        (w_px, -d_px - d_px - tab_offset//2),
        (w_px, -d_px - d_px)
    ]

    left_side = (0, 0, -d_px, h_px)
    left_side_layer_2 = (-d_px, 0, -d_px - d_px, h_px)
    attatch_tab_left = [
        (-d_px - d_px, 0),
        (-d_px - d_px - tab_offset//2, 0),
        (-d_px - d_px - tab_offset, tab_offset//2),
        (-d_px - d_px - tab_offset, h_px - tab_offset//2),
        (-d_px - d_px - tab_offset//2, h_px),
        (-d_px - d_px, h_px)
    ]

    right_side = (w_px, 0, w_px + d_px, h_px)
    right_side_layer_2 = (w_px + d_px, 0, w_px + d_px + d_px, h_px)
    attatch_tab_right = [
        (w_px + d_px + d_px, 0),
        (w_px + d_px + d_px + tab_offset//2, 0),
        (w_px + d_px + d_px + tab_offset, tab_offset//2),
        (w_px + d_px + d_px + tab_offset, h_px - tab_offset//2),
        (w_px + d_px + d_px + tab_offset//2, h_px),
        (w_px + d_px + d_px, h_px)
    ]
    def _add_constant_to_coords(coords, constant_x, constant_y):
        """Adds a constant value to the x and y components of each coordinate pair."""
        if type(coords) == tuple:
            x, y, x2, y2 = coords
            x, y, x2, y2 = x + constant_x, y + constant_y, x2 + constant_x, y2 + constant_y
            if x > x2:
                x, x2 = x2, x
            if y > y2:
                y, y2 = y2, y
            return [(x, y), (x2, y2)]
        print(f'coords: {coords}')
        return [(x + constant_x, y + constant_y) for x, y in coords]
    START_X = PAPER_WIDTH_PX//2 - w_px//2
    START_Y = PAPER_HEIGHT_PX//2 - h_px//2

    draw.rectangle(_add_constant_to_coords(name_lid, START_X, START_Y), outline="black")

    draw.rectangle(_add_constant_to_coords(bottom_side, START_X, START_Y), outline="black")
    draw.rectangle(_add_constant_to_coords(bottom_side_layer_2, START_X, START_Y), outline="black")
    draw.polygon(_add_constant_to_coords(attatch_tab_bottom, START_X, START_Y), outline="black")

    draw.rectangle(_add_constant_to_coords(top_side, START_X, START_Y), outline="black")
    draw.rectangle(_add_constant_to_coords(top_side_layer_2, START_X, START_Y), outline="black")
    draw.polygon(_add_constant_to_coords(attatch_tab_top, START_X, START_Y), outline="black")

    draw.rectangle(_add_constant_to_coords(left_side, START_X, START_Y), outline="black")
    draw.rectangle(_add_constant_to_coords(left_side_layer_2, START_X, START_Y), outline="black")
    draw.polygon(_add_constant_to_coords(attatch_tab_left, START_X, START_Y), outline="black")

    draw.rectangle(_add_constant_to_coords(right_side, START_X, START_Y), outline="black")
    draw.rectangle(_add_constant_to_coords(right_side_layer_2, START_X, START_Y), outline="black")
    draw.polygon(_add_constant_to_coords(attatch_tab_right, START_X, START_Y), outline="black")
    return sheet







    



def main():
    """
    Generates a two-page print layout for a foldable box.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("--- Generating Printable Box Layout ---")
    print("Black lines are for cutting, gray lines are for folding.")

    # --- Define Box Dimensions ---
    LID_WIDTH = 11.0
    LID_HEIGHT = 2.375
    LID_DEPTH = 1.5

    # Tray is slightly smaller
    TRAY_WIDTH = LID_WIDTH - 0.125
    TRAY_DEPTH = LID_DEPTH - 0.125
    TRAY_HEIGHT = 1.5

    # --- Generate Sheets ---
    # create_box_layout_sheet("box_tray_layout.png", TRAY_WIDTH, TRAY_DEPTH, TRAY_HEIGHT)
    layout_sheet = create_box_layout_sheet("box_lid_layout.png", LID_WIDTH, LID_DEPTH, LID_HEIGHT, is_lid=True)
    output_filename = os.path.join(OUTPUT_DIR, 'box_layout.png')
    layout_sheet.save(output_filename)

    print(f"\nBox layout generation complete. Sheets are in the '{OUTPUT_DIR}' directory.")


if __name__ == '__main__':
    main()