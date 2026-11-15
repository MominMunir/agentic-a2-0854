from PIL import Image, ImageDraw, ImageFont

from gigbid_core.config import ROOT


def main():
    frames = []
    titles = [
        ("inbox-desktop.png", "1. Discover opportunities"),
        ("proposal-studio.png", "2. Review the draft and its evidence"),
        ("inbox-mobile.png", "3. Keep control on mobile"),
    ]
    for filename, title in titles:
        image = Image.open(ROOT / "docs/images" / filename).convert("RGB")
        image.thumbnail((1000, 650))
        canvas = Image.new("RGB", (1040, 740), "#f5f7f1")
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
        except OSError:
            font = ImageFont.load_default(size=22)
        draw.text((25, 15), title, fill="#195d4b", font=font)
        canvas.paste(image, ((1040 - image.width) // 2, 60))
        draw.text(
            (25, 710),
            "Actual UI captures · synthetic smoke-test data · human approval required",
            fill="#63795e",
            font=ImageFont.load_default(size=15),
        )
        frames.append(canvas)
    frames[0].save(
        ROOT / "docs/images/demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=10000,
        loop=0,
        optimize=True,
    )
    print("30-second GIF assembled from actual verified UI screenshots.")


if __name__ == "__main__":
    main()
