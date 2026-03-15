"""
============================================
Grapevine Disease Detection - Prediction Module
============================================

This module handles loading the trained CNN model and making
predictions on new grape leaf images.

Functions:
  - load_model(): Load the trained .h5 model from disk
  - preprocess_image(): Prepare an image for model input
  - predict_disease(): Run prediction and return disease + confidence

The prediction pipeline:
  1. Load image from file path
  2. Resize to 224x224 (model's expected input size)
  3. Normalize pixel values to [0, 1]
  4. Expand dimensions to match batch format
  5. Run through model to get class probabilities
  6. Return disease name and confidence percentage
"""

import os
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model as keras_load_model

# ============================================
# Configuration
# ============================================
IMAGE_SIZE = (128, 128)  # Must match the training image size (CPU-optimized)

# Disease class names in the same order as training
# This order must match the class_indices from training
CLASS_NAMES = ['Black Rot', 'ESCA', 'Healthy', 'Leaf Blight']

# Path to the saved model file
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, 'grape_disease_model.h5')

# Global model variable (loaded once, reused for all predictions)
_model = None


def load_model():
    """
    Load the trained Keras model from the .h5 file.
    
    Uses a global variable to cache the model so it's only loaded
    once, even if predict_disease() is called multiple times.
    This significantly improves prediction speed for web API usage.
    
    Returns:
        keras.Model: The loaded and compiled CNN model
    
    Raises:
        FileNotFoundError: If the model file doesn't exist
    """
    global _model
    
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found at: {MODEL_PATH}. "
                "Please run model_training.py first to train and save the model."
            )
        
        print(f"[INFO] Loading model from: {MODEL_PATH}")
        _model = keras_load_model(MODEL_PATH)
        print("[INFO] Model loaded successfully!")
    
    return _model


def preprocess_image(image_path):
    """
    Preprocess an image for model prediction.
    
    Steps:
      1. Open the image using PIL
      2. Convert to RGB (handles grayscale or RGBA images)
      3. Resize to 224x224 to match model input
      4. Convert to numpy array
      5. Normalize pixel values from [0, 255] to [0, 1]
      6. Add batch dimension (model expects shape: [1, 224, 224, 3])
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        numpy.ndarray: Preprocessed image array with shape (1, 224, 224, 3)
    
    Raises:
        FileNotFoundError: If the image file doesn't exist
        ValueError: If the image cannot be processed
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    try:
        # Open and convert image to RGB format
        img = Image.open(image_path).convert('RGB')
        
        # Resize to the model's expected input dimensions
        img = img.resize(IMAGE_SIZE, Image.LANCZOS)
        
        # Convert PIL image to numpy array (shape: 224, 224, 3)
        img_array = np.array(img, dtype=np.float32)
        
        # Normalize pixel values to [0, 1] range
        # This matches the rescale=1./255 used during training
        img_array = img_array / 255.0
        
        # Add batch dimension: (224, 224, 3) -> (1, 224, 224, 3)
        # The model expects a batch of images, even for single predictions
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
        
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")


def predict_disease(image_path):
    """
    Predict the disease from a grape leaf image.
    
    Pipeline:
      1. Load model (cached after first call)
      2. Preprocess the input image
      3. Run model prediction to get class probabilities
      4. Find the class with highest probability
      5. Return disease name and confidence score
    
    Args:
        image_path (str): Path to the grape leaf image
    
    Returns:
        dict: Prediction result containing:
            - disease_name (str): Name of the predicted disease
            - confidence (float): Confidence percentage (0-100)
            - all_predictions (dict): Probabilities for all classes
    
    Example:
        >>> result = predict_disease("uploads/leaf.jpg")
        >>> print(result)
        {
            "disease_name": "ESCA",
            "confidence": 94.52,
            "all_predictions": {
                "Black Rot": 2.15,
                "ESCA": 94.52,
                "Healthy": 1.83,
                "Leaf Blight": 1.50
            }
        }
    """
    # Load the trained model (uses cache if already loaded)
    model = load_model()
    
    # Preprocess the input image
    processed_image = preprocess_image(image_path)
    
    # Run prediction - returns probability for each class
    predictions = model.predict(processed_image, verbose=0)
    
    # Get the predicted class index (highest probability)
    predicted_class_index = np.argmax(predictions[0])
    
    # Get the confidence score as a percentage
    confidence = float(predictions[0][predicted_class_index]) * 100
    
    # Get the disease name from class index
    disease_name = CLASS_NAMES[predicted_class_index]
    
    # Build detailed predictions for all classes
    all_predictions = {}
    for i, class_name in enumerate(CLASS_NAMES):
        all_predictions[class_name] = round(float(predictions[0][i]) * 100, 2)
    
    result = {
        'disease_name': disease_name,
        'confidence': round(confidence, 2),
        'all_predictions': all_predictions
    }
    
    print(f"[PREDICTION] Disease: {disease_name}, Confidence: {confidence:.2f}%")
    
    return result


if __name__ == '__main__':
    # Quick test - can be run standalone to test prediction
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python predict.py <image_path>")
        print("Example: python predict.py ../uploads/test_leaf.jpg")
        sys.exit(1)
    
    test_image = sys.argv[1]
    result = predict_disease(test_image)
    
    print("\n" + "=" * 40)
    print("  Prediction Result")
    print("=" * 40)
    print(f"  Disease: {result['disease_name']}")
    print(f"  Confidence: {result['confidence']}%")
    print("\n  All Predictions:")
    for disease, conf in result['all_predictions'].items():
        bar = "█" * int(conf / 2)
        print(f"    {disease:15s}: {conf:6.2f}% {bar}")
    print("=" * 40)
