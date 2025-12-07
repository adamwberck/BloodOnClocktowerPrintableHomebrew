import math
import os
from PIL import Image, ImageDraw, ImageFont


def draw_text_on_arc(image, center_xy, radius, start_angle_deg, text_angle_deg, text, font, fill):
    """
    Draws text along a circular arc, with each letter individually rotated.

    Args:
        image (PIL.Image.Image): The image to draw on.
        center_xy (tuple): (x, y) coordinates of the arc's center.
        radius (int): The radius of the arc.
        start_angle_deg (float): The starting angle of the text on the arc in degrees.
                                 0 is to the right (3 o'clock), -90 is top (12 o'clock).
        text_angle_deg (float): The total angular distance the text should span.
        text (str): The text to display (will be converted to uppercase).
        font (PIL.ImageFont.FreeTypeFont): The font to use for the text.
        fill (tuple or str): The color of the text.
    """
    text = text.upper()
    if not text:
        return

    center_x, center_y = center_xy
    num_chars = len(text)

    # Calculate the angular step between the center of each character
    if num_chars > 1:
        angle_step = text_angle_deg / (num_chars - 1)
    else:
        angle_step = 0  # A single character is placed in the middle of the arc

    for i, char in enumerate(text):
        # Determine the angle for the current character
        if num_chars > 1:
            char_angle_deg = start_angle_deg + (i * angle_step)
        else:
            # Center the single character within the provided text_angle_deg
            char_angle_deg = start_angle_deg + text_angle_deg / 2

        # --- 1. Calculate character's center position on the arc ---
        char_angle_rad = math.radians(char_angle_deg)
        char_x = center_x + radius * math.cos(char_angle_rad)
        char_y = center_y + radius * math.sin(char_angle_rad)

        # --- 2. Create a temporary image for the single rotated character ---
        # Get character size
        char_bbox = font.getbbox(char)
        char_width = char_bbox[2] - char_bbox[0]
        char_height = char_bbox[3] - char_bbox[1]

        # Create a transparent canvas for the character, large enough for rotation
        temp_size = int(math.sqrt(char_width**2 + char_height**2) * 1.2)
        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)

        # Draw the character in the center of the temporary image
        temp_draw.text((temp_size / 2, temp_size / 2), char, font=font, fill=fill, anchor='mm')

        # --- 3. Rotate the character to be tangent to the arc ---
        # The rotation angle makes the character's "up" direction point away from the center
        if text_angle_deg > 0:
            rotation_angle = 270 - char_angle_deg
        else:
            rotation_angle = 90 - char_angle_deg
        rotated_char_img = temp_img.rotate(rotation_angle, expand=True, resample=Image.Resampling.BICUBIC)

        # --- 4. Paste the rotated character onto the main image ---
        # Calculate top-left corner for pasting to center the character on its arc position
        paste_x = int(char_x - rotated_char_img.width / 2)
        paste_y = int(char_y - rotated_char_img.height / 2)

        image.paste(rotated_char_img, (paste_x, paste_y), rotated_char_img)


def save_arc_text_example(filename="arc_text_example.png", text="EXAMPLE TEXT ON ARC"):
    """
    Creates and saves an image to demonstrate the draw_text_on_arc function.
    """
    # --- Setup Canvas ---
    width, height = 1024, 1024
    image = Image.new('RGBA', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # --- Font and Arc Parameters ---
    try:
        font_path = "dum1.ttf"
        font = ImageFont.truetype("dum1.ttf", 80)
    except IOError:
        print(f"Warning: {font_path} not found. Using default PIL font.")
        font = ImageFont.load_default(size=80)

    center = (width // 2, height // 2)
    radius = 400

    # Draw a guide circle for reference
    draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        outline='lightgray',
        width=2
    )

    big_r = 450
    draw.ellipse(
        (center[0] - big_r, center[1] - big_r, center[0] + big_r, center[1] + big_r),
        outline='lightgray',
        width=2
    )

    # --- Draw Text on Top Arc ---
    magic_ratio_length_to_width = 4.9
    text_width = draw.textlength(text, font=font)
    text_angle_deg = -text_width // magic_ratio_length_to_width
    start_angle_deg = 90 + abs(text_angle_deg//2)
    draw_text_on_arc(
        image=image,
        center_xy=center,
        radius=radius,
        start_angle_deg=start_angle_deg,
        text_angle_deg=text_angle_deg,
        text=text,
        font=font,
        fill='black'
    )

    # --- Save Image ---
    image.save(filename)
    print(f"Saved example image to '{os.path.abspath(filename)}'")


if __name__ == '__main__':
    save_arc_text_example(text="doppelganger")