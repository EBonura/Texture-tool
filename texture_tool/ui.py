"""UI components for the Texture Tool application."""

import reflex as rx
from .state import State, FileItem


def should_show_item(item: FileItem) -> rx.Var:
    """Check if item should be shown based on parent folder expansion."""
    # For root level items (no parent), always show
    return rx.cond(
        item.parent == "",
        True,
        True  # For now, show all items - we can implement proper hiding later
    )


def folder_item(item: FileItem) -> rx.Component:
    """Create a folder button."""
    return rx.button(
        rx.hstack(
            rx.text("📁", font_size="16px", width="20px", text_align="center"),
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
        should_show_item(item),
        rx.cond(
            item.is_folder,
            folder_item(item),
            file_item(item)
        ),
        rx.fragment()
    )


def image_list_panel() -> rx.Component:
    """Create the image list panel."""
    return rx.vstack(
        rx.heading("Files", size="6"),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    State.file_items,
                    tree_item
                ),
                spacing="0",
                width="100%"
            ),
            height="600px",
            width="100%"
        ),
        width="450px",
        align="start",
        spacing="3"
    )


def image_preview_panel() -> rx.Component:
    """Create the image preview panel."""
    return rx.vstack(
        rx.heading("Preview", size="6"),
        rx.cond(
            State.selected_image != "",
            rx.vstack(
                rx.text(State.selected_image, size="2", weight="bold"),
                rx.hstack(
                    rx.badge(State.image_format, color_scheme="blue"),
                    rx.badge(State.image_resolution, color_scheme="green"),
                    rx.badge(State.image_file_size, color_scheme="gray"),
                    spacing="2"
                ),
                rx.image(
                    src=State.selected_image_data,
                    max_width="600px",
                    max_height="500px",
                    object_fit="contain"
                ),
                spacing="3",
                align="start"
            ),
            rx.text("Select an image to preview", color="gray")
        ),
        flex="1",
        align="start"
    )


def index() -> rx.Component:
    """Main application page."""
    return rx.box(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.hstack(
                rx.button(
                    "Refresh Images",
                    on_click=State.load_images,
                    color_scheme="blue",
                    size="2"
                ),
                justify="start",
                width="100%"
            ),
            rx.hstack(
                image_list_panel(),
                image_preview_panel(),
                spacing="4",
                width="100%",
                align="start",
                height="calc(100vh - 120px)"
            ),
            spacing="4",
            width="100%",
            height="100vh"
        ),
        width="100vw",
        padding="4",
        on_mount=State.on_load
    )