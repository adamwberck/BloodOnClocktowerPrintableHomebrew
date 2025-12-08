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
    if not text:
        return
    text = text.strip()

    draw_text = ImageDraw.Draw(image)
    draw_text.text(center_xy, text, font=font, fill=fill, anchor='mm')

    center_x, center_y = center_xy
    def calc_char_width(char, next_char=None):
        if next_char is None:
            print(f'char: {char} next_char: {next_char}')
            return font.getlength(char)
        return font.getlength(f'{char}{next_char}') - font.getlength(next_char)
    

    char_widths = [calc_char_width(text[i], text[i+1])
                   if i < len(text)-1 else calc_char_width(text[i])
                   for i in range(len(text))]
    assert sum(char_widths) == font.getlength(text)
    char_angles = [ char_width / radius for char_width in char_widths]
    # char_angles = [math.acos(
    #                 (2 * math.pow(better_radius,2) - math.pow(char_width,2)) /
    #                 (2 * math.pow(better_radius,2))) for char_width in char_widths]
    print([f"{char}: {char_widths[i]}, {char_angles[i]}" for i, char in enumerate(text)])

    current_angle = math.radians(start_angle_deg)
    for i, char in enumerate(text):
        # --- 1. Calculate character's center position on the arc ---
        char_angle_rad = current_angle
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
        rotation_angle = 90 - math.degrees(current_angle)
        rotated_char_img = temp_img.rotate(rotation_angle, expand=True, resample=Image.Resampling.BICUBIC)


        # --- 4. Paste the rotated character onto the main image ---
        # Calculate top-left corner for pasting to center the character on its arc position
        paste_x = int(char_x - rotated_char_img.width / 2)
        paste_y = int(char_y - rotated_char_img.height / 2)

        image.paste(rotated_char_img, (paste_x, paste_y), rotated_char_img)
        draw = ImageDraw.Draw(image)
        half_w = rotated_char_img.width / 2
        draw.line((paste_x - half_w, paste_y, paste_x + half_w, paste_y))

        # --- 5. Increment the angle by the width
        char_width = char_widths[i]
        angle_step = char_angles[i]
        current_angle -= angle_step




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
    start_angle_deg = 120 + abs(text_angle_deg//2)
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
    save_arc_text_example(text="dpooel ganger")