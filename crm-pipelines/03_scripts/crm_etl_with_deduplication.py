#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced CRM Data ETL Processor with Deduplication
===================================================
Comprehensive ETL pipeline with integrated duplicate removal functionality.

NEW FEATURES:
- Automatic duplicate detection and removal based on email
- Quality-based record selection (completeness, recency, valuation amount)
- Detailed deduplication report
- Preserves best quality data from duplicates

Author: AI Assistant
Date: September 4, 2025
"""

import json
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
from dataclasses import dataclass
import unicodedata

# Excel formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

warnings.filterwarnings('ignore')

@dataclass
class DataQualityMetrics:
    """Data quality metrics for reporting"""
    total_records: int
    complete_records: int
    duplicates_found: int
    duplicates_removed: int  # NEW
    invalid_emails: int
    invalid_phones: int
    missing_critical_fields: int
    data_completeness_score: float
    deduplication_rate: float  # NEW

@dataclass
class DeduplicationStats:
    """Statistics from deduplication process"""
    original_count: int
    final_count: int
    removed_count: int
    unique_emails_with_duplicates: int
    max_duplicates_per_email: int
    avg_duplicates_per_email: float

class EnhancedCRMProcessor:
    """Enhanced ETL processor with deduplication capabilities"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.field_translations = self._create_field_mapping()
        self.market_translations = self._create_market_mapping()
        self.stage_translations = self._create_stage_mapping()
        self.quality_metrics = {}
        self.consolidation_report = []
        self.deduplication_stats = {}  # NEW
        
    def _create_field_mapping(self) -> Dict[str, str]:
        """Create comprehensive Portuguese to English field mapping"""
        return {
            # Company/Startup Fields
            'ID': 'company_id',
            'Nome da Startup': 'company_name',
            'Nome_Empresa': 'company_name',
            'Site': 'website',
            'Website': 'website',
            'Cidade/Estado': 'location',
            'Cidade': 'city',
            'Estado': 'state',
            'Estágio Operacional': 'operational_stage',
            'Estagio_Operacional': 'operational_stage',
            'Modelo de Negócio': 'business_model',
            'Modelo_Negocio': 'business_model',
            'Mercado': 'market_sector',
            'Estágio de Investimento': 'investment_stage',
            'Estagio_Investimento': 'investment_stage',
            
            # Contact Fields
            'Nome do Respondente': 'contact_name',
            'Email': 'email',
            'Telefone': 'phone',
            
            # Financial Fields
            'Valuation': 'valuation_amount',
            'Resultado_Valuation': 'valuation_amount',
            'MRR': 'monthly_recurring_revenue',
            'LTM': 'last_twelve_months_revenue',
            'Faturamento_LTM': 'last_twelve_months_revenue',
            'Captação': 'fundraising_interest',
            'Pretende_Captar': 'fundraising_interest',
            'Tipo de Valuation': 'valuation_type',
            'Data de Valuation': 'valuation_date',
            'Horário de Valuation': 'valuation_time',
            
            # Payment Fields
            'paid': 'payment_status',
            'amount': 'payment_amount',
            'type': 'service_type',
            'date': 'payment_date',
            
            # GPT/Analytics Fields
            'createdAt': 'created_date',
            'name': 'user_name',
            'consent': 'consent_given',
            'questions': 'questions_asked',
            
            # Metrics Fields
            'totalValuations': 'total_valuations',
            'averageValuation': 'average_valuation',
            'averageRevenue': 'average_revenue',
            'totalPaidValuations': 'total_paid_valuations',
            'totalPaidValue': 'total_paid_value'
        }
    
    def _create_market_mapping(self) -> Dict[str, str]:
        """Map Portuguese market sectors to English"""
        return {
            'Edtech': 'Education Technology',
            'Fintech': 'Financial Technology',
            'Healthtech': 'Healthcare Technology',
            'Foodtech': 'Food Technology',
            'Martech': 'Marketing Technology',
            'Proptech': 'Property Technology',
            'Insurtech': 'Insurance Technology',
            'Agtech': 'Agriculture Technology',
            'Telecom': 'Telecommunications',
            'Entretenimento': 'Entertainment',
            'Outros': 'Other'
        }
    
    def _create_stage_mapping(self) -> Dict[str, str]:
        """Map Portuguese operational stages to English"""
        return {
            'Planejamento': 'Planning',
            'Validação': 'Validation',
            'Tração': 'Traction',
            'Operação': 'Operation',
            'Pré-Seed': 'Pre-Seed',
            'Seed': 'Seed',
            'Série A': 'Series A',
            'Série B': 'Series B',
            'Investimento Anjo': 'Angel Investment',
            'Aceleração': 'Acceleration',
            'Nenhuma das Anteriores': 'None of the Above'
        }
    
    def calculate_record_quality_score(self, row: pd.Series) -> float:
        """
        Calculate quality score for a record to determine which duplicate to keep.
        
        Scoring criteria:
        1. Data completeness (number of non-null fields) - PRIMARY
        2. Valuation date recency - SECONDARY
        3. Valuation amount - TERTIARY
        """
        # Count non-null fields
        completeness = row.notna().sum()
        
        # Parse date score (more recent = higher score)
        date_score = 0
        date_field = None
        
        # Check various date field names
        for field in ['valuation_date', 'Data de Valuation', 'created_date', 'Data_Valuation']:
            if field in row and pd.notna(row[field]):
                date_field = row[field]
                break
        
        if date_field is not None:
            try:
                if isinstance(date_field, str):
                    # Try dd/mm/yyyy format
                    if '/' in date_field:
                        parts = date_field.split('/')
                        if len(parts) == 3:
                            day, month, year = parts[0], parts[1], parts[2].split()[0]  # Handle time part
                            date_score = int(year) * 10000 + int(month) * 100 + int(day)
                    # Try yyyy-mm-dd format
                    elif '-' in date_field:
                        parts = date_field.split('-')
                        if len(parts) == 3:
                            year, month, day = parts[0], parts[1], parts[2].split()[0]
                            date_score = int(year) * 10000 + int(month) * 100 + int(day)
                elif pd.api.types.is_datetime64_any_dtype(type(date_field)):
                    date_score = date_field.year * 10000 + date_field.month * 100 + date_field.day
            except:
                date_score = 0
        
        # Parse valuation amount
        valuation_score = 0
        valuation_field = None
        
        # Check various valuation field names
        for field in ['valuation_amount', 'Resultado_Valuation', 'Valuation', 'valuation']:
            if field in row and pd.notna(row[field]):
                valuation_field = row[field]
                break
        
        if valuation_field is not None:
            try:
                if isinstance(valuation_field, str):
                    # Remove currency symbol and convert Brazilian format
                    val_str = str(valuation_field)
                    val_str = val_str.replace('R$', '').replace(' ', '')
                    val_str = val_str.replace('.', '').replace(',', '.')
                    valuation_score = float(val_str)
                else:
                    valuation_score = float(valuation_field)
            except:
                valuation_score = 0
        
        # Combine scores with weights
        # Completeness is most important, then date, then valuation
        total_score = (completeness * 1000000) + (date_score * 10) + (valuation_score / 1000000)
        
        return total_score
    
    def deduplicate_dataframe(self, df: pd.DataFrame, email_column: str = 'email', 
                            dataset_name: str = 'dataset') -> Tuple[pd.DataFrame, DeduplicationStats]:
        """
        Remove duplicates based on email, keeping the highest quality record.
        
        Args:
            df: DataFrame to deduplicate
            email_column: Name of the email column
            dataset_name: Name of the dataset for reporting
        
        Returns:
            Tuple of (deduplicated DataFrame, deduplication statistics)
        """
        if df.empty or email_column not in df.columns:
            return df, None
        
        original_count = len(df)
        
        # Skip if no duplicates
        if not df.duplicated(subset=[email_column]).any():
            stats = DeduplicationStats(
                original_count=original_count,
                final_count=original_count,
                removed_count=0,
                unique_emails_with_duplicates=0,
                max_duplicates_per_email=1,
                avg_duplicates_per_email=1.0
            )
            self.consolidation_report.append(
                f"{dataset_name}: No duplicates found - {original_count} records preserved"
            )
            return df, stats
        
        # Calculate quality scores
        df['_quality_score'] = df.apply(self.calculate_record_quality_score, axis=1)
        
        # Get duplicate statistics before removal
        email_counts = df[email_column].value_counts()
        duplicate_emails = email_counts[email_counts > 1]
        unique_emails_with_duplicates = len(duplicate_emails)
        max_duplicates = duplicate_emails.max() if len(duplicate_emails) > 0 else 1
        avg_duplicates = duplicate_emails.mean() if len(duplicate_emails) > 0 else 1.0
        
        # Sort by email and quality score (descending)
        df_sorted = df.sort_values([email_column, '_quality_score'], ascending=[True, False])
        
        # Keep only the first (best) record for each email
        df_deduplicated = df_sorted.drop_duplicates(subset=[email_column], keep='first')
        
        # Remove the quality score column
        df_deduplicated = df_deduplicated.drop('_quality_score', axis=1)
        
        final_count = len(df_deduplicated)
        removed_count = original_count - final_count
        
        # Create statistics
        stats = DeduplicationStats(
            original_count=original_count,
            final_count=final_count,
            removed_count=removed_count,
            unique_emails_with_duplicates=unique_emails_with_duplicates,
            max_duplicates_per_email=max_duplicates,
            avg_duplicates_per_email=avg_duplicates
        )
        
        # Add to consolidation report
        self.consolidation_report.append(
            f"{dataset_name}: Removed {removed_count} duplicates from {original_count} records "
            f"({(removed_count/original_count)*100:.1f}% reduction) - {final_count} unique records remain"
        )
        
        # Store statistics
        self.deduplication_stats[dataset_name] = stats
        
        return df_deduplicated, stats
    
    def load_excel_file(self, filename: str) -> pd.DataFrame:
        """Load data from Excel file"""
        filepath = self.data_dir / filename
        if filepath.exists():
            try:
                df = pd.read_excel(filepath)
                print(f"✓ Loaded {len(df)} records from {filename}")
                return df
            except Exception as e:
                print(f"✗ Error loading {filename}: {e}")
        else:
            print(f"✗ File not found: {filename}")
        return pd.DataFrame()
    
    def process_and_deduplicate_crm_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process CRM data and remove duplicates"""
        if df.empty:
            return df
        
        # Apply deduplication FIRST before any processing
        df_dedup, stats = self.deduplicate_dataframe(
            df, 
            email_column='Email' if 'Email' in df.columns else 'email',
            dataset_name='CRM Data'
        )
        
        # Now process the deduplicated data
        # Rename columns to English
        column_mapping = {}
        for col in df_dedup.columns:
            if col in self.field_translations:
                column_mapping[col] = self.field_translations[col]
        
        if column_mapping:
            df_dedup = df_dedup.rename(columns=column_mapping)
        
        # Calculate quality metrics
        total_records = len(df_dedup)
        email_col = 'email' if 'email' in df_dedup.columns else 'Email'
        complete_records = df_dedup.dropna(subset=[email_col]).shape[0] if email_col in df_dedup.columns else 0
        
        self.quality_metrics['crm_data'] = DataQualityMetrics(
            total_records=total_records,
            complete_records=complete_records,
            duplicates_found=stats.removed_count if stats else 0,
            duplicates_removed=stats.removed_count if stats else 0,
            invalid_emails=0,  # Would need validation logic
            invalid_phones=0,
            missing_critical_fields=total_records - complete_records,
            data_completeness_score=(complete_records / total_records * 100) if total_records > 0 else 0,
            deduplication_rate=(stats.removed_count / stats.original_count * 100) if stats and stats.original_count > 0 else 0
        )
        
        return df_dedup
    
    def create_deduplication_report_worksheet(self, wb: Workbook):
        """Create a detailed deduplication report worksheet"""
        ws = wb.create_sheet("Deduplication Report")
        
        # Title
        ws['A1'] = "Email Deduplication Report"
        ws['A1'].font = Font(bold=True, size=16, color="366092")
        ws.merge_cells('A1:H1')
        
        # Generated date
        ws['A2'] = f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A2'].font = Font(italic=True, size=10)
        
        # Summary section
        row = 4
        ws[f'A{row}'] = "DEDUPLICATION SUMMARY"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        ws.merge_cells(f'A{row}:H{row}')
        
        # Headers for summary table
        row += 2
        headers = ['Dataset', 'Original Records', 'Duplicates Found', 'Records Removed', 
                  'Final Records', 'Reduction %', 'Max Duplicates/Email', 'Avg Duplicates/Email']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="366092")
            cell.alignment = Alignment(horizontal="center")
        
        # Data rows
        row += 1
        total_original = 0
        total_removed = 0
        total_final = 0
        
        for dataset_name, stats in self.deduplication_stats.items():
            if stats:
                ws.cell(row=row, column=1, value=dataset_name)
                ws.cell(row=row, column=2, value=stats.original_count)
                ws.cell(row=row, column=3, value=stats.unique_emails_with_duplicates)
                ws.cell(row=row, column=4, value=stats.removed_count)
                ws.cell(row=row, column=5, value=stats.final_count)
                reduction_pct = (stats.removed_count / stats.original_count * 100) if stats.original_count > 0 else 0
                ws.cell(row=row, column=6, value=f"{reduction_pct:.1f}%")
                ws.cell(row=row, column=7, value=stats.max_duplicates_per_email)
                ws.cell(row=row, column=8, value=f"{stats.avg_duplicates_per_email:.1f}")
                
                # Color coding for reduction percentage
                if reduction_pct > 30:
                    ws.cell(row=row, column=6).fill = PatternFill("solid", fgColor="FFB6C1")
                elif reduction_pct > 20:
                    ws.cell(row=row, column=6).fill = PatternFill("solid", fgColor="FFFF99")
                elif reduction_pct > 10:
                    ws.cell(row=row, column=6).fill = PatternFill("solid", fgColor="90EE90")
                
                total_original += stats.original_count
                total_removed += stats.removed_count
                total_final += stats.final_count
                row += 1
        
        # Total row
        ws.cell(row=row, column=1, value="TOTAL")
        ws.cell(row=row, column=2, value=total_original)
        ws.cell(row=row, column=4, value=total_removed)
        ws.cell(row=row, column=5, value=total_final)
        total_reduction = (total_removed / total_original * 100) if total_original > 0 else 0
        ws.cell(row=row, column=6, value=f"{total_reduction:.1f}%")
        
        # Make total row bold
        for col in range(1, 9):
            ws.cell(row=row, column=col).font = Font(bold=True)
        
        # Quality criteria section
        row += 3
        ws[f'A{row}'] = "DEDUPLICATION CRITERIA"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        ws.merge_cells(f'A{row}:H{row}')
        
        row += 2
        criteria = [
            "1. PRIMARY: Data Completeness - Records with more filled fields are preferred",
            "2. SECONDARY: Recency - More recent valuation dates are preferred (dd/mm/yyyy format)",
            "3. TERTIARY: Valuation Amount - Higher valuation amounts are used as tiebreaker",
            "",
            "Selection Process:",
            "• All records are grouped by email address",
            "• Within each group, records are scored based on the above criteria",
            "• The highest-scoring record from each group is retained",
            "• All other records in the group are removed as duplicates"
        ]
        
        for criterion in criteria:
            ws[f'A{row}'] = criterion
            if criterion.startswith("Selection Process:"):
                ws[f'A{row}'].font = Font(bold=True)
            row += 1
        
        # Benefits section
        row += 2
        ws[f'A{row}'] = "BENEFITS OF DEDUPLICATION"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        ws.merge_cells(f'A{row}:H{row}')
        
        row += 2
        benefits = [
            "✓ Improved data quality and integrity",
            "✓ More accurate analytics and reporting",
            "✓ Reduced storage requirements",
            "✓ Better customer communication (no duplicate emails)",
            "✓ Cleaner data for machine learning and predictive models",
            "✓ Compliance with data protection regulations"
        ]
        
        for benefit in benefits:
            ws[f'A{row}'] = benefit
            ws[f'A{row}'].font = Font(color="2E7D32")
            row += 1
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            try:
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            except AttributeError:
                # Skip merged cells
                continue
    
    def create_styled_workbook(self) -> Workbook:
        """Create a workbook with custom styles"""
        wb = Workbook()
        
        # Define custom named styles
        header_style = NamedStyle(name="header_style")
        header_style.font = Font(bold=True, color="FFFFFF", size=11)
        header_style.fill = PatternFill("solid", fgColor="366092")
        header_style.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        header_style.border = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
        wb.add_named_style(header_style)
        
        data_style = NamedStyle(name="data_style")
        data_style.font = Font(size=10)
        data_style.alignment = Alignment(horizontal="left", vertical="center")
        data_style.border = Border(
            left=Side(style='thin', color='D3D3D3'),
            right=Side(style='thin', color='D3D3D3'),
            top=Side(style='thin', color='D3D3D3'),
            bottom=Side(style='thin', color='D3D3D3')
        )
        wb.add_named_style(data_style)
        
        return wb
    
    def run_enhanced_etl(self) -> str:
        """Execute the enhanced ETL pipeline with deduplication"""
        print("\n🚀 Starting ENHANCED ETL Pipeline with Deduplication...")
        print("="*60)
        
        # Load the original CRM data file
        print("\n📂 Loading CRM data...")
        filename = "CRM_Dados_Padronizados_COMPLETO_20250904_002307.xlsx"
        df = self.load_excel_file(filename)
        
        if df.empty:
            print("❌ No data loaded!")
            return None
        
        print(f"📊 Original data: {len(df)} records")
        
        # Process and deduplicate
        print("\n🔄 Processing and deduplicating data...")
        df_processed = self.process_and_deduplicate_crm_data(df)
        
        print(f"✅ After deduplication: {len(df_processed)} unique records")
        
        # Create workbook
        print("\n📊 Creating Excel workbook with reports...")
        wb = self.create_styled_workbook()
        
        # Remove default sheet
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])
        
        # Create main data worksheet
        ws = wb.create_sheet("Deduplicated Data")
        for r in dataframe_to_rows(df_processed, index=False, header=True):
            ws.append(r)
        
        # Apply styling to headers
        for cell in ws[1]:
            cell.style = "header_style"
        
        # Apply styling to data and format specific columns
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.style = "data_style"
                
                # Format dates (dd/mm/yyyy HH:MM)
                if cell.column in [1, 2]:  # Adjust based on your date columns
                    cell.number_format = 'DD/MM/YYYY HH:MM'
                
                # Format currency
                if 'valuation' in str(ws.cell(1, cell.column).value).lower() or \
                   'revenue' in str(ws.cell(1, cell.column).value).lower() or \
                   'mrr' in str(ws.cell(1, cell.column).value).lower() or \
                   'ltm' in str(ws.cell(1, cell.column).value).lower():
                    cell.number_format = 'R$ #,##0.00'
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            try:
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            except AttributeError:
                # Skip merged cells
                continue
        
        # Freeze top row
        ws.freeze_panes = 'A2'
        
        # Create deduplication report
        self.create_deduplication_report_worksheet(wb)
        print("✓ Created Deduplication Report")
        
        # Create data quality worksheet
        ws_quality = wb.create_sheet("Data Quality")
        ws_quality['A1'] = "Data Quality Report"
        ws_quality['A1'].font = Font(bold=True, size=16)
        
        row = 3
        ws_quality['A3'] = "Metric"
        ws_quality['B3'] = "Value"
        
        metrics = self.quality_metrics.get('crm_data')
        if metrics:
            metrics_data = [
                ("Total Records (after dedup)", metrics.total_records),
                ("Complete Records", metrics.complete_records),
                ("Duplicates Found", metrics.duplicates_found),
                ("Duplicates Removed", metrics.duplicates_removed),
                ("Data Completeness", f"{metrics.data_completeness_score:.1f}%"),
                ("Deduplication Rate", f"{metrics.deduplication_rate:.1f}%")
            ]
            
            for metric_name, metric_value in metrics_data:
                row += 1
                ws_quality[f'A{row}'] = metric_name
                ws_quality[f'B{row}'] = metric_value
        
        print("✓ Created Data Quality Report")
        
        # Save workbook
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"CRM_ETL_Deduplicated_{timestamp}.xlsx"
        output_path = self.data_dir / output_filename
        
        wb.save(output_path)
        
        print(f"\n✅ ETL with Deduplication Complete!")
        print(f"📍 Output file: {output_filename}")
        print(f"📂 Location: {output_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("📈 DEDUPLICATION SUMMARY:")
        print("="*60)
        
        for dataset_name, stats in self.deduplication_stats.items():
            if stats:
                print(f"\n{dataset_name}:")
                print(f"  Original records: {stats.original_count:,}")
                print(f"  Duplicates removed: {stats.removed_count:,}")
                print(f"  Final unique records: {stats.final_count:,}")
                print(f"  Reduction: {(stats.removed_count/stats.original_count)*100:.1f}%")
                print(f"  Max duplicates per email: {stats.max_duplicates_per_email}")
                print(f"  Avg duplicates per email: {stats.avg_duplicates_per_email:.1f}")
        
        return output_filename


def main():
    """Main execution function"""
    processor = EnhancedCRMProcessor()
    processor.run_enhanced_etl()


if __name__ == "__main__":
    main()
