from graph.builder import graph 
import os
from datetime import datetime

try:
    png_data = graph.get_graph().draw_mermaid_png()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(current_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = os.path.join(images_dir, f"global_graph_{timestamp}.png")

    with open(image_filename, "wb") as f:
        f.write(png_data)
    print(f"Graph image saved to {image_filename}")

except Exception as e:
    print(f"Error generating or saving graph image: {e}")

