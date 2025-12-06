import json
import time
import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont


IMAGE_Y = 0.60

def _setup_canvas(character_data, background_paths, image_size):
    """1. Sets up the canvas with the background and a circular mask."""
    W, H = image_size

    # --- 1a. Select and Load Background Image ---
    has_first_night = "firstNight" in character_data
    has_other_night = "otherNight" in character_data

    if has_first_night and has_other_night:
        bg_path = background_paths["both"]
    elif has_first_night:
        bg_path = background_paths["first"]
    elif has_other_night:
        bg_path = background_paths["other"]
    else:
        bg_path = background_paths["none"]

    final_image = Image.open(bg_path).convert("RGBA")
    draw = ImageDraw.Draw(final_image)
    return final_image, draw


def _add_reminder_number(final_image, draw, character_data, font_path, image_size):
    total_reminders = len(character_data.get("reminders", []))
    if total_reminders > 0:
        W, H = image_size
        font_size = 70
        font = ImageFont.truetype(font_path, font_size)
        text = str(total_reminders)
        
        # Calculate text size and position
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_height = text_bbox[3] - text_bbox[1]

        padding = 40
        text_x = W//2
        text_y = text_height/2 + padding

        # Create a new image for the text with transparency
        text_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)

        # Draw the text in white with low opacity (e.g., 128 out of 255)
        text_draw.text((text_x, text_y), text, font=font, anchor="mm", fill=(255, 255, 255, 175))

        # Composite the text layer onto the final image
        final_image.alpha_composite(text_layer)


