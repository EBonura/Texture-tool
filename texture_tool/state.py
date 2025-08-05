"""State management for the Texture Tool application."""

import reflex as rx
import os
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
    image_width: int = 0  # Add this
    image_height: int = 0  # Add this
    
    def on_load(self):
        """Auto-load images when the page loads."""
        self.load_images()
    
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
            self.expanded_folders = [f for f in self.expanded_folders if f != folder_path]
        else:
            self.expanded_folders = self.expanded_folders + [folder_path]
    
    def select_image(self, image_path: str):
        """Select an image to display and load it as base64."""
        self.selected_image = image_path
        self.zoom_level = 1.0  # Reset zoom when selecting new image
        
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
                self.image_width = img.width  # Store actual width
                self.image_height = img.height  # Store actual height
            
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
            self.zoom_level = min(self.zoom_level + 1.0, 4.0)
    
    def zoom_out(self):
        """Decrease zoom level."""
        if self.zoom_level > 1.0:
            self.zoom_level = max(self.zoom_level - 1.0, 1.0)