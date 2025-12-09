import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
DPI = 100  # Dots Per Inch


DEBUG_PAPER_WIDTH_INCHES = 25
DEBUG_PAPER_HEIGHT_INCHES = 25

OUTPUT_DIR = 'box_print_sheets'

# --- Calculations (inches to pixels) ---
DEBUG_PAPER_WIDTH_PX = int(DEBUG_PAPER_WIDTH_INCHES * DPI)
DEBUG_PAPER_HEIGHT_PX = int(DEBUG_PAPER_HEIGHT_INCHES * DPI)


PRINT_WIDTH_INCHES = 8.5
PRINT_HEIGHT_INCHES = 11
# --- Calculations (inches to pixels) ---
PAPER_WIDTH_PX = int(PRINT_WIDTH_INCHES * DPI)
PAPER_HEIGHT_PX = int(PRINT_HEIGHT_INCHES * DPI)
MARGIN_INCHES = 0.7
MARGIN_PX = int(MARGIN_INCHES * DPI)
PRINTABLE_WIDTH_PX = PAPER_WIDTH_PX - 2 * MARGIN_PX
PRINTABLE_HEIGHT_PX =PAPER_HEIGHT_PX - 2 * MARGIN_PX


def create_new_sheet(PW=DEBUG_PAPER_WIDTH_PX, PH=DEBUG_PAPER_HEIGHT_PX):
    """Creates a new blank letter-sized sheet with a white background."""
    return Image.new('RGBA', (PW, PH), 'white')


def _add_constant_to_cords(cords, constant_x, constant_y):
    """Adds a constant value to the x and y components of each coordinate pair."""
    if type(cords) == tuple:
        x, y, x2, y2 = cords
        x, y, x2, y2 = x + constant_x, y + constant_y, x2 + constant_x, y2 + constant_y
        if x > x2:
            x, x2 = x2, x
        if y > y2:
            y, y2 = y2, y
        return x, y, x2, y2
    return [(x + constant_x, y + constant_y) for x, y in cords]


def reflect_cords(cords, xaxis=False, yaxis=True):
    """Reflects coordinates across the x or y axis."""
    reflected = []
    for x, y in cords:
        if xaxis:
            y = -y
        if yaxis:
            x = -x
        reflected.append((x, y))
    return reflected




