import pandas as pd
import glob
import os
from datetime import datetime
import hashlib
from pathlib import Path
import logging
import json

# Basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    """Manages all script configurations."""
    def __init__(self, base_dir='.'):
        self.base_dir = Path(base_dir)
        self.input_dir = self.base_dir
        self.output_dir = self.base_dir / 'processed_data'
        self.log_dir = self.base_dir / 'logs'
        self.backup_dir = self.base_dir / 'backups'
        
        # Create directories if they don't exist
        self.output_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

        # File patterns and column names
        self.csv_pattern = "*.csv"
        self.cpf_column = 'CPF:'
        self.date_column = 'Submit Date (UTC)'
        self.output_separator = '|'

class CrmCleaner:
    """Handles the cleaning and validation of CRM data."""

    def process_date(self, date_str):
        """Converts a date string to a datetime object."""
        if pd.isna(date_str) or date_str == '':
            return pd.NaT
        try:
            return pd.to_datetime(date_str)
        except (ValueError, TypeError):
            return pd.NaT

    def clean_dataframe(self, df, cpf_column, date_column):
        """Deduplicates a dataframe based on CPF and submission date."""
        if cpf_column not in df.columns:
            logging.warning(f"CPF column '{cpf_column}' not found. Skipping deduplication.")
            return df

        # Process submission dates for sorting
        if date_column in df.columns:
            df['processed_submission_date'] = df[date_column].apply(self.process_date)
            df.sort_values('processed_submission_date', ascending=False, inplace=True)
        else:
            logging.warning(f"Date column '{date_column}' not found. Using record order for deduplication.")

        # Remove null CPFs and deduplicate
        df.dropna(subset=[cpf_column], inplace=True)
        df.drop_duplicates(subset=[cpf_column], keep='first', inplace=True)

        if 'processed_submission_date' in df.columns:
            df.drop(columns=['processed_submission_date'], inplace=True)

        return df

class EtlPipeline:
    """Manages the entire ETL workflow."""
    def __init__(self, config):
        self.config = config
        self.cleaner = CrmCleaner()

    def _generate_unique_filename(self):
        """Generates a unique filename for the output file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_obj = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"unified_dataset_{timestamp}_{hash_obj}.csv"

    def run(self):
        """Executes the complete ETL pipeline."""
        logging.info("Starting ETL pipeline...")
        
        csv_files = glob.glob(str(self.config.input_dir / self.config.csv_pattern))
        if not csv_files:
            logging.info("No CSV files found to process.")
            return

        logging.info(f"Found {len(csv_files)} CSV files to process.")
        
        all_dataframes = []
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path, sep=self.config.output_separator, low_memory=False)
                df['source_file'] = Path(file_path).name
                all_dataframes.append(df)
                logging.info(f"Successfully loaded and processed '{Path(file_path).name}'.")
            except Exception as e:
                logging.error(f"Error reading '{Path(file_path).name}': {e}")

        if not all_dataframes:
            logging.info("No dataframes were created. Exiting.")
            return

        # Concatenate and clean the data
        full_df = pd.concat(all_dataframes, ignore_index=True)
        logging.info(f"Total records before deduplication: {len(full_df)}")

        cleaned_df = self.cleaner.clean_dataframe(full_df, self.config.cpf_column, self.config.date_column)
        logging.info(f"Total records after deduplication: {len(cleaned_df)}")

        # Save the unified and cleaned dataset
        output_filename = self._generate_unique_filename()
        output_path = self.config.output_dir / output_filename
        cleaned_df.to_csv(output_path, sep=self.config.output_separator, index=False)
        logging.info(f"Unified and cleaned data saved to '{output_path}'.")
        
        # Final report
        self._generate_final_report(len(csv_files), len(full_df), len(cleaned_df), output_path)

    def _generate_final_report(self, files_processed, original_records, final_records, output_path):
        """Generates and prints a summary of the ETL process."""
        report = {
            "files_processed": files_processed,
            "total_original_records": original_records,
            "total_final_records": final_records,
            "records_deduplicated": original_records - final_records,
            "output_file": str(output_path)
        }
        logging.info("ETL Pipeline Final Report:")
        logging.info(json.dumps(report, indent=4))

if __name__ == "__main__":
    config = Config()
    pipeline = EtlPipeline(config)
    pipeline.run()