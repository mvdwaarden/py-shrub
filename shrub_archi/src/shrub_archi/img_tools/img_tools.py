from PIL import Image
import numpy as np


def remove_white_background(input_image_path, output_image_path, lower_threshold=200, upper_threshold=255):
    # Open the image
    img = Image.open(input_image_path)

    # Convert the image to RGBA (if it's not already in that mode)
    img = img.convert("RGBA")

    # Convert the image to a numpy array
    data = np.array(img)

    # Get the RGB channels (ignore the alpha channel for now)
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]

    # Create a mask to identify the "white" pixels (within the threshold range)
    white_mask = (r >= lower_threshold) & (r <= upper_threshold) & \
                 (g >= lower_threshold) & (g <= upper_threshold) & \
                 (b >= lower_threshold) & (b <= upper_threshold)

    # Set those pixels' alpha channel to 0 (fully transparent)
    data[white_mask] = [0, 0, 0, 0]  # R, G, B, A

    # Create a new image from the modified data
    new_img = Image.fromarray(data)

    # Save the result
    new_img.save(output_image_path, "PNG")
    print(f"Image saved as {output_image_path}")


def test_remove_white_background():
    # Example usage:
    input_image_path = "input_image.jpg"
    output_image_path = "output_image.png"
    lower_threshold = 200  # Minimum white value for the removal
    upper_threshold = 255  # Maximum white value for the removal

    remove_white_background(input_image_path, output_image_path, lower_threshold, upper_threshold)


if __name__ == "__main__":
    test_remove_white_background()