import reflex as rx

config = rx.Config(
    app_name="texture_tool",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)