import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# Load the image
img = Image.open('graveyard_floor.png')

# Convert image to numpy array
img_array = np.array(img)

# Tile the image 4x4
tiled_array = np.tile(img_array, (4, 4, 1))

# Convert back to image
tiled_img = Image.fromarray(tiled_array)

# Save the tiled image
tiled_img.save('tiled_graveyard_floor_4x4.png')

# Display the tiled image
plt.imshow(tiled_img)
plt.axis('off')
plt.show()
