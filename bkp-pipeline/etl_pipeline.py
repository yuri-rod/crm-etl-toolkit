import pandas as pd
import glob
import os
from datetime import datetime
import hashlib
from pathlib import Path
import logging
import json

# --- Basic Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    """Manages all script configurations."""
    def __init__(self, base_dir='.'):
        self.base_dir = Path(base_dir)
        self.input_dir = self.base_dir
        self.output_dir = self.base_dir / 'processed_data'
        self.log_dir = self.base_dir / 'logs'
        
        # --- Create necessary directories ---
        for a_dir in [self.output_dir, self.log_dir]:
            a_dir.mkdir(exist_ok=True)

        self.csv_pattern = "*.csv"
        self.cpf_column = 'CPF:'
        self.date_column = 'Submit Date (UTC)'
        self.output_separator = '|'

class CrmCleaner:
    """Handles CRM data cleaning and validation."""

    def process_date(self, date_str):
        if pd.isna(date_str) or not date_str:
            return pd.NaT
        try:
            return pd.to_datetime(date_str)
        except (ValueError, TypeError):
            return pd.NaT

    def clean_dataframe(self, df, cpf_column, date_column):
        if cpf_column not in df.columns:
            logging.warning(f"CPF column '{cpf_column}' not found. Skipping deduplication.")
            return df

        if date_column in df.columns:
            df['processed_submission_date'] = df[date_column].apply(self.process_date)
            df = df.sort_values('processed_submission_date', ascending=False)
        else:
            logging.warning(f"Date column '{date_column}' not found. Using record order for deduplication.")

        df.dropna(subset=[cpf_column], inplace=True)
        df.drop_duplicates(subset=[cpf_column], keep='first', inplace=True)

        if 'processed_submission_date' in df.columns:
            df.drop(columns=['processed_submission_date'], inplace=True)

        return df

class EtlPipeline:
    """Manages the complete ETL workflow."""
    def __init__(self, config):
        self.config = config
        self.cleaner = CrmCleaner()

    def _generate_unique_filename(self):
        """Creates a unique filename for the output."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_digest = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"unified_dataset_{timestamp}_{hash_digest}.csv"

    def run(self):
        """Executes the ETL pipeline."""
        logging.info("Starting ETL pipeline...")
        csv_files = list(self.config.input_dir.glob(self.config.csv_pattern))

        if not csv_files:
            logging.info("No CSV files found.")
            return

        logging.info(f"Found {len(csv_files)} CSV files.")
        
        dataframes = []
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path, sep=self.config.output_separator, low_memory=False)
                df['source_file'] = file_path.name
                dataframes.append(df)
                logging.info(f"Successfully processed '{file_path.name}'.")
            except Exception as e:
                logging.error(f"Error reading '{file_path.name}': {e}")

        if not dataframes:
            logging.info("No dataframes created. Exiting.")
            return

        full_df = pd.concat(dataframes, ignore_index=True)
        logging.info(f"Total records before deduplication: {len(full_df)}")

        cleaned_df = self.cleaner.clean_dataframe(full_df, self.config.cpf_column, self.config.date_column)
        logging.info(f"Total records after deduplication: {len(cleaned_df)}")

        output_filename = self._generate_unique_filename()
        output_path = self.config.output_dir / output_filename
        cleaned_df.to_csv(output_path, sep=self.config.output_separator, index=False)
        logging.info(f"Unified data saved to '{output_path}'.")
        
        self._generate_final_report(len(csv_files), len(full_df), len(cleaned_df), output_path)

    def _generate_final_report(self, files_processed, original_records, final_records, output_path):
        """Generates a summary of the ETL process."""
        report = {
            "files_processed": files_processed,
            "total_original_records": original_records,
            "total_final_records": final_records,
            "records_deduplicated": original_records - final_records,
            "output_file": str(output_path)
        }
        logging.info("--- ETL Pipeline Final Report ---")
        logging.info(json.dumps(report, indent=4))

if __name__ == "__main__":
    config = Config()
    pipeline = EtlPipeline(config)
    pipeline.run()