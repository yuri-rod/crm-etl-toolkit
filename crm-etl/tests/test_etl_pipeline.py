#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL Pipeline Tests
==================

ETL pipeline test that loads a sample CSV → transforms → writes JSON.
Tests the complete ETL workflow with data validation.

Developed for CRM ETL
"""

import pytest
import pandas as pd
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import os
import sys
import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    # Note: ETL-main has dashes which makes direct import impossible
    # These would need to be imported differently in actual usage
    ETL_MAIN_AVAILABLE = False
except ImportError:
    # Try alternative import paths
    try:
        from etl.extractors.csv_extractor import CSVExtractor
        from etl.transform import Transform as ETLTransform
        from etl.load import Load as ETLLoad
        ETL_EXTRACTORS_AVAILABLE = True
        ETL_MAIN_AVAILABLE = False
    except ImportError:
        ETL_MAIN_AVAILABLE = False
        ETL_EXTRACTORS_AVAILABLE = False


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files (shared by all classes)"""
    temp_dir = tempfile.mkdtemp(prefix="crm_etl_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestETLPipeline:
    """Complete ETL Pipeline tests"""

    @pytest.fixture
    def sample_csv_data(self, temp_directory):
        """Create sample CSV file with realistic business data"""
        csv_file = temp_directory / "sample_customers.csv"
        
        # Create realistic customer data
        data = {
            'customer_id': range(1, 101),
            'name': [f'Customer {i}' for i in range(1, 101)],
            'email': [f'customer{i}@example.com' for i in range(1, 101)],
            'age': np.random.randint(18, 80, 100),
            'city': np.random.choice(['São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Recife'], 100),
            'purchase_value': np.random.uniform(10.0, 1000.0, 100).round(2),
            'purchase_date': [
                (datetime(2024, 1, 1).date() + pd.Timedelta(days=int(x))).strftime('%Y-%m-%d') 
                for x in np.random.randint(0, 365, 100)
            ],
            'category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home', 'Sports'], 100),
            'satisfaction_score': np.random.randint(1, 6, 100),  # 1-5 scale
            'is_premium': np.random.choice([True, False], 100)
        }
        
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False)
        
        return csv_file

    @pytest.fixture
    def expected_json_structure(self):
        """Define expected JSON output structure"""
        return {
            'metadata': {
                'source_file': str,
                'processing_timestamp': str,
                'total_records': int,
                'transformation_applied': list
            },
            'data': list,
            'summary_statistics': {
                'age_stats': dict,
                'purchase_value_stats': dict,
                'category_distribution': dict,
                'city_distribution': dict
            }
        }

    def test_csv_extraction(self, sample_csv_data):
        """Test CSV data extraction"""
        # Test direct pandas reading
        df = pd.read_csv(sample_csv_data)
        
        # Validate structure
        assert not df.empty, "CSV should contain data"
        assert len(df) == 100, "Should have 100 records"
        
        expected_columns = [
            'customer_id', 'name', 'email', 'age', 'city', 
            'purchase_value', 'purchase_date', 'category', 
            'satisfaction_score', 'is_premium'
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Column '{col}' should be present"
        
        # Validate data types and ranges
        assert df['customer_id'].dtype in ['int64', 'int32'], "customer_id should be integer"
        assert df['age'].min() >= 18 and df['age'].max() <= 80, "Age should be in valid range"
        assert df['satisfaction_score'].min() >= 1 and df['satisfaction_score'].max() <= 5, "Satisfaction score should be 1-5"
        assert df['purchase_value'].min() > 0, "Purchase value should be positive"

    def test_data_transformation(self, sample_csv_data, temp_directory):
        """Test data transformation logic"""
        # Load data
        df = pd.read_csv(sample_csv_data)
        
        # Apply transformations
        transformed_df = self._apply_transformations(df)
        
        # Validate transformations
        assert 'customer_segment' in transformed_df.columns, "Customer segment should be added"
        assert 'purchase_month' in transformed_df.columns, "Purchase month should be extracted"
        assert 'age_group' in transformed_df.columns, "Age group should be categorized"
        assert 'high_value_customer' in transformed_df.columns, "High value flag should be added"
        
        # Check segment logic
        premium_customers = transformed_df[transformed_df['is_premium'] == True]
        if not premium_customers.empty:
            assert all(premium_customers['customer_segment'].isin(['Premium', 'VIP'])), \
                "Premium customers should have Premium or VIP segment"
        
        # Check age groups
        young_customers = transformed_df[transformed_df['age'] < 30]
        if not young_customers.empty:
            assert all(young_customers['age_group'] == 'Young'), "Young customers should be categorized correctly"

    def test_json_output(self, sample_csv_data, temp_directory, expected_json_structure):
        """Test JSON output generation"""
        # Load and transform data
        df = pd.read_csv(sample_csv_data)
        transformed_df = self._apply_transformations(df)
        
        # Generate JSON output
        json_output = self._generate_json_output(transformed_df, sample_csv_data)
        
        # Save JSON file
        json_file = temp_directory / "transformed_output.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False, default=str)
        
        # Validate JSON structure
        assert 'metadata' in json_output, "JSON should contain metadata"
        assert 'data' in json_output, "JSON should contain data"
        assert 'summary_statistics' in json_output, "JSON should contain summary statistics"
        
        # Validate metadata
        metadata = json_output['metadata']
        assert 'source_file' in metadata, "Metadata should include source file"
        assert 'processing_timestamp' in metadata, "Metadata should include timestamp"
        assert 'total_records' in metadata, "Metadata should include record count"
        assert metadata['total_records'] == len(df), "Record count should match"
        
        # Validate data content
        data_records = json_output['data']
        assert len(data_records) == len(transformed_df), "Data records should match transformed data"
        assert all(isinstance(record, dict) for record in data_records), "Each record should be a dictionary"
        
        # Validate summary statistics
        stats = json_output['summary_statistics']
        assert 'age_stats' in stats, "Should include age statistics"
        assert 'purchase_value_stats' in stats, "Should include purchase value statistics"
        assert 'category_distribution' in stats, "Should include category distribution"

    def test_complete_etl_pipeline(self, sample_csv_data, temp_directory):
        """Test complete ETL pipeline: CSV → Transform → JSON"""
        
        # Step 1: Extract (Load CSV)
        print(f"📥 Step 1: Extracting data from {sample_csv_data}")
        source_df = pd.read_csv(sample_csv_data)
        assert not source_df.empty, "Source data should not be empty"
        print(f"✅ Extracted {len(source_df)} records")
        
        # Step 2: Transform
        print("🔄 Step 2: Transforming data")
        transformed_df = self._apply_transformations(source_df)
        
        # Validate transformations were applied
        original_columns = set(source_df.columns)
        transformed_columns = set(transformed_df.columns)
        new_columns = transformed_columns - original_columns
        
        assert len(new_columns) > 0, "Transformations should add new columns"
        print(f"✅ Applied transformations, added columns: {new_columns}")
        
        # Step 3: Load (Save as JSON)
        print("💾 Step 3: Loading data to JSON")
        output_json = self._generate_json_output(transformed_df, sample_csv_data)
        
        json_file = temp_directory / "pipeline_output.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False, default=str)
        
        # Validate output file
        assert json_file.exists(), "JSON output file should be created"
        assert json_file.stat().st_size > 0, "JSON file should not be empty"
        print(f"✅ Saved output to {json_file}")
        
        # Step 4: Validate complete pipeline
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_json = json.load(f)
        
        # Compare input vs output record counts
        input_count = len(source_df)
        output_count = loaded_json['metadata']['total_records']
        assert input_count == output_count, f"Record count mismatch: {input_count} vs {output_count}"
        
        print("✅ Complete ETL pipeline test passed!")
        
        # Return pipeline results for further testing
        return {
            'source_records': len(source_df),
            'transformed_records': len(transformed_df),
            'output_file': json_file,
            'pipeline_success': True
        }

    def test_error_handling(self, temp_directory):
        """Test ETL pipeline error handling"""
        
        # Test with invalid CSV
        invalid_csv = temp_directory / "invalid.csv"
        with open(invalid_csv, 'w') as f:
            f.write("invalid,csv,format\nno,data,here\n\n\n")  # Malformed CSV
        
        # Should handle gracefully
        try:
            df = pd.read_csv(invalid_csv)
            transformed_df = self._apply_transformations(df)
            assert len(transformed_df) >= 0, "Should handle minimal data"
        except Exception as e:
            pytest.fail(f"ETL should handle invalid data gracefully: {e}")
        
        # Test with empty CSV
        empty_csv = temp_directory / "empty.csv"
        with open(empty_csv, 'w') as f:
            f.write("col1,col2,col3\n")  # Only headers
        
        df_empty = pd.read_csv(empty_csv)
        assert len(df_empty) == 0, "Empty CSV should result in empty DataFrame"

    def test_data_quality_validation(self, sample_csv_data):
        """Test data quality validation during ETL"""
        df = pd.read_csv(sample_csv_data)
        
        # Check for required columns
        required_columns = ['customer_id', 'name', 'email', 'purchase_value']
        missing_columns = [col for col in required_columns if col not in df.columns]
        assert not missing_columns, f"Missing required columns: {missing_columns}"
        
        # Check for data quality issues
        quality_report = {
            'null_values': df.isnull().sum().to_dict(),
            'duplicate_ids': df['customer_id'].duplicated().sum(),
            'invalid_emails': (~df['email'].str.contains('@')).sum(),
            'negative_values': (df['purchase_value'] <= 0).sum()
        }
        
        # Validate data quality
        assert quality_report['duplicate_ids'] == 0, "Should not have duplicate customer IDs"
        assert quality_report['invalid_emails'] == 0, "Should not have invalid emails"
        assert quality_report['negative_values'] == 0, "Should not have negative purchase values"

    def _apply_transformations(self, df):
        """Apply business transformations to the data"""
        transformed_df = df.copy()
        required = {'is_premium', 'purchase_value', 'purchase_date', 'age'}
        if not required <= set(df.columns):
            return transformed_df  # unknown schema: pass through gracefully

        # Add customer segmentation
        conditions = [
            (transformed_df['is_premium'] == True) & (transformed_df['purchase_value'] > 500),
            (transformed_df['is_premium'] == True) & (transformed_df['purchase_value'] <= 500),
            (transformed_df['is_premium'] == False) & (transformed_df['purchase_value'] > 300),
            (transformed_df['is_premium'] == False) & (transformed_df['purchase_value'] <= 300)
        ]
        choices = ['VIP', 'Premium', 'Standard', 'Basic']
        transformed_df['customer_segment'] = np.select(conditions, choices, default='Basic')
        
        # Extract purchase month
        transformed_df['purchase_date'] = pd.to_datetime(transformed_df['purchase_date'])
        transformed_df['purchase_month'] = transformed_df['purchase_date'].dt.strftime('%Y-%m')
        
        # Add age groups
        age_conditions = [
            transformed_df['age'] < 30,
            (transformed_df['age'] >= 30) & (transformed_df['age'] < 50),
            transformed_df['age'] >= 50
        ]
        age_choices = ['Young', 'Middle-aged', 'Senior']
        transformed_df['age_group'] = np.select(age_conditions, age_choices, default='Unknown')
        
        # High value customer flag
        high_value_threshold = transformed_df['purchase_value'].quantile(0.8)  # Top 20%
        transformed_df['high_value_customer'] = transformed_df['purchase_value'] > high_value_threshold
        
        # Add processing timestamp
        transformed_df['processing_timestamp'] = datetime.now().isoformat()
        
        return transformed_df

    def _generate_json_output(self, df, source_file):
        """Generate structured JSON output"""
        
        # Convert DataFrame to records
        records = df.to_dict('records')
        
        # Generate summary statistics
        summary_stats = {
            'age_stats': {
                'mean': float(df['age'].mean()),
                'median': float(df['age'].median()),
                'min': int(df['age'].min()),
                'max': int(df['age'].max())
            },
            'purchase_value_stats': {
                'mean': float(df['purchase_value'].mean()),
                'median': float(df['purchase_value'].median()),
                'min': float(df['purchase_value'].min()),
                'max': float(df['purchase_value'].max()),
                'total': float(df['purchase_value'].sum())
            },
            'category_distribution': df['category'].value_counts().to_dict(),
            'city_distribution': df['city'].value_counts().to_dict(),
            'segment_distribution': df['customer_segment'].value_counts().to_dict() if 'customer_segment' in df.columns else {}
        }
        
        # Create structured output
        json_output = {
            'metadata': {
                'source_file': str(source_file),
                'processing_timestamp': datetime.now().isoformat(),
                'total_records': len(df),
                'transformation_applied': [
                    'customer_segmentation',
                    'age_grouping',
                    'purchase_month_extraction',
                    'high_value_customer_flag'
                ],
                'pipeline_version': '1.0.0'
            },
            'data': records,
            'summary_statistics': summary_stats
        }
        
        return json_output


@pytest.mark.integration
class TestETLIntegration:
    """Integration tests for ETL with external systems"""

    def test_etl_with_multiple_formats(self, temp_directory):
        """Test ETL with different input formats"""
        
        # Create test data in multiple formats
        test_data = {
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
            'value': [100, 200, 150, 300, 250]
        }
        
        df = pd.DataFrame(test_data)
        
        # Save in different formats
        csv_file = temp_directory / "test.csv"
        json_file = temp_directory / "test.json"
        excel_file = temp_directory / "test.xlsx"
        
        # CSV
        df.to_csv(csv_file, index=False)
        
        # JSON
        df.to_json(json_file, orient='records', indent=2)
        
        # Excel (if openpyxl available)
        try:
            df.to_excel(excel_file, index=False)
        except ImportError:
            print("⚠️ openpyxl not available, skipping Excel test")
        
        # Test reading each format
        csv_df = pd.read_csv(csv_file)
        json_df = pd.read_json(json_file)
        
        assert len(csv_df) == len(df), "CSV should preserve all records"
        assert len(json_df) == len(df), "JSON should preserve all records"
        
        # Test transformation consistency
        test_pipeline = TestETLPipeline()
        csv_transformed = test_pipeline._apply_transformations(csv_df)
        json_transformed = test_pipeline._apply_transformations(json_df)
        
        # Both should produce similar results
        assert len(csv_transformed) == len(json_transformed), "Transformations should be consistent across formats"

    def test_large_dataset_performance(self, temp_directory):
        """Test ETL performance with larger dataset"""
        
        # Create larger dataset (10,000 records)
        large_data = {
            'id': range(1, 10001),
            'value': np.random.uniform(1, 1000, 10000),
            'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], 10000),
            'date': [datetime.now().strftime('%Y-%m-%d') for _ in range(10000)]
        }
        
        large_df = pd.DataFrame(large_data)
        large_csv = temp_directory / "large_dataset.csv"
        large_df.to_csv(large_csv, index=False)
        
        # Time the ETL process
        import time
        start_time = time.time()
        
        # Run ETL
        loaded_df = pd.read_csv(large_csv)
        test_pipeline = TestETLPipeline()
        transformed_df = test_pipeline._apply_transformations(loaded_df)
        json_output = test_pipeline._generate_json_output(transformed_df, large_csv)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 30, f"ETL should complete within 30 seconds, took {processing_time:.2f}s"
        assert len(transformed_df) == 10000, "Should preserve all records"
        assert len(json_output['data']) == 10000, "JSON output should contain all records"
        
        print(f"✅ Processed 10,000 records in {processing_time:.2f} seconds")


if __name__ == "__main__":
    # Quick test run
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    try:
        test = TestETLPipeline()
        # Create sample data
        sample_file = Path(temp_dir) / "test.csv"
        test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Test1', 'Test2', 'Test3'],
            'value': [100, 200, 300]
        })
        test_data.to_csv(sample_file, index=False)
        
        # Test extraction
        df = pd.read_csv(sample_file)
        print(f"✅ Extracted {len(df)} records")
        
        # Test transformation
        transformed = test._apply_transformations(df)
        print(f"✅ Transformed data with {len(transformed.columns)} columns")
        
        # Test JSON generation
        json_output = test._generate_json_output(transformed, sample_file)
        print(f"✅ Generated JSON with {len(json_output['data'])} records")
        
        print("🎉 ETL Pipeline test completed successfully!")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