def _add_character_image(final_image, char_img, image_size, pos=None, scale_factor=1.0):
    W, H = image_size
    
    # Resize and paste the character image
    img_w, img_h = char_img.size
    if img_w == 0 or img_h == 0:
        return # Avoid division by zero if image is empty after crop
    aspect_ratio = img_w / img_h
    new_h = int((W * scale_factor) / aspect_ratio)
    char_img = char_img.resize((int(W * scale_factor), new_h), Image.Resampling.LANCZOS)

    if pos:
        paste_x, paste_y = pos
        paste_x = int(paste_x - char_img.width // 2)
        paste_y = int(paste_y - char_img.height // 2)
    else:
        paste_x = (W - char_img.width) // 2
        paste_y = int((H - char_img.height) * IMAGE_Y)
    final_image.paste(char_img, (paste_x, paste_y), char_img)


def _crop_transparent_area(img):
    # Crop the image to the bounding box of the non-transparent parts
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    else:
        # Image is fully transparent, nothing to add.
        return
    return img


def _get_character_image(character_data):
    """Gets the character image from local cache or by downloading it."""
    image_url = character_data.get("image")
    if not image_url:
        return None

    # Handle case where 'image' is a list
    if isinstance(image_url, list):
        image_url = image_url[0]

    # Define a path to save downloaded images
    image_assets_path = "assets/character_images"
    os.makedirs(image_assets_path, exist_ok=True)

    # Create a unique filename for the character image
    image_filename = os.path.join(image_assets_path, f"{character_data.get('id')}.png")

    # Check if the image already exists locally
    if os.path.exists(image_filename):
        print(f"Using local image for {character_data.get('name')}: {image_filename}")
        try:
            return _crop_transparent_area(Image.open(image_filename).convert("RGBA"))
        except Exception as e:
            print(f"Error processing local image for {character_data.get('name')}: {e}. Attempting to re-download.")

    # Download image with retries
    retries = 3
    delay = 5  # seconds
    for attempt in range(retries):
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            print(f"Successfully downloaded image for {character_data.get('name')} on attempt {attempt + 1}")
            # Process and save image
            try:
                char_img_data = io.BytesIO(response.content)
                char_img = Image.open(char_img_data).convert("RGBA")
                char_img.save(image_filename)  # Save the downloaded image locally
                return _crop_transparent_area(Image.open(image_filename).convert("RGBA"))
            except Exception as e:
                print(f"Error processing image for {character_data.get('name')} after download: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {character_data.get('name')}: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)

    print(f"Could not download image for {character_data.get('name')} after {retries} attempts.")
    return None


# Calculate the maximum width for each line based on its vertical position
# This creates a more circular text area at the top
def get_max_line_width(y_position, line_height, image_size, margin_px=0):
    """
    Calculates the max width for a line of text to fit within a circle.

    The width is calculated based on the y-position of the line, ensuring it
    stays within the circular boundary with a given margin from the edge.
    """

    W, H = image_size
    W = W * 0.82
    radius = W / 2
    center_y = H / 2

    # Calculate width at the bottom of the line, where the circle is narrowest for that line.
    y_for_width_calc = y_position + line_height

    # Distance of the line's bottom from the horizontal centerline of the circle
    dist_from_center = abs(y_for_width_calc - center_y)

    if dist_from_center >= radius:
        return 0  # Line is outside the circle

    # Using Pythagorean theorem: half_width^2 + dist_from_center^2 = radius^2
    half_width = (radius**2 - dist_from_center**2)**0.5
    full_width = 2 * half_width

    # Apply margin
    return max(0, full_width - margin_px)


def _calculate_ability_text_layout(character_data, font_path, image_size):
    """Calculates font size and wrapped text for the ability."""
    name = character_data.get("name", "")
    ability_text = character_data.get("ability", "")
    if not ability_text:
        return None, None, 50  # Return default font size

    START_Y = 0.10
    _, H = image_size
    total_lines = 1
    step_down = 2
    font_size = 46 + step_down
    font = None
    max_lines = 0
    wrapped_lines = []
    MINIMUM_FONT_SIZE = 42
    while total_lines > max_lines:
        font_size -= step_down
        if font_size < MINIMUM_FONT_SIZE: # Prevent font from becoming too small
            font_size = MINIMUM_FONT_SIZE
            break
        max_lines = (100-font_size) // 10.8
        font = ImageFont.truetype(font_path, font_size) # Load the font

        words = ability_text.split()
        wrapped_lines = []
        current_line = ""
        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] # Approximate line height

        # Initial y_position for the first line
        current_y_pos = START_Y * H

        for word in words:
            test_line = f"{current_line} {word}" if current_line else word
            max_width_for_this_line = get_max_line_width(current_y_pos, line_height, image_size)

            if font.getlength(test_line) <= max_width_for_this_line:
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                current_line = word
                current_y_pos += line_height # Move to the next line's y position
        if current_line:
            wrapped_lines.append(current_line)

        total_lines = len(wrapped_lines)

    wrapped_text = "\n".join(wrapped_lines)
    name = character_data.get("name", "").upper()
    print(f'{name}: total lines: {total_lines} font size: {font_size}')
    return font, wrapped_text, font_size


def _add_ability_text(draw, font, wrapped_text, image_size):
    """Adds the character's ability text to the top of the token."""
    if not wrapped_text:
        return

    W, H = image_size
    START_Y = 0.10
    draw.multiline_text(
        (W / 2, H*START_Y),
        wrapped_text,
        fill="black",
        font=font,
        anchor="ma",
        align="center"
    )


def create_reminder_token(character_data, font_path, background_path, image_size=(1024, 1024)):
    reminders = character_data.get("reminders", [])
    for index, reminder in enumerate(reminders):
        # Load the background image for the reminder token
        # Assuming background_path is a direct path to the reminder token background
        reminder_image = Image.open(background_path).convert("RGBA")

        reminder_draw = ImageDraw.Draw(reminder_image)

        if reminder:
            W, H = image_size
            font_size = 60
            font = ImageFont.truetype(font_path, font_size)
            
            # Wrap text
            words = reminder.split()
            wrapped_lines = []
            current_line = ""
            max_width = W * 0.8 # 80% of image width
            for word in words:
                test_line = f"{current_line} {word}" if current_line else word
                if font.getlength(test_line) <= max_width:
                    current_line = test_line
                else:
                    wrapped_lines.append(current_line)
                    current_line = word
            if current_line:
                wrapped_lines.append(current_line)
            
            display_text = "\n".join(wrapped_lines)
            
            text_x = W // 2
            text_y = (H // 4) * 3
            reminder_draw.multiline_text(
                (text_x, text_y),
                display_text,
                fill="white",
                font=font,
                anchor="mm",
                align="center"
            )
            image_pos = (W//2, (H / 2) - (H * .05))
            print(f'image pos: {image_pos}')
            print(f'W:{W} H:{H}')
            char_img_obj = _get_character_image(character_data)
            if char_img_obj:
                _add_character_image(reminder_image, char_img_obj, image_size, pos=image_pos, scale_factor=0.70)

        # Save the reminder image
        reminder_output_path = "reminder_tokens"
        team_name = character_data.get("team")
        if team_name:
            reminder_output_path = os.path.join(reminder_output_path, team_name.lower().replace(" ", "_"))
        
        char_id = character_data.get("id")
        if char_id:
            reminder_output_path = os.path.join(reminder_output_path, char_id)
        
        os.makedirs(reminder_output_path, exist_ok=True)
        
        # Sanitize reminder text for filename
        sanitized_reminder_text = reminder.replace(" ", "_")
        output_filename = f"{reminder_output_path}/{sanitized_reminder_text}_{index}.png"
        reminder_image.save(output_filename)
        print(f"Created reminder token for {reminder} at {output_filename}")
    


def _add_character_name(draw, character_data, font_path, image_size):
    """4. Adds the character's name to the bottom of the token."""
    name = character_data.get("name", "").upper()
    if not name:
        return
    W, H = image_size
    LARGE_FONT_SIZE = 120
    MED_FONT_SIZE = 90
    SMALL_FONT_SIZE = 74
    
    # Determine font size dynamically
    name_font_size = LARGE_FONT_SIZE
    name_font = ImageFont.truetype(font_path, name_font_size)
    max_name_width = W * 0.60

    name_font_length = name_font.getlength(name)
    if name_font_length > max_name_width:
        name_font_size = MED_FONT_SIZE
        name_font = ImageFont.truetype(font_path, name_font_size)
        name_font_length = name_font.getlength(name)
        if name_font_length > max_name_width:
            name_font_size = SMALL_FONT_SIZE
    print(f'name: {name}  font length: {name_font.getlength(name)} font size {name_font_size}')
    name_font = ImageFont.truetype(font_path, name_font_size)
    name_x = W / 2
    name_y = H * 0.82  # Position near the bottom
    draw.text(
        (name_x, name_y),
        name,
        fill="black",
        font=name_font,
        anchor="mm"
    )


def _finalize_and_save(final_image, character_data, output_path):
    """5. Finalizes and saves the token image."""
    char_id = character_data.get("id")
    # final_image.putalpha(mask) # Apply the circular mask
    # # Create a subfolder for the team if team data is available
    team_name = character_data.get("team")
    if team_name:
        team_output_path = os.path.join(output_path, team_name.lower().replace(" ", "_"))
        if not os.path.exists(team_output_path):
            os.makedirs(team_output_path)
        output_path = team_output_path

    output_filename = f"{output_path}/{char_id}.png"
    final_image.save(output_filename)
    print(f"Created token for {character_data.get('name')} at {output_filename}")


def create_character_token(character_data, font_paths, background_paths, output_path, image_size=(1024, 1024)):
    """
    Creates a circular token for a character by orchestrating helper functions.

    Args:
        character_data (dict): A dictionary containing the character's info.
        font_paths (dict): Paths to the .ttf font files for name and description.
        background_paths (dict): Paths to the background images.
        output_path (str): The folder to save the generated image in.
        image_size (tuple): The size of the output image (width, height).
    """
    # --- 0. Pre-check ---
    char_id = character_data.get("id")
    if not char_id or char_id == "_meta":
        return  # Skip meta object
    

    # create_reminder_token(character_data, font_paths.get("description"), background_paths["reminder"], image_size)

    # --- 1. Setup Canvas ---
    final_image, draw = _setup_canvas(character_data, background_paths, image_size)

    W, H = image_size

    _add_reminder_number(final_image, draw, character_data, font_paths.get("description"), image_size)

    # --- 2. Get assets and calculate text layout ---
    char_img_obj = _get_character_image(character_data)
    font, wrapped_text, _ = _calculate_ability_text_layout(character_data, font_paths.get("description"), image_size)

    # --- 3. Iteratively find best image scale to avoid text overlap ---
    image_scale_factor = .5  # Start with default/max scale

    if char_img_obj and wrapped_text:
        # Get text bounding box to find its bottom edge
        text_bbox = draw.multiline_textbbox((W / 2, H * 0.10), wrapped_text, font=font, anchor="ma", align="center")
        text_bottom = text_bbox[3]

        # Loop to shrink image until it doesn't overlap with the text
        for _ in range(2000):
            # Calculate image geometry for the current scale
            img_w, img_h = char_img_obj.size
            aspect_ratio = img_w / img_h if img_h > 0 else 1
            resized_img_h = int((W * image_scale_factor) / aspect_ratio)
            image_top_y = int((H - resized_img_h) * IMAGE_Y)

            # Check for overlap (with some padding)
            padding_px = 10
            print(f'{character_data.get("name")}: text bottom:{text_bottom} image top: {image_top_y-padding_px}')
            if text_bottom < image_top_y - padding_px:
                break  # Found a good scale, exit loop
            else:
                image_scale_factor *= 0.97  # Shrink scale by 3% and retry
        print(f"INFO: {character_data.get('name')} Final image scale is {image_scale_factor:.2f}")

    # --- 4. Add Character Image ---
    if char_img_obj:
        _add_character_image(final_image, char_img_obj, image_size, scale_factor=image_scale_factor)

    # --- 5. Add Ability Text ---
    _add_ability_text(draw, font, wrapped_text, image_size)

    # --- 6. Add Character Name ---
    _add_character_name(draw, character_data, font_paths.get("name"), image_size)

    # --- 7. Finalize and Save ---
    _finalize_and_save(final_image, character_data, output_path)


if __name__ == '__main__':
    # Make sure these paths are correct
    JSON_FILE_PATH = 'menagerie_fixed.json'
    NAME_FONT_PATH = 'dum1.ttf'
    DESCRIPTION_FONT_PATH = 'trade-gothic-lt.ttf'
    BACKGROUND_PATHS = {
        "both": "assets/backgrounds_light/left right token.png",
        "first": "assets/backgrounds_light/left token.png",
        "other": "assets/backgrounds_light/right token.png",
        "none": "assets/backgrounds_light/non token.png",
        "reminder": "assets/backgrounds_light/reminder.png"
    }
    OUTPUT_FOLDER = 'character_tokens'

    import os
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        all_characters = json.load(f)

    for  i, character in enumerate(all_characters):
        create_character_token(character, {"name": NAME_FONT_PATH, "description": DESCRIPTION_FONT_PATH}, BACKGROUND_PATHS, OUTPUT_FOLDER)
    
