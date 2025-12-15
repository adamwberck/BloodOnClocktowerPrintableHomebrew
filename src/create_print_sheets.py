import os
from PIL import Image

# --- Configuration ---
DPI = 300  # Dots Per Inch
PAPER_WIDTH_INCHES = 11
PAPER_HEIGHT_INCHES = 8.5
MARGIN_INCHES = 0.75

CHARACTER_TOKEN_DIAMETER_INCHES = 1.75
REMINDER_TOKEN_DIAMETER_INCHES = 1

PADDING = 1/16
PADDING_PX = int(PADDING * DPI)

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

    character_tokens = []
    reminder_tokens = []
    for path in char_paths:
        character_tokens.append({'path': path, 'size': CHAR_TOKEN_SIZE_PX})
    for path in reminder_paths:
        reminder_tokens.append({'path': path, 'size': REMINDER_TOKEN_SIZE_PX})

    if not character_tokens and not character_tokens:
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
    pending_token = None

    while character_tokens or reminder_tokens or pending_token:
        if pending_token:
            token_info = pending_token
            pending_token = None
        else:
            # Decide which token to try placing.
            # Prioritize larger character tokens if they fit in the current row.
            # If a character token doesn't fit, see if a smaller reminder token does.
            char_fits = character_tokens and (x_pos + CHAR_TOKEN_SIZE_PX <= MARGIN_PX + PRINTABLE_WIDTH_PX)
            reminder_fits = reminder_tokens and (x_pos + REMINDER_TOKEN_SIZE_PX <= MARGIN_PX + PRINTABLE_WIDTH_PX)

            if char_fits:
                token_info = character_tokens.pop()
            elif reminder_fits:
                token_info = reminder_tokens.pop()
            elif character_tokens: # Neither fits, so we'll wrap. Prioritize char token.
                token_info = character_tokens.pop()
            elif reminder_tokens: # No chars left, take a reminder that will wrap.
                token_info = reminder_tokens.pop()
            else:
                break # No tokens left

        path = token_info['path']
        size = token_info['size']

        # If the token doesn't fit in the current row, move to the next row.
        if x_pos + size > MARGIN_PX + PRINTABLE_WIDTH_PX:
            x_pos = MARGIN_PX
            y_pos += row_height
            row_height = 0

        # If the token doesn't fit on the current page, save this one and start a new one.
        if y_pos + size > MARGIN_PX + PRINTABLE_HEIGHT_PX:
            pending_token = token_info # This token will be the first on the next sheet.

            # Before creating a new sheet, try to fill the remaining space with small reminder tokens.
            while reminder_tokens:
                if x_pos + REMINDER_TOKEN_SIZE_PX > MARGIN_PX + PRINTABLE_WIDTH_PX:
                    x_pos = MARGIN_PX
                    y_pos += row_height
                    row_height = 0

                if y_pos + REMINDER_TOKEN_SIZE_PX > MARGIN_PX + PRINTABLE_HEIGHT_PX:
                    break # No more space on this sheet, even for small tokens.

                # A reminder fits, so place it.
                r_token = reminder_tokens.pop()
                try:
                    with Image.open(r_token['path']) as token_img:
                        cropped_token = token_img.crop(token_img.getbbox())
                        resized_img = cropped_token.resize((REMINDER_TOKEN_SIZE_PX, REMINDER_TOKEN_SIZE_PX), Image.Resampling.LANCZOS)
                        current_sheet.paste(resized_img, (x_pos, y_pos), resized_img)
                        sheet_has_content = True
                except Exception as e:
                    print(f"Error processing image {r_token['path']}: {e}")
                    continue
                x_pos += REMINDER_TOKEN_SIZE_PX + PADDING_PX
                row_height = max(row_height, REMINDER_TOKEN_SIZE_PX + PADDING_PX)

            # Now the sheet is as full as we can make it.
            output_filename = os.path.join(OUTPUT_DIR, f'print_sheet_{sheet_num}.png')
            current_sheet.save(output_filename)
            print(f"Saved {output_filename}")

            sheet_num += 1
            current_sheet = create_new_sheet()
            x_pos, y_pos, row_height, sheet_has_content = MARGIN_PX, MARGIN_PX, 0, False
            continue # Restart loop for the pending_token on the new sheet.

        try:
            with Image.open(path) as token_img:
                cropped_token = token_img.crop(token_img.getbbox())
                resized_img = cropped_token.resize((size, size), Image.Resampling.LANCZOS)
                current_sheet.paste(resized_img, (x_pos, y_pos), resized_img)
                sheet_has_content = True
        except Exception as e:
            print(f"Error processing image {path}: {e}")
            continue

        x_pos += size + PADDING_PX
        row_height = max(row_height, size + PADDING_PX)

    if sheet_has_content:
        output_filename = os.path.join(OUTPUT_DIR, f'print_sheet_{sheet_num}.png')
        current_sheet.save(output_filename)
        print(f"Saved {output_filename}")
    print(f"\nPrint sheet generation complete. Sheets are in the '{OUTPUT_DIR}' directory.")


if __name__ == '__main__':
    main()
