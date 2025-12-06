import os
from PIL import Image

# --- Configuration ---
DPI = 600  # Dots Per Inch
PAPER_WIDTH_INCHES = 11
PAPER_HEIGHT_INCHES = 8.5
MARGIN_INCHES = 0.7

CHARACTER_TOKEN_DIAMETER_INCHES = 1.75
REMINDER_TOKEN_DIAMETER_INCHES = 1

CHARACTER_TOKEN_DIR = 'character_tokens'
REMINDER_TOKEN_DIR = 'reminder_tokens'
OUTPUT_DIR = 'print_sheets'

# --- Calculations (inches to pixels) ---
PAPER_WIDTH_PX = int(PAPER_WIDTH_INCHES * DPI)
PAPER_HEIGHT_PX = int(PAPER_HEIGHT_INCHES * DPI)
MARGIN_PX = int(MARGIN_INCHES * DPI)

PRINTABLE_WIDTH_PX = PAPER_WIDTH_PX - 2 * MARGIN_PX
PRINTABLE_HEIGHT_PX = PAPER_HEIGHT_PX - 2 * MARGIN_PX

CHAR_TOKEN_SIZE_PX = int(CHARACTER_TOKEN_DIAMETER_INCHES * DPI)
REMINDER_TOKEN_SIZE_PX = int(REMINDER_TOKEN_DIAMETER_INCHES * DPI)


def collect_image_paths(directory):
    """Recursively collects all .png image paths from a directory, skipping 'fabled' and 'loric'."""
    image_paths = []
    if not os.path.isdir(directory):
        print(f"Warning: Directory not found: {directory}")
        return []
    for root, dirs, files in os.walk(directory):
        # Exclude 'fabled' and 'loric' directories from the walk
        dirs[:] = [d for d in dirs if d.lower() not in ['fabled', 'loric']]
        for file in sorted(files): # Sort files for consistent order
            if file.lower().endswith('.png'):
                image_paths.append(os.path.join(root, file))
    return image_paths


def create_new_sheet():
    """Creates a new blank letter-sized sheet with a white background."""
    return Image.new('RGBA', (PAPER_WIDTH_PX, PAPER_HEIGHT_PX), 'white')


def main():
    """
    Generates print sheets for character and reminder tokens.
    """
    # --- 1. Setup ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- 2. Collect all token images ---
    char_paths = collect_image_paths(CHARACTER_TOKEN_DIR)
    reminder_paths = collect_image_paths(REMINDER_TOKEN_DIR)

    tokens_to_print = []
    for path in char_paths:
        tokens_to_print.append({'path': path, 'size': CHAR_TOKEN_SIZE_PX})
    for path in reminder_paths:
        tokens_to_print.append({'path': path, 'size': REMINDER_TOKEN_SIZE_PX})

    if not tokens_to_print:
        print("No token images found. Please run create_tokens.py first.")
        return

    print(f"Found {len(char_paths)} character tokens and {len(reminder_paths)} reminder tokens.")

    # --- 3. Arrange tokens on sheets ---
    sheet_num = 1
    current_sheet = create_new_sheet()
    x_pos = MARGIN_PX
    y_pos = MARGIN_PX
    row_height = 0
    sheet_has_content = False

    for token_info in tokens_to_print:
        path = token_info['path']
        size = token_info['size']

        if x_pos + size > MARGIN_PX + PRINTABLE_WIDTH_PX:
            x_pos = MARGIN_PX
            y_pos += row_height
            row_height = 0

        if y_pos + size > MARGIN_PX + PRINTABLE_HEIGHT_PX:
            output_filename = os.path.join(OUTPUT_DIR, f'print_sheet_{sheet_num}.png')
            current_sheet.save(output_filename)
            print(f"Saved {output_filename}")

            sheet_num += 1
            current_sheet = create_new_sheet()
            x_pos, y_pos, row_height, sheet_has_content = MARGIN_PX, MARGIN_PX, 0, False

        try:
            with Image.open(path) as token_img:
                resized_img = token_img.resize((size, size), Image.Resampling.LANCZOS)
                current_sheet.paste(resized_img, (x_pos, y_pos), resized_img)
                sheet_has_content = True
        except Exception as e:
            print(f"Error processing image {path}: {e}")
            continue

        x_pos += size
        row_height = max(row_height, size)

    if sheet_has_content:
        output_filename = os.path.join(OUTPUT_DIR, f'print_sheet_{sheet_num}.png')
        current_sheet.save(output_filename)
        print(f"Saved {output_filename}")

    print(f"\nPrint sheet generation complete. Sheets are in the '{OUTPUT_DIR}' directory.")


if __name__ == '__main__':
    main()
