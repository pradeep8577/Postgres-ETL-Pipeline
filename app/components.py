import reflex as rx
from app.state import PipelineState


def card_header(icon: str, title: str, step: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="size-5 text-indigo-500"),
            class_name="flex items-center justify-center size-10 bg-indigo-100 rounded-full",
        ),
        rx.el.div(
            rx.el.h3(title, class_name="text-lg font-semibold text-gray-800"),
            rx.el.p(step, class_name="text-sm text-gray-500"),
            class_name="ml-4",
        ),
        class_name="flex items-center p-4 border-b border-gray-200",
    )


def db_connection_ui(db_type: str) -> rx.Component:
    db_info = getattr(PipelineState, f"{db_type}_db")
    on_change_fn = getattr(PipelineState, f"set_{db_type}_url")
    return rx.el.div(
        card_header(
            "database",
            f"{db_type.capitalize()} Database",
            "Step 1: Connect to your database",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Connection URL",
                    class_name="text-sm font-medium text-gray-700 mb-1",
                ),
                rx.el.input(
                    placeholder=f"e.g., postgresql://user:pass@host/db",
                    default_value=db_info.url,
                    on_change=on_change_fn,
                    class_name="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow",
                    disabled=PipelineState.is_running,
                ),
            ),
            rx.el.button(
                rx.icon("plug_zap", class_name="mr-2 size-4"),
                "Connect",
                on_click=lambda: PipelineState.connect_db(db_type),
                class_name="mt-4 flex items-center justify-center w-full bg-indigo-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm disabled:bg-gray-400",
                disabled=PipelineState.is_running,
            ),
            rx.cond(
                db_info.error_message,
                rx.el.div(
                    rx.icon(
                        "flag_triangle_right", class_name="mr-2 size-4 text-red-500"
                    ),
                    rx.el.span(
                        db_info.error_message, class_name="text-sm text-red-600"
                    ),
                    class_name="mt-2 flex items-center p-2 bg-red-50 border border-red-200 rounded-lg",
                ),
                rx.cond(
                    db_info.is_connected,
                    rx.el.div(
                        rx.icon(
                            "square_check", class_name="mr-2 size-4 text-green-500"
                        ),
                        rx.el.span(
                            "Connection successful!",
                            class_name="text-sm text-green-600",
                        ),
                        class_name="mt-2 flex items-center p-2 bg-green-50 border border-green-200 rounded-lg",
                    ),
                    None,
                ),
            ),
            class_name="p-4",
        ),
        class_name="bg-white rounded-xl border border-gray-200 shadow-md elevation-1 hover:elevation-2 transition-all duration-300",
    )


def table_selection_ui() -> rx.Component:
    return rx.el.div(
        card_header(
            "table_2", "Select Tables", "Step 2: Choose source and target tables"
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Source Table", class_name="text-sm font-medium text-gray-700 mb-1"
                ),
                rx.el.select(
                    rx.el.option("Select a table...", value="", disabled=True),
                    rx.foreach(
                        PipelineState.source_db.tables,
                        lambda table: rx.el.option(table, value=table),
                    ),
                    value=PipelineState.source_table,
                    on_change=PipelineState.set_source_table_event,
                    class_name="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                    disabled=~PipelineState.source_db.is_connected
                    | PipelineState.is_running,
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.el.label(
                    "Target Table", class_name="text-sm font-medium text-gray-700 mb-1"
                ),
                rx.el.select(
                    rx.el.option("Select a table...", value="", disabled=True),
                    rx.foreach(
                        PipelineState.target_db.tables,
                        lambda table: rx.el.option(table, value=table),
                    ),
                    value=PipelineState.target_table,
                    on_change=PipelineState.set_target_table_event,
                    class_name="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                    disabled=~PipelineState.target_db.is_connected
                    | PipelineState.is_running,
                ),
                class_name="w-full",
            ),
            class_name="p-4 grid grid-cols-1 md:grid-cols-2 gap-4",
        ),
        class_name="bg-white rounded-xl border border-gray-200 shadow-md elevation-1 hover:elevation-2 transition-all duration-300",
    )


def column_mapping_ui() -> rx.Component:
    return rx.el.div(
        card_header(
            "arrow-right-left", "Map Columns", "Step 3: Define column mappings"
        ),
        rx.el.div(
            rx.cond(
                PipelineState.source_columns.length() > 0,
                rx.el.div(
                    rx.foreach(
                        PipelineState.source_columns,
                        lambda col: rx.el.div(
                            rx.el.div(
                                rx.el.span(
                                    col, class_name="font-semibold text-gray-700"
                                ),
                                class_name="w-1/3 flex items-center",
                            ),
                            rx.icon("arrow-right", class_name="mx-4 text-gray-400"),
                            rx.el.select(
                                rx.el.option("Select Target Column", value=""),
                                rx.foreach(
                                    PipelineState.target_columns,
                                    lambda target_col: rx.el.option(
                                        target_col, value=target_col
                                    ),
                                ),
                                value=PipelineState.column_mapping[col],
                                on_change=lambda val: PipelineState.set_column_mapping(
                                    col, val
                                ),
                                class_name="w-2/3 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500",
                                disabled=PipelineState.is_running,
                            ),
                            class_name="flex items-center justify-between p-2 my-1 bg-gray-50 rounded-lg",
                            key=col,
                        ),
                    ),
                    class_name="space-y-2",
                ),
                rx.el.div(
                    rx.el.p(
                        "Select source and target tables to see columns.",
                        class_name="text-sm text-gray-500",
                    ),
                    class_name="flex items-center justify-center h-24 text-center",
                ),
            ),
            class_name="p-4",
        ),
        class_name="bg-white rounded-xl border border-gray-200 shadow-md elevation-1 hover:elevation-2 transition-all duration-300",
    )


