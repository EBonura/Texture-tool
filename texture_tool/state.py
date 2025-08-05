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
        folders_seen = set()
        
        # Walk through directory and collect all items
        for root, _, files in os.walk(self.texture_directory):
            relative_root = os.path.relpath(root, self.texture_directory)
            if relative_root == ".":
                relative_root = ""
            
            # Add folders to the list
            if relative_root and relative_root not in folders_seen:
                parts = relative_root.split(os.sep)
                for i, part in enumerate(parts):
                    folder_path = os.sep.join(parts[:i+1])
                    if folder_path not in folders_seen:
                        folders_seen.add(folder_path)
                        items.append(FileItem(
                            name=part,
                            path=folder_path,
                            is_folder=True,
                            level=i,
                            parent=os.sep.join(parts[:i]) if i > 0 else ""
                        ))
            
            # Add image files
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    file_path = os.path.join(relative_root, file) if relative_root else file
                    level = len(relative_root.split(os.sep)) if relative_root else 0
                    items.append(FileItem(
                        name=file,
                        path=file_path,
                        is_folder=False,
                        level=level,
                        parent=relative_root
                    ))
        
        self.file_items = sorted(items, key=lambda x: (x.parent, not x.is_folder, x.name))
    
    def is_item_visible(self, item: FileItem) -> bool:
        """Check if an item should be visible based on parent folder expansion."""
        if not item.parent:
            return True
        
        # Check if all parent folders are expanded
        parent_parts = item.parent.split(os.sep)
        for i in range(len(parent_parts)):
            parent_path = os.sep.join(parent_parts[:i+1])
            if parent_path not in self.expanded_folders:
                return False
        
        return True
    
    @rx.var
    def visible_items(self) -> List[FileItem]:
        """Return only the items that should be visible."""
        return [item for item in self.file_items if self.is_item_visible(item)]
    
    def is_folder_expanded(self, folder_path: str) -> bool:
        """Check if a folder is expanded."""
        return folder_path in self.expanded_folders
    
    def toggle_folder(self, folder_path: str):
        """Toggle folder expansion state."""
        if folder_path in self.expanded_folders:
            self.expanded_folders = [f for f in self.expanded_folders if f != folder_path]
        else:
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