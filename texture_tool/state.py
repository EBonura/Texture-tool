"""State management for the Texture Tool application."""

import reflex as rx
import os
import io
import base64
from pathlib import Path
from typing import List
from PIL import Image


class FileItem(rx.Base):
    """Represents a file or folder item."""
    name: str
    path: str
    is_folder: bool
    level: int
    parent: str


class State(rx.State):
    """The app state."""
    file_items: List[FileItem] = []
    expanded_folders: List[str] = []
    selected_image: str = ""
    selected_image_data: str = ""
    image_format: str = ""
    image_resolution: str = ""
    image_file_size: str = ""
    texture_directory: str = "/Users/ebonura/Desktop/Godot/cortex-ignition-2/textures"
    zoom_level: float = 1.0
    image_width: int = 0
    image_height: int = 0
    directory_input: str = ""

    # Resize properties
    resize_width: int = 128
    resize_height: int = 128
    resize_mode: str = "nearest"  # nearest, point, or bilinear
    color_depth: int = 16  # bits per pixel (PS1 was 16-bit)
    dithering: bool = True
    processed_image_data: str = ""
    show_processed: bool = False
    
    def process_image(self):
        """Process the image with PS1-style effects."""
        if not self.selected_image:
            return rx.window_alert("Please select an image first")
        
        full_path = os.path.join(self.texture_directory, self.selected_image)
        
        try:
            # Open the image
            img = Image.open(full_path)
            
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Resize with nearest neighbor for that crunchy PS1 look
            if self.resize_mode == "nearest":
                resample = Image.NEAREST
            elif self.resize_mode == "point":
                resample = Image.NEAREST  # Same as nearest
            else:  # bilinear for comparison
                resample = Image.BILINEAR
            
            resized = img.resize((self.resize_width, self.resize_height), resample)
            
            # Apply color depth reduction for PS1 effect
            if self.color_depth == 16:
                # Convert to 16-bit color (5-6-5 RGB)
                resized = resized.convert('RGB')
                pixels = resized.load()
                for y in range(resized.height):
                    for x in range(resized.width):
                        r, g, b = pixels[x, y]
                        # 5 bits for R and B, 6 bits for G
                        r = (r >> 3) << 3
                        g = (g >> 2) << 2
                        b = (b >> 3) << 3
                        pixels[x, y] = (r, g, b)
            elif self.color_depth == 8:
                # 8-bit color palette
                resized = resized.convert('P', palette=Image.ADAPTIVE, colors=256)
                if self.dithering:
                    resized = resized.convert('RGB')
            elif self.color_depth == 4:
                # 4-bit color (16 colors)
                resized = resized.convert('P', palette=Image.ADAPTIVE, colors=16)
                if self.dithering:
                    resized = resized.convert('RGB')
            
            # Convert to base64 for display
            buffered = io.BytesIO()
            resized.save(buffered, format="PNG")
            processed_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            self.processed_image_data = f"data:image/png;base64,{processed_data}"
            self.show_processed = True
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return rx.window_alert(f"Error processing image: {str(e)}")

    def set_color_depth_from_string(self, value: str):
        """Set color depth from radio group string value."""
        if "4-bit" in value:
            self.color_depth = 4
        elif "8-bit" in value:
            self.color_depth = 8
        else:  # "16-bit (PS1 native)"
            self.color_depth = 16
            
    def set_resize_width_from_string(self, value: str):
        """Set resize width from string value."""
        try:
            self.resize_width = int(value)
        except ValueError:
            self.resize_width = 128  # Default fallback

    def set_resize_height_from_string(self, value: str):
        """Set resize height from string value."""
        try:
            self.resize_height = int(value)
        except ValueError:
            self.resize_height = 128  # Default fallback

    def toggle_preview(self):
        """Toggle between original and processed image."""
        if self.processed_image_data:
            self.show_processed = not self.show_processed

    def on_load(self):
        """Auto-load images when the page loads."""
        self.directory_input = self.texture_directory  # Initialize input with current directory
        self.load_images()
    
    def update_directory(self):
        """Update the texture directory and reload images."""
        new_directory = self.directory_input.strip()
        
        # Check if the directory exists
        if os.path.exists(new_directory) and os.path.isdir(new_directory):
            self.texture_directory = new_directory
            self.selected_image = ""  # Clear current selection
            self.selected_image_data = ""
            self.load_images()
        else:
            return rx.window_alert(f"Invalid directory: {new_directory}")

    def go_up_directory(self):
        """Navigate to the parent directory."""
        parent_dir = os.path.dirname(self.texture_directory)
        
        # Check if we're not already at the root
        if parent_dir and parent_dir != self.texture_directory:
            self.texture_directory = parent_dir
            self.directory_input = parent_dir
            self.selected_image = ""  # Clear current selection
            self.selected_image_data = ""
            self.load_images()
        else:
            return rx.window_alert("Already at root directory")

    def load_images(self):
        """Load all image files and build a flat list with hierarchy info."""
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tga', '.webp', '.exr', '.hdr'}
        
        if not os.path.exists(self.texture_directory):
            self.file_items = []
            return
        
        items = []
        
        # First, collect all folders and files
        folder_contents = {}
        
        for root, dirs, files in os.walk(self.texture_directory):
            relative_root = os.path.relpath(root, self.texture_directory)
            if relative_root == ".":
                relative_root = ""
            
            # Store folder structure
            if relative_root:
                parts = relative_root.split(os.sep)
                for i, part in enumerate(parts):
                    folder_path = os.sep.join(parts[:i+1])
                    parent = os.sep.join(parts[:i]) if i > 0 else ""
                    
                    if folder_path not in folder_contents:
                        folder_contents[folder_path] = {
                            'item': FileItem(
                                name=part,
                                path=folder_path,
                                is_folder=True,
                                level=i,
                                parent=parent
                            ),
                            'children': []
                        }
            
            # Collect image files
            image_files = []
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    file_path = os.path.join(relative_root, file) if relative_root else file
                    level = len(relative_root.split(os.sep)) if relative_root else 0
                    image_files.append(FileItem(
                        name=file,
                        path=file_path,
                        is_folder=False,
                        level=level,
                        parent=relative_root
                    ))
            
            # Store files in their parent folder
            if relative_root and relative_root in folder_contents:
                folder_contents[relative_root]['children'].extend(image_files)
            elif not relative_root:
                # Root level files
                items.extend(sorted(image_files, key=lambda x: x.name))
        
        # Build the final list with proper ordering
        def add_folder_and_children(folder_path, folder_data):
            items.append(folder_data['item'])
            # Add immediate children (files)
            for child in sorted(folder_data['children'], key=lambda x: x.name):
                items.append(child)
            # Add subfolders
            for sub_path, sub_data in sorted(folder_contents.items()):
                if sub_data['item'].parent == folder_path:
                    add_folder_and_children(sub_path, sub_data)
        
        # Add root level folders
        for folder_path, folder_data in sorted(folder_contents.items()):
            if not folder_data['item'].parent:  # Root level folder
                add_folder_and_children(folder_path, folder_data)
        
        self.file_items = items
    
    def toggle_folder(self, folder_path: str):
        """Toggle folder expansion state."""
        if folder_path in self.expanded_folders:
            # When collapsing a folder, also collapse all its subfolders
            self.expanded_folders = [
                f for f in self.expanded_folders 
                if f != folder_path and not f.startswith(folder_path + os.sep)
            ]
        else:
            # When expanding, just add this folder
            self.expanded_folders = self.expanded_folders + [folder_path]
    
    def select_image(self, image_path: str):
        """Select an image to display and load it as base64."""
        self.selected_image = image_path
        
        # Load image as base64 and extract metadata
        full_path = os.path.join(self.texture_directory, image_path)
        try:
            # Get file size
            file_size = os.path.getsize(full_path)
            if file_size < 1024:
                self.image_file_size = f"{file_size} B"
            elif file_size < 1024 * 1024:
                self.image_file_size = f"{file_size / 1024:.1f} KB"
            else:
                self.image_file_size = f"{file_size / (1024 * 1024):.1f} MB"
            
            # Load image with PIL to get metadata
            with Image.open(full_path) as img:
                self.image_format = img.format or Path(image_path).suffix.upper().lstrip('.')
                self.image_resolution = f"{img.width} × {img.height}"
                self.image_width = img.width
                self.image_height = img.height
            
            # Load image as base64
            with open(full_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                # Get file extension to determine MIME type
                ext = Path(image_path).suffix.lower()
                if ext in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif ext == '.png':
                    mime_type = 'image/png'
                elif ext == '.bmp':
                    mime_type = 'image/bmp'
                elif ext == '.webp':
                    mime_type = 'image/webp'
                else:
                    mime_type = 'image/png'  # Default fallback
                
                self.selected_image_data = f"data:{mime_type};base64,{image_data}"
        except Exception as e:
            print(f"Error loading image: {e}")
            self.selected_image_data = ""
            self.image_format = ""
            self.image_resolution = ""
            self.image_file_size = ""
            self.image_width = 0
            self.image_height = 0
    
    def set_zoom(self, level: float):
        """Set the zoom level."""
        self.zoom_level = level
    
    def zoom_in(self):
        """Increase zoom level."""
        if self.zoom_level < 4.0:
            if self.zoom_level < 1.0:
                self.zoom_level = min(self.zoom_level * 2, 1.0)
            else:
                self.zoom_level = min(self.zoom_level + 1.0, 4.0)
    
    def zoom_out(self):
        """Decrease zoom level."""
        if self.zoom_level > 0.125:
            if self.zoom_level <= 1.0:
                self.zoom_level = max(self.zoom_level / 2, 0.125)
            else:
                self.zoom_level = max(self.zoom_level - 1.0, 0.125)