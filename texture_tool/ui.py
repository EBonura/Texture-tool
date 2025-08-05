"""UI components for the Texture Tool application."""

import reflex as rx
from .state import State, FileItem


def is_item_visible(item: FileItem) -> rx.Var:
    """Check if an item should be visible based on parent folder expansion."""
    # For root items (parent is empty string), always visible
    # For items with parents, check if parent is expanded
    return rx.cond(
        item.parent == "",
        True,  # Root items always visible
        State.expanded_folders.contains(item.parent)  # Check if parent folder is expanded
    )


def folder_item(item: FileItem) -> rx.Component:
    """Create a folder button."""
    return rx.button(
        rx.hstack(
            rx.cond(
                State.expanded_folders.contains(item.path),
                rx.text("📂", font_size="16px", width="20px", text_align="center"),
                rx.text("📁", font_size="16px", width="20px", text_align="center")
            ),
            rx.text(item.name, font_size="14px", white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            spacing="2",
            align="center",
            width="100%"
        ),
        on_click=State.toggle_folder(item.path),
        variant="ghost",
        width="100%",
        justify="start",
        padding_left=f"{item.level * 20 + 8}px",
        padding_y="2",
        min_height="32px"
    )


def file_item(item: FileItem) -> rx.Component:
    """Create a file button."""
    return rx.button(
        rx.hstack(
            rx.text("🖼️", font_size="16px", width="20px", text_align="center"),
            rx.text(item.name, font_size="14px", white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            spacing="2",
            align="center",
            width="100%"
        ),
        on_click=State.select_image(item.path),
        variant="ghost",
        width="100%",
        justify="start", 
        padding_left=f"{item.level * 20 + 8}px",
        padding_y="2",
        min_height="32px"
    )


def tree_item(item: FileItem) -> rx.Component:
    """Create a tree item (folder or file)."""
    return rx.cond(
        is_item_visible(item),
        rx.cond(
            item.is_folder,
            folder_item(item),
            file_item(item)
        ),
        rx.fragment()  # Return empty fragment for hidden items
    )


def image_list_panel() -> rx.Component:
    """Create the image list panel."""
    return rx.card(
        rx.vstack(
            rx.foreach(
                State.file_items,
                tree_item
            ),
            width="100%",
            align="start",
            spacing="0"
        ),
        width="400px",
        min_width="400px"
    )

def zoom_controls() -> rx.Component:
    """Create zoom control buttons."""
    return rx.hstack(
        rx.button(
            "−",
            on_click=State.zoom_out,
            size="1",
            variant="soft",
            disabled=State.zoom_level <= 0.125
        ),
        rx.button(
            "⅛×",
            on_click=State.set_zoom(0.125),
            size="1",
            variant=rx.cond(State.zoom_level == 0.125, "solid", "soft")
        ),
        rx.button(
            "¼×",
            on_click=State.set_zoom(0.25),
            size="1",
            variant=rx.cond(State.zoom_level == 0.25, "solid", "soft")
        ),
        rx.button(
            "½×",
            on_click=State.set_zoom(0.5),
            size="1",
            variant=rx.cond(State.zoom_level == 0.5, "solid", "soft")
        ),
        rx.button(
            "1×",
            on_click=State.set_zoom(1.0),
            size="1",
            variant=rx.cond(State.zoom_level == 1.0, "solid", "soft")
        ),
        rx.button(
            "2×",
            on_click=State.set_zoom(2.0),
            size="1",
            variant=rx.cond(State.zoom_level == 2.0, "solid", "soft")
        ),
        rx.button(
            "3×",
            on_click=State.set_zoom(3.0),
            size="1",
            variant=rx.cond(State.zoom_level == 3.0, "solid", "soft")
        ),
        rx.button(
            "4×",
            on_click=State.set_zoom(4.0),
            size="1",
            variant=rx.cond(State.zoom_level == 4.0, "solid", "soft")
        ),
        rx.button(
            "+",
            on_click=State.zoom_in,
            size="1",
            variant="soft",
            disabled=State.zoom_level >= 4.0
        ),
        spacing="1",
        align="center"
    )


def image_preview_panel() -> rx.Component:
    """Create the image preview panel."""
    return rx.card(
        rx.vstack(
            rx.cond(
                State.selected_image != "",
                rx.vstack(
                    rx.text(State.selected_image, size="2", weight="bold"),
                    rx.hstack(
                        rx.badge(State.image_format, color_scheme="blue"),
                        rx.badge(State.image_resolution, color_scheme="green"),
                        rx.badge(State.image_file_size, color_scheme="gray"),
                        rx.divider(orientation="vertical", size="2"),
                        zoom_controls(),
                        spacing="2",
                        align="center"
                    ),
                    rx.html(
                        f'<img src="{State.selected_image_data}" '
                        f'width="{State.image_width * State.zoom_level}px" '
                        f'height="{State.image_height * State.zoom_level}px" '
                        f'style="image-rendering: pixelated; image-rendering: -moz-crisp-edges; image-rendering: crisp-edges;" />'
                    ),
                    spacing="3",
                    align="start",
                    width="100%"
                ),
                rx.text("Select an image to preview", color="gray")
            ),
            width="100%",
            align="start"
        ),
    )
    
def directory_selector() -> rx.Component:
    """Create a directory selector component."""
    return rx.hstack(
        rx.button(
            rx.icon("arrow-up", size=16),
            on_click=State.go_up_directory,
            size="2",
            variant="soft",
            title="Go up one directory"
        ),
        rx.input(
            value=State.directory_input,
            on_change=State.set_directory_input,
            placeholder="Enter texture directory path...",
            width="400px",
            size="2"
        ),
        rx.button(
            "Change Directory",
            on_click=State.update_directory,
            size="2",
            variant="soft"
        ),
        spacing="2",
        width="100%"
    )

def index() -> rx.Component:
    """Main application page."""
    return rx.box(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.hstack(
                rx.heading("Texture Tool", size="4"),
                rx.button(
                    rx.icon("refresh-cw", size=20),
                    on_click=State.load_images,
                    variant="ghost",
                    size="3",
                    cursor="pointer"
                ),
                align="center",
                justify="start",
                width="100%",
                padding_bottom="2"
            ),
            directory_selector(),  # Add the directory selector here
            rx.hstack(
                image_list_panel(),
                image_preview_panel(),
                spacing="4",
                width="100%",
                align="start",
                height="calc(100vh - 120px)"
            ),
            padding="10px",
            spacing="4",
            width="100%",
            height="100vh"
        ),
        width="100vw",
        padding="4",
        on_mount=State.on_load
    )