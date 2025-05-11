import unittest
import pandas as pd
from src.etl import clean_oecd, clean_survey_2014

class TestETL(unittest.TestCase):
    def test_clean_oecd(self):
        # Create test data
        test_data = pd.DataFrame({
            'STRUCTURE': ['A', 'B', None],
            'OBS_VALUE': [1, 2, 3]
        })
        # Test cleaning function
        cleaned = clean_oecd(test_data)
        self.assertFalse(cleaned.empty)
        
    # Add more tests for each function

if __name__ == '__main__':
    unittest.main()