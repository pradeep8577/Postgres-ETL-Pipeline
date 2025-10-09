import reflex as rx
from typing import TypedDict, Any
import sqlalchemy as sa
from sqlalchemy import create_engine, text, inspect, MetaData, Table
import pandas as pd
import asyncio
import logging

logging.basicConfig(level=logging.INFO)


class DBConnection(TypedDict):
    url: str
    is_connected: bool
    tables: list[str]
    error_message: str | None


class PipelineState(rx.State):
    source_db: DBConnection = {
        "url": "postgresql://user:password@host:port/database",
        "is_connected": False,
        "tables": [],
        "error_message": None,
    }
    target_db: DBConnection = {
        "url": "sqlite:///target.db",
        "is_connected": False,
        "tables": [],
        "error_message": None,
    }
    source_table: str = ""
    target_table: str = ""
    source_columns: list[str] = []
    target_columns: list[str] = []
    column_mapping: dict[str, str] = {}
    transformations: list[dict[str, str]] = []
    pipeline_status: str = "Idle"
    pipeline_logs: list[str] = []
    is_running: bool = False

    async def _get_engine(self, url: str):
        try:
            return create_engine(url)
        except Exception as e:
            logging.exception(f"Failed to create engine for {url}: {e}")
            return None

    @rx.event
    async def connect_db(self, db_type: str):
        db_state_key = f"{db_type}_db"
        db_info: DBConnection = getattr(self, db_state_key)
        self._add_log(f"Connecting to {db_type.capitalize()} database...")
        engine = await self._get_engine(db_info["url"])
        if not engine:
            db_info["is_connected"] = False
            db_info["error_message"] = "Invalid connection URL."
            setattr(self, db_state_key, db_info)
            self._add_log(
                f"Error: Invalid connection URL for {db_type.capitalize()} DB."
            )
            return
        try:
            with engine.connect() as conn:
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                db_info["is_connected"] = True
                db_info["tables"] = tables
                db_info["error_message"] = None
                self._add_log(
                    f"Successfully connected to {db_type.capitalize()} DB. Found tables: {tables}"
                )
        except Exception as e:
            logging.exception(f"Error connecting to {db_type.capitalize()} DB: {e}")
            db_info["is_connected"] = False
            db_info["error_message"] = str(e)
            self._add_log(f"Error connecting to {db_type.capitalize()} DB: {e}")
        setattr(self, db_state_key, db_info)

    @rx.event
    async def fetch_columns(self, db_type: str, table_name: str):
        db_state_key = f"{db_type}_db"
        columns_state_key = f"{db_type}_columns"
        db_info: DBConnection = getattr(self, db_state_key)
        if not db_info["is_connected"] or not table_name:
            setattr(self, columns_state_key, [])
            if db_type == "source":
                self.column_mapping = {}
            return
        self._add_log(f"Fetching columns for {db_type}.{table_name}...")
        engine = await self._get_engine(db_info["url"])
        if not engine:
            self._add_log(f"Engine not available for {db_type}.")
            return
        try:
            inspector = inspect(engine)
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            setattr(self, columns_state_key, columns)
            self._add_log(f"Columns for {db_type}.{table_name}: {columns}")
            if db_type == "source":
                self.source_table = table_name
                self.column_mapping = {col: "" for col in columns}
            else:
                self.target_table = table_name
        except Exception as e:
            logging.exception(f"Error fetching columns for {db_type}.{table_name}: {e}")
            self._add_log(f"Error fetching columns for {db_type}.{table_name}: {e}")
            setattr(self, columns_state_key, [])

    @rx.event
    def set_source_url(self, url: str):
        self.source_db["url"] = url

    @rx.event
    def set_target_url(self, url: str):
        self.target_db["url"] = url

    @rx.event
    def set_source_table_event(self, table: str):
        self.source_table = table
        return PipelineState.fetch_columns("source", table)

    @rx.event
    def set_target_table_event(self, table: str):
        self.target_table = table
        return PipelineState.fetch_columns("target", table)

    @rx.event
    def set_column_mapping(self, source_col: str, target_col: str):
        self.column_mapping[source_col] = target_col
        self._add_log(
            f"Mapped source column '{source_col}' to target column '{target_col}'."
        )

    @rx.event
    def add_transformation(self):
        self.transformations.append({"column": "", "type": "uppercase"})
        self._add_log("Added new transformation rule.")

    @rx.event
    def update_transformation(self, index: int, field: str, value: str):
        self.transformations[index][field] = value
        self._add_log(f"Updated transformation at index {index}: {field} = {value}.")

    @rx.event
    def remove_transformation(self, index: int):
        self.transformations.pop(index)
        self._add_log(f"Removed transformation at index {index}.")

    def _add_log(self, message: str):
        self.pipeline_logs.insert(
            0, f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] {message}"
        )

    @rx.event(background=True)
    async def run_pipeline(self):
        async with self:
            self.is_running = True
            self.pipeline_status = "Running"
            self.pipeline_logs = []
            self._add_log("Pipeline starting...")
        await asyncio.sleep(1)
        source_engine = await self._get_engine(self.source_db["url"])
        target_engine = await self._get_engine(self.target_db["url"])
        if not source_engine or not target_engine:
            async with self:
                self.pipeline_status = "Failed"
                self._add_log("Pipeline failed: Database engine could not be created.")
                self.is_running = False
            return
        try:
            async with self:
                self._add_log(f"Extracting data from source table: {self.source_table}")
            df = pd.read_sql(f'SELECT * FROM "{self.source_table}"', source_engine)
            async with self:
                self._add_log(f"Extracted {len(df)} rows.")
            await asyncio.sleep(1)
            async with self:
                self._add_log("Applying transformations...")
            final_mapping = {
                k: v for k, v in self.column_mapping.items() if k in df.columns and v
            }
            df.rename(columns=final_mapping, inplace=True)
            async with self:
                self._add_log(f"Applied column mapping: {final_mapping}")
            df = df[[col for col in self.target_columns if col in df.columns]]
            for trans in self.transformations:
                col = trans.get("column")
                trans_type = trans.get("type")
                if col and col in df.columns:
                    if trans_type == "uppercase":
                        df[col] = df[col].str.upper()
                    elif trans_type == "lowercase":
                        df[col] = df[col].str.lower()
                    async with self:
                        self._add_log(f"Applied '{trans_type}' to column '{col}'.")
            await asyncio.sleep(1)
            async with self:
                self._add_log(f"Loading data into target table: {self.target_table}")
            df.to_sql(self.target_table, target_engine, if_exists="append", index=False)
            async with self:
                self._add_log(f"Successfully loaded {len(df)} rows.")
                self.pipeline_status = "Completed"
                self.is_running = False
        except Exception as e:
            logging.exception(f"Pipeline failed: {e}")
            async with self:
                self.pipeline_status = "Failed"
                self._add_log(f"Error during pipeline execution: {e}")
                self.is_running = False

    @rx.event
    def reset_pipeline(self):
        self.source_table = ""
        self.target_table = ""
        self.source_columns = []
        self.target_columns = []
        self.column_mapping = {}
        self.transformations = []
        self.pipeline_status = "Idle"
        self.pipeline_logs = []
        self.is_running = False