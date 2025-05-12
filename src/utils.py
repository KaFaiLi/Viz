import pandas as pd
from typing import Optional
from pathlib import Path

class DataLoader:
    """Class to handle data loading and preprocessing operations."""
    
    def __init__(self):
        self.data = None
        
    def load_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load data from a CSV file.
        
        Args:
            file_path (str): Path to the CSV file
            **kwargs: Additional arguments to pass to pd.read_csv
            
        Returns:
            pd.DataFrame: Loaded and preprocessed data
        """
        try:
            self.data = pd.read_csv(file_path, **kwargs)
            self._preprocess_data()
            return self.data
        except Exception as e:
            raise Exception(f"Error loading CSV file: {str(e)}")
    
    def _preprocess_data(self):
        """Preprocess the loaded data."""
        if self.data is None:
            raise Exception("No data loaded. Please load data first.")
            
        try:
            # Convert relevant columns to appropriate types
            # Ensure 'Date' column is converted to datetime
            self.data['consoValueDate'] = pd.to_datetime(self.data['consoValueDate'])
        except KeyError as e:
            raise Exception(f"Error converting Date column: {str(e)}")
        except Exception as e:
            raise Exception(f"Error during data preprocessing: {str(e)}")
        
        # Handle missing consoMreMetricName
        self.data['consoMreMetricName'] = self.data['consoMreMetricName'].fillna(
            self.data['rmRiskMetricName']
        )
        
        # Convert numeric columns
        numeric_cols = ['consoValue', 'limMaxValue', 'limMinValue']
        for col in numeric_cols:
            self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
    
    def validate_data(self) -> bool:
        """
        Validate that the data has all required columns.
        
        Returns:
            bool: True if data is valid, raises Exception otherwise
        """
        required_columns = [
            'limId', 'rmRiskIndicator', 'rmRiskMetricName', 'stranaNodeName',
            'consoValue', 'Date', 'consoMreMetricName', 'limMaxValue', 'limMinValue'
        ]
        
        missing_cols = [col for col in required_columns if col not in self.data.columns]
        if missing_cols:
            raise Exception(f"Missing required columns: {missing_cols}")
        
        return True 

    def get_data(self) -> pd.DataFrame:
        return self.data 