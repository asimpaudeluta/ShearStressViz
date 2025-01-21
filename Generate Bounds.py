import os
import rasterio
from rasterio.warp import transform_bounds, calculate_default_transform, reproject, Resampling
from rasterio.plot import reshape_as_image
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
from PIL import Image
import json

# Directory containing your .tif files
input_directory = "Raster_files_for_Shear_Stress"

# Output JSON file
output_json = "raster_bounds.json"

# Target CRS for rasters and bounds (EPSG:3857 - Web Mercator)
target_crs = "EPSG:3857"

# Dictionary to store raster bounds
raster_bounds = {}

# Calculate global min and max across all datasets
global_min, global_max = float('inf'), float('-inf')

# First pass to compute global min and max
for filename in os.listdir(input_directory):
    if filename.endswith(".tif"):
        filepath = os.path.join(input_directory, filename)
        with rasterio.open(filepath) as dataset:
            data = dataset.read(1, masked=True)  # Read the first band
            global_min = min(global_min, np.min(data))
            global_max = max(global_max, np.max(data))

# Normalize function
norm = Normalize(vmin=global_min, vmax=global_max)

# Inferno color map
cmap = plt.get_cmap('inferno')

# Second pass to reproject and save each raster as PNG
for filename in os.listdir(input_directory):
    if filename.endswith(".tif"):
        filepath = os.path.join(input_directory, filename)

        # Open the .tif file with rasterio
        with rasterio.open(filepath) as dataset:
            # Reproject the dataset to the target CRS (EPSG:3857)
            transform, width, height = calculate_default_transform(
                dataset.crs, target_crs, dataset.width, dataset.height, *dataset.bounds
            )
            kwargs = dataset.meta.copy()
            kwargs.update({
                "crs": target_crs,
                "transform": transform,
                "width": width,
                "height": height
            })

            # Create a temporary in-memory raster for reprojection
            with rasterio.MemoryFile() as memfile:
                with memfile.open(**kwargs) as temp_dataset:
                    for i in range(1, dataset.count + 1):
                        reproject(
                            source=rasterio.band(dataset, i),
                            destination=rasterio.band(temp_dataset, i),
                            src_transform=dataset.transform,
                            src_crs=dataset.crs,
                            dst_transform=transform,
                            dst_crs=target_crs,
                            resampling=Resampling.nearest
                        )

                    # Get the transformed bounds
                    bounds = temp_dataset.bounds

                    # Save the bounds in EPSG:3857
                    raster_bounds[filename] = {
                        "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top]
                    }

                    # Read the first band (data)
                    data = temp_dataset.read(1, masked=True)

                    # Normalize data and apply colormap
                    normalized_data = norm(data)  # Normalize to 0-1 range
                    colored_data = cmap(normalized_data)  # Apply colormap

                    # Handle no-data values by setting alpha to 0
                    colored_data[..., -1] = ~data.mask  # Alpha channel (0 where masked)

                    # Convert to 8-bit RGBA for saving as PNG
                    rgba_data = (colored_data * 255).astype(np.uint8)

                    # Create output PNG path
                    output_png = os.path.join(input_directory, f"{os.path.splitext(filename)[0]}.png")

                    # Save as PNG
                    Image.fromarray(rgba_data).save(output_png)

# Write the bounds to a JSON file
with open(output_json, "w") as json_file:
    json.dump(raster_bounds, json_file, indent=4)

# Create and save the legend
legend_output = os.path.join(input_directory, "legend.png")
fig, ax = plt.subplots(figsize=(6, 1))
fig.subplots_adjust(bottom=0.5)

# Create a colorbar with the global min and max
cb = plt.colorbar(
    plt.cm.ScalarMappable(norm=norm, cmap=cmap),
    cax=ax,
    orientation='horizontal',
    label="Shear Stress (Low to High)",
)
cb.set_label("Shear Stress (Low to High)", fontsize=12)

# Save the legend as a PNG
plt.savefig(legend_output, dpi=300, bbox_inches="tight")
plt.close()

print(f"Bounds saved to {output_json}")
print("PNG files and legend generated.")