def create_box_layout_shapes(box_w, box_d, box_h):
    """Generates a printable sheet for one part of the box (tray or lid)."""
    sheet = create_new_sheet()
    draw = ImageDraw.Draw(sheet)

    # Dimensions in pixels
    w_px, d_px, h_px = int(box_w * DPI), int(box_d * DPI), int(box_h * DPI)
    tab_offset = h_px // 4


    name_lid = (0, 0, w_px, h_px) # lid with the name on it 

    left_right_shape = (0, 0, d_px, h_px)
    right_side = _add_constant_to_cords(left_right_shape, w_px, 0)
    right_side_layer_2 = _add_constant_to_cords(left_right_shape, w_px + d_px, 0)
    attatch_tab_right_shape = [
        (0, 0),
        (0 + tab_offset, tab_offset),
        (0 + tab_offset, h_px - tab_offset),
        (0, h_px)
    ]
    attatch_tab_right = _add_constant_to_cords(attatch_tab_right_shape, w_px + d_px + d_px, 0)

    left_side = _add_constant_to_cords(left_right_shape, -d_px, 0)
    left_side_layer_2 = _add_constant_to_cords(left_right_shape, -d_px - d_px, 0)
    attatch_tab_left = [
        (-d_px - d_px, 0),
        (-d_px - d_px - tab_offset, tab_offset),
        (-d_px - d_px - tab_offset, h_px - tab_offset),
        (-d_px - d_px, h_px)
    ]

    
    bottom_side = ( 0, h_px, w_px, h_px + d_px) # this will be under the name lid    
    bottom_side_layer_2 = _add_constant_to_cords(bottom_side, 0, d_px) # this will be under bottom side
    attatch_tab_bottom = _add_constant_to_cords([
        (0, 0),
        (tab_offset, tab_offset),
        (w_px - tab_offset, tab_offset),
        (w_px, 0)
    ], 0, h_px + d_px + d_px)# this will be bellow bottom
    insert_tab_offset = d_px * 0.15
    insert_tab_extension = h_px * 0.25
    attatch_tab_bottom_right = _add_constant_to_cords([
        (0, 0),
        (0 + insert_tab_offset, insert_tab_offset),
        (0 + insert_tab_offset + insert_tab_extension, insert_tab_offset),
        (0 + insert_tab_offset + insert_tab_extension, insert_tab_offset),
        (0 + insert_tab_offset + insert_tab_extension, d_px - insert_tab_offset),
        (0 + insert_tab_offset, d_px - insert_tab_offset),
        (0, d_px)
    ], w_px, h_px + d_px)
    top_side = _add_constant_to_cords(bottom_side, 0, -d_px - h_px) # above name
    
    top_side_layer_2 =_add_constant_to_cords(
        bottom_side, 0, -h_px - d_px - d_px) # this will be above top side
    attatch_tab_top = [
        (0, -d_px - d_px),
        (tab_offset, -d_px - d_px - tab_offset),
        (w_px - tab_offset, -d_px - d_px - tab_offset),
        (w_px, -d_px - d_px)
    ]
    attatch_tab_top_right = _add_constant_to_cords(attatch_tab_bottom_right, 0, -h_px - d_px - d_px - d_px)

    attatch_tab_bottom_left = _add_constant_to_cords(reflect_cords(attatch_tab_bottom_right), w_px, 0)
    attatch_tab_top_left = _add_constant_to_cords(reflect_cords(attatch_tab_top_right), w_px, 0)

    START_X = DEBUG_PAPER_WIDTH_PX//2 - w_px//2
    START_Y = DEBUG_PAPER_HEIGHT_PX//2 - h_px//2

    list_of_shapes = [
        {'name': 'name_lid', 'cords': name_lid},
        {'name': 'bottom_side', 'cords': bottom_side},
        {'name': 'bottom_side_layer_2', 'cords': bottom_side_layer_2},
        {'name': 'attatch_tab_bottom', 'cords': attatch_tab_bottom},
        {'name': 'top_side', 'cords': top_side},
        {'name': 'top_side_layer_2', 'cords': top_side_layer_2},
        {'name': 'attatch_tab_top', 'cords': attatch_tab_top},
        {'name': 'left_side', 'cords': left_side},
        {'name': 'left_side_layer_2', 'cords': left_side_layer_2},
        {'name': 'attatch_tab_left', 'cords': attatch_tab_left},
        {'name': 'right_side', 'cords': right_side},
        {'name': 'right_side_layer_2', 'cords': right_side_layer_2},
        {'name': 'attatch_tab_right', 'cords': attatch_tab_right},
        {'name': 'attatch_tab_bottom_right', 'cords': attatch_tab_bottom_right},
        {'name': 'attatch_tab_top_right', 'cords': attatch_tab_top_right},
        {'name': 'attatch_tab_bottom_left', 'cords': attatch_tab_bottom_left},
        {'name': 'attatch_tab_top_left', 'cords': attatch_tab_top_left},
    ]
    for shape_data in list_of_shapes:
        print(f'{shape_data["name"]}: {shape_data["cords"]}')
        shape = shape_data["cords"]
        if type(shape) == tuple:
            draw.rectangle(_add_constant_to_cords(shape, START_X, START_Y), outline="black")
        else:
            draw.polygon(_add_constant_to_cords(shape, START_X, START_Y), outline="black")

    return sheet, list_of_shapes


def shapes_split_into_sheets(list_of_shapes):
    sheet_grid = {}
    for shape_data in list_of_shapes:
        name = shape_data["name"]
        shape = shape_data["cords"]
        def find_sheet(shape):
            if type(shape) == tuple:
                print(f'hello name: {name} cords: {shape}')
                x1, y1, x2, y2 = shape
                sheet_x1 = x1//PRINTABLE_WIDTH_PX
                sheet_x2 = x2//PRINTABLE_WIDTH_PX
                sheet_y1 = y1//PRINTABLE_HEIGHT_PX
                sheet_y2 = y2//PRINTABLE_HEIGHT_PX
                print(f'name: {name} cords: {shape} sheet: {list(set([(sheet_x1, sheet_y1), (sheet_x2, sheet_y2)]))}')
                return list(set([(sheet_x1, sheet_y1), (sheet_x2, sheet_y2)]))
            sheet_x = 0
            sheet_y = 0
            out_put = []
            for x, y in shape:
                sheet_x = x//PRINTABLE_WIDTH_PX
                sheet_y = y//PRINTABLE_HEIGHT_PX
                out_put.append((sheet_x, sheet_y))
            
            print(f'name: {name} cords: {shape} sheet: {list(set(out_put))}')
            return list(set(out_put))
        
        all_sheets = find_sheet(shape)
        for sheet_x, sheet_y in all_sheets:
            if (sheet_x, sheet_y) not in sheet_grid:
                sheet_grid[(sheet_x, sheet_y)] = [shape_data]
            else:
                sheet_grid[(sheet_x, sheet_y)].append(shape_data)
    return sheet_grid


