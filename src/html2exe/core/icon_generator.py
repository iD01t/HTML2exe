from PIL import Image, ImageDraw, ImageFont


class IconGenerator:
    """Professional icon generator with multiple formats."""

    @staticmethod
    def generate_icon(text: str, output_path: str, size: int = 256):
        """Generate professional application icon."""
        # Create image with gradient background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Gradient background
        for y in range(size):
            r = int(102 + (116 * y / size))  # 667eea to 764ba2
            g = int(126 - (47 * y / size))
            b = int(234 - (72 * y / size))
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

        # Draw circle background
        margin = size // 8
        circle_size = size - 2 * margin
        draw.ellipse([margin, margin, margin + circle_size, margin + circle_size],
                     fill=(255, 255, 255, 30))

        # Draw text
        try:
            font_size = size // 4
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("calibri.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()

        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center text
        x = (size - text_width) // 2
        y = (size - text_height) // 2

        # Draw text with shadow
        draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 100), font=font)
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

        # Save as ICO
        img.save(output_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        return output_path