def transformations_ui() -> rx.Component:
    return rx.el.div(
        card_header("disc_2", "Transform Data", "Step 4: Add data transformations"),
        rx.el.div(
            rx.foreach(
                PipelineState.transformations,
                lambda trans, index: rx.el.div(
                    rx.el.select(
                        rx.el.option("Select Column", value="", disabled=True),
                        rx.foreach(
                            PipelineState.source_columns,
                            lambda col: rx.el.option(col, value=col),
                        ),
                        value=trans["column"],
                        on_change=lambda val: PipelineState.update_transformation(
                            index, "column", val
                        ),
                        class_name="w-1/3 p-2 border border-gray-300 rounded-lg",
                        disabled=PipelineState.is_running,
                    ),
                    rx.el.select(
                        rx.el.option("Uppercase", value="uppercase"),
                        rx.el.option("Lowercase", value="lowercase"),
                        value=trans["type"],
                        on_change=lambda val: PipelineState.update_transformation(
                            index, "type", val
                        ),
                        class_name="w-1/3 p-2 border border-gray-300 rounded-lg",
                        disabled=PipelineState.is_running,
                    ),
                    rx.el.button(
                        rx.icon("trash-2", class_name="size-4"),
                        on_click=lambda: PipelineState.remove_transformation(index),
                        class_name="text-red-500 hover:text-red-700 p-2 rounded-md hover:bg-red-100",
                        disabled=PipelineState.is_running,
                    ),
                    class_name="flex items-center justify-between space-x-2 p-2 bg-gray-50 rounded-lg",
                    key=index,
                ),
            ),
            rx.el.button(
                rx.icon("plus", class_name="mr-2 size-4"),
                "Add Transformation",
                on_click=PipelineState.add_transformation,
                class_name="mt-4 flex items-center justify-center w-full border-2 border-dashed border-gray-300 text-gray-600 font-semibold py-2 px-4 rounded-lg hover:bg-gray-100 hover:border-gray-400 transition-colors",
                disabled=PipelineState.is_running,
            ),
            class_name="p-4",
        ),
        class_name="bg-white rounded-xl border border-gray-200 shadow-md elevation-1 hover:elevation-2 transition-all duration-300",
    )


def pipeline_controls_ui() -> rx.Component:
    return rx.el.div(
        card_header("circle_play", "Execute Pipeline", "Step 5: Run the data transfer"),
        rx.el.div(
            rx.el.button(
                rx.cond(
                    PipelineState.is_running,
                    rx.fragment(rx.spinner(class_name="mr-2"), "Running..."),
                    rx.fragment(rx.icon("play", class_name="mr-2"), "Run Pipeline"),
                ),
                on_click=PipelineState.run_pipeline,
                class_name="w-full flex items-center justify-center bg-green-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-green-700 transition-colors shadow-lg elevation-3 hover:elevation-5 disabled:bg-gray-400",
                disabled=PipelineState.is_running,
            ),
            rx.el.button(
                rx.icon("rotate-cw", class_name="mr-2"),
                "Reset",
                on_click=PipelineState.reset_pipeline,
                class_name="w-full flex items-center justify-center mt-2 bg-gray-200 text-gray-800 font-semibold py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors",
                disabled=PipelineState.is_running,
            ),
            class_name="p-4",
        ),
        class_name="bg-white rounded-xl border border-gray-200 shadow-md elevation-1 hover:elevation-2 transition-all duration-300",
    )


def status_and_logs_ui() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Pipeline Status", class_name="text-lg font-semibold text-gray-800"
                ),
                rx.el.div(
                    rx.el.span(
                        rx.match(
                            PipelineState.pipeline_status,
                            (
                                "Idle",
                                rx.icon("coffee", class_name="mr-2 text-gray-500"),
                            ),
                            ("Running", rx.spinner(class_name="mr-2 text-indigo-500")),
                            (
                                "Completed",
                                rx.icon(
                                    "square_check", class_name="mr-2 text-green-500"
                                ),
                            ),
                            (
                                "Failed",
                                rx.icon("circle_x", class_name="mr-2 text-red-500"),
                            ),
                            rx.icon("info", class_name="mr-2"),
                        )
                    ),
                    rx.el.span(
                        PipelineState.pipeline_status,
                        class_name=rx.match(
                            PipelineState.pipeline_status,
                            ("Idle", "text-gray-600 font-bold text-lg"),
                            ("Running", "text-indigo-600 font-bold text-lg"),
                            ("Completed", "text-green-600 font-bold text-lg"),
                            ("Failed", "text-red-600 font-bold text-lg"),
                            "text-gray-600 font-bold text-lg",
                        ),
                    ),
                    class_name="flex items-center mt-2",
                ),
            ),
            class_name="p-4 border-b border-gray-200",
        ),
        rx.el.div(
            rx.el.h3(
                "Logs", class_name="text-md font-semibold text-gray-700 mb-2 px-4"
            ),
            rx.el.div(
                rx.foreach(
                    PipelineState.pipeline_logs,
                    lambda log: rx.el.p(
                        log,
                        class_name="text-xs text-gray-600 font-mono p-1 border-b border-gray-100",
                    ),
                ),
                class_name="h-64 overflow-y-auto bg-gray-50 rounded-b-lg p-2",
            ),
            class_name="pt-4",
        ),
        class_name="bg-white rounded-xl border border-gray-200 shadow-md elevation-1",
    )