def main():
    """
    Generates a two-page print layout for a foldable box.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("--- Generating Printable Box Layout ---")
    print("Black lines are for cutting, gray lines are for folding.")

    # --- Define Box Dimensions ---
    LID_WIDTH = 8
    LID_HEIGHT = 2.375
    LID_DEPTH = 1.5

    # Tray is slightly smaller
    TRAY_WIDTH = LID_WIDTH - 0.125
    TRAY_DEPTH = LID_DEPTH - 0.125
    TRAY_HEIGHT = 1.5

    # --- Generate Sheets ---
    # create_box_layout_sheet("box_tray_layout.png", TRAY_WIDTH, TRAY_DEPTH, TRAY_HEIGHT)
    debug_layout_sheet, list_of_shapes = create_box_layout_shapes(LID_WIDTH, LID_DEPTH, LID_HEIGHT)
    output_filename = os.path.join(OUTPUT_DIR, 'box_layout_debug.png')
    debug_layout_sheet.save(output_filename)
    split_to_multiple_sheets_save(list_of_shapes)


def find_lowest_cord(shapes):
    lowest_cord_x = float('inf')
    lowest_cord_y = float('inf')
    for shape in shapes:
        if type(shape) == tuple:
            x, y, x2, y2 = shape
            lowest_cord_x = min(lowest_cord_x, x, x2)
            lowest_cord_y = min(lowest_cord_y, y, y2)
        else:
            for x, y in shape:
                lowest_cord_x = min(lowest_cord_x, x)
                lowest_cord_y = min(lowest_cord_y, y)
    return lowest_cord_x, lowest_cord_y


def draw_shape(sheet, draw, shape, margin=MARGIN_PX):
    # print(f'shape: {shape}')
    # print(f'sheet size: {sheet.size}')
    # print(f'margin: {margin}')
    # print(f'sheet max x: {sheet.width-margin}')
    # print(f'sheet max y: {sheet.height-margin}')

    if type(shape) == tuple:
        x, y, x2, y2 = shape
        # x = min(x, sheet.width - margin)
        # y = min(y, sheet.height - margin)
        # x2 = max(x2, sheet.width - margin)
        # y2 = max(y2, sheet.height - margin)
        draw.rectangle((x, y, x2, y2), outline="black")
    else:
        draw_poly = []
        for x, y in shape:
            # x = min(x, sheet.width - margin)
            # y = min(y, sheet.height - margin)
            draw_poly.append((x, y))
        draw.polygon(draw_poly, outline="black")


def split_to_multiple_sheets_save(list_of_shapes):
    lowest_cord_x, lowest_cord_y = find_lowest_cord(shape_data["cords"] for shape_data in list_of_shapes)
    list_of_shapes = [{"name": shape_data["name"],
                       "cords": _add_constant_to_cords(shape_data["cords"], -lowest_cord_x, -lowest_cord_y)}
                       for shape_data in list_of_shapes]
    all_sheets = shapes_split_into_sheets(list_of_shapes)
    for i, sheet_data_key in enumerate(all_sheets):
        sheet_data = all_sheets[sheet_data_key]
        sheet = create_new_sheet(PAPER_WIDTH_PX, PAPER_HEIGHT_PX)
        draw = ImageDraw.Draw(sheet)
        low_x, low_y = find_lowest_cord(shape["cords"] for shape in sheet_data)
        for shape in sheet_data:
            print(f'{shape["name"]}: {shape["cords"]}')
            cords = shape["cords"]
            # move shape to top left
            cords = _add_constant_to_cords(cords, -low_x, -low_y)
            draw_shape(sheet, draw, _add_constant_to_cords(cords, MARGIN_PX, MARGIN_PX))
        sheet.save(os.path.join(OUTPUT_DIR, f'box_layout_{sheet_data_key}.png'))







    print(f"\nBox layout generation complete. Sheets are in the '{OUTPUT_DIR}' directory.")


if __name__ == '__main__':
    main()