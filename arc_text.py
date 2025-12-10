import math
import os
from PIL import Image, ImageDraw, ImageFont


def draw_text_on_arc(image, center_xy, radius, start_angle_deg, text, font, fill):
    """
    Draws text along a circular arc, with each letter individually rotated.

    Args:
        image (PIL.Image.Image): The image to draw on.
        center_xy (tuple): (x, y) coordinates of the arc's center.
        radius (int): The radius of the arc.
        start_angle_deg (float): The starting angle of the text on the arc in degrees.
                                 0 is to the right (3 o'clock), -90 is top (12 o'clock).
        text (str): The text to display (will be converted to uppercase).
        font (PIL.ImageFont.FreeTypeFont): The font to use for the text.
        fill (tuple or str): The color of the text.
    """
    if not text:
        return
    text = text.strip()

    draw = ImageDraw.Draw(image)
    center_x, center_y = center_xy

    # The start_angle_deg is the angle where the text should begin.
    # The caller is responsible for calculating this to center the text block if desired.
    start_angle_rad = math.radians(start_angle_deg)

    for i, char in enumerate(text):
        # --- 1. Calculate character's center position on the arc ---
        # Use textlength to get kerning-aware positioning.
        # This measures the width of the string up to the current character.
        width_before = draw.textlength(text[:i], font=font)
        # This is the advance width of the character itself.
        char_advance = draw.textlength(text[:i+1], font=font) - width_before

        # The angle for the center of this character.
        # We add half the character's advance to the width before it.
        angle_offset_rad = (width_before + char_advance / 2) / radius
        char_angle_rad = start_angle_rad - angle_offset_rad

        char_x = center_x + radius * math.cos(char_angle_rad)
        char_y = center_y + radius * math.sin(char_angle_rad)

        # --- 2. Create a temporary image for the single rotated character ---
        # Get character glyph size from its bounding box.
        left, top, right, bottom = font.getbbox(char)
        char_width = right - left
        char_height = bottom - top

        # Create a transparent canvas for the character, large enough for rotation
        # A larger multiplier provides more space to avoid clipping during rotation.
        temp_size = int(math.sqrt(char_width**2 + char_height**2) * 1.4)
        if temp_size == 0:
            continue  # Skip spaces or zero-width characters

        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)

        # Draw the character in the center of the temporary image
        temp_draw.text((temp_size / 2, temp_size / 2), char, font=font, fill=fill, anchor='mm')

        # --- 3. Rotate the character to be tangent to the arc ---
        rotation_angle = -math.degrees(char_angle_rad) + 90
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
    text = text.upper()

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
    text_width = draw.textlength(text, font=font)
    text_angle_deg = math.degrees( text_width / radius)
    # For drawing on the top arc, start angle should be calculated to center the text.
    # 90 degrees is the top of the circle. We start from the left of the top.
    start_angle_deg = 90 + text_angle_deg / 2
    draw_text_on_arc(
        image=image,
        center_xy=center,
        radius=radius,
        start_angle_deg=start_angle_deg,
        text=text,
        font=font,
        fill='black'
    )

    # --- Save Image ---
    image.save(filename)
    print(f"Saved example image to '{os.path.abspath(filename)}'")


if __name__ == '__main__':
    save_arc_text_example(text="dpooel ganger")