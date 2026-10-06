import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
import joblib
import logging
from pathlib import Path

# Basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MLPipeline:
    """Manages the entire machine learning workflow."""

    def __init__(self, input_path, model_dir='ml_models'):
        self.input_path = Path(input_path)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.model = None

    def run(self):
        """Executes the complete machine learning pipeline."""
        logging.info("Starting ML pipeline...")
        
        # Load and prepare data
        df = pd.read_csv(self.input_path, sep='|')
        X = df.drop('target_column', axis=1)  # Replace 'target_column' with your actual target
        y = df['target_column']

        # Define preprocessing for numeric and categorical features
        numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
        categorical_features = X.select_dtypes(include=['object']).columns

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numeric_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
            ])

        # Create the ML pipeline
        self.model = Pipeline(steps=[('preprocessor', preprocessor),
                                     ('classifier', RandomForestClassifier(random_state=42))])

        # Split data and train the model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)

        # Evaluate the model
        predictions = self.model.predict(X_test)
        logging.info("Classification Report:\n" + classification_report(y_test, predictions))

        # Save the model
        self.save_model()

    def save_model(self):
        """Saves the trained model to a file."""
        if self.model:
            model_path = self.model_dir / "trained_model.joblib"
            joblib.dump(self.model, model_path)
            logging.info(f"Model saved to {model_path}")

if __name__ == "__main__":
    # Ensure you have a unified dataset from the ETL pipeline
    input_dataset_path = "processed_data/unified_dataset.csv"  # Update with the actual filename
    if Path(input_dataset_path).exists():
        pipeline = MLPipeline(input_dataset_path)
        pipeline.run()
    else:
        logging.error(f"Input dataset not found at '{input_dataset_path}'. Please run the ETL pipeline first.")