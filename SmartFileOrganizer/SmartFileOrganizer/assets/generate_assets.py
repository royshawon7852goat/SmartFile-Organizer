"""Asset generator using Pillow.
Creates modern Windows 11 style app icons and visual graphics for Smart File Organizer.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
ICONS_DIR = BASE_DIR / "assets" / "icons"
IMAGES_DIR = BASE_DIR / "assets" / "images"

ICONS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def create_app_icon():
    """Generates a sleek, modern Windows 11 style gradient folder icon."""
    size = (256, 256)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Rounded background container
    # Deep slate / blue gradient simulated with layered rounded rectangles
    padding = 16
    draw.rounded_rectangle(
        [padding, padding, size[0] - padding, size[1] - padding],
        radius=48,
        fill=(22, 27, 34, 255),
        outline=(56, 139, 253, 200),
        width=4
    )

    # Folder base
    f_left, f_top, f_right, f_bottom = 48, 80, 208, 196
    # Tab
    draw.rounded_rectangle([f_left, f_top - 20, f_left + 60, f_top + 10], radius=8, fill=(31, 111, 235, 255))
    # Folder body
    draw.rounded_rectangle([f_left, f_top, f_right, f_bottom], radius=16, fill=(56, 139, 253, 255))

    # Inner organizing sparkle / gear / checkmark overlay
    # Draw organizing accent badge (emerald green circle with check/lightning)
    badge_center = (168, 156)
    badge_radius = 32
    draw.ellipse(
        [badge_center[0] - badge_radius, badge_center[1] - badge_radius,
         badge_center[0] + badge_radius, badge_center[1] + badge_radius],
        fill=(16, 185, 129, 255),
        outline=(255, 255, 255, 220),
        width=3
    )

    # Checkmark inside badge
    check_coords = [
        (badge_center[0] - 14, badge_center[1]),
        (badge_center[0] - 4, badge_center[1] + 10),
        (badge_center[0] + 14, badge_center[1] - 10)
    ]
    draw.line(check_coords, fill=(255, 255, 255, 255), width=5, joint="curve")

    # Save PNG
    png_path = ICONS_DIR / "app_icon.png"
    image.save(png_path, format="PNG")

    # Save multi-size ICO for Windows
    ico_path = ICONS_DIR / "app_icon.ico"
    image.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    print(f"Generated icons: {png_path} and {ico_path}")

if __name__ == "__main__":
    create_app_icon()
