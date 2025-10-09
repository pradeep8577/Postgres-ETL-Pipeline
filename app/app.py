import reflex as rx
from app.state import PipelineState
from app.components import (
    db_connection_ui,
    table_selection_ui,
    column_mapping_ui,
    transformations_ui,
    pipeline_controls_ui,
    status_and_logs_ui,
)


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.header(
                rx.el.div(
                    rx.icon("waypoints", class_name="size-8 text-indigo-500"),
                    rx.el.h1(
                        "Data Pipeline Orchestrator",
                        class_name="text-3xl font-bold text-gray-800 ml-4",
                    ),
                    class_name="flex items-center",
                ),
                rx.el.p(
                    "Visually configure and execute your ETL pipelines.",
                    class_name="text-gray-500 mt-2",
                ),
                class_name="text-center py-12 bg-white border-b border-gray-200",
            ),
            rx.el.div(
                rx.el.div(
                    db_connection_ui("source"),
                    db_connection_ui("target"),
                    class_name="grid grid-cols-1 lg:grid-cols-2 gap-8",
                ),
                rx.el.div(table_selection_ui(), class_name="mt-8"),
                rx.el.div(column_mapping_ui(), class_name="mt-8"),
                rx.el.div(transformations_ui(), class_name="mt-8"),
                rx.el.div(pipeline_controls_ui(), class_name="mt-8"),
                rx.el.div(status_and_logs_ui(), class_name="mt-8"),
                class_name="max-w-4xl mx-auto p-4 md:p-8",
            ),
            class_name="min-h-screen",
        ),
        class_name="font-['JetBrains_Mono'] bg-gray-50",
    )


app = rx.App(
    theme=rx.theme(appearance="light", accent_color="indigo"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, title="Data Pipeline Orchestrator")