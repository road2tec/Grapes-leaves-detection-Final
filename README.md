# 🍇 GrapeGuard AI — Grapevine Disease Detection System

An end-to-end AI-powered web application that detects grapevine leaf diseases using a trained Convolutional Neural Network (CNN). Users can upload grape leaf images and receive instant disease classification with confidence scores.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Diseases Detected](#diseases-detected)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Model Training](#model-training)
- [API Endpoints](#api-endpoints)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)

---

## 🔍 Overview

The Grapevine Disease Detection System allows users to:

- **Register** and **Login** with secure authentication (JWT + bcrypt)
- **Upload** grape leaf images for analysis
- **Get instant predictions** powered by a trained CNN model
- **View prediction history** on a beautiful dashboard
- **Track statistics** including total predictions, average confidence, and disease distribution

---

## 🦠 Diseases Detected

| Disease | Description |
|---------|-------------|
| **Black Rot** | Caused by *Guignardia bidwellii*, creates circular lesions with dark borders |
| **ESCA** | Complex fungal disease (Black Measles) causing tiger-stripe patterns on leaves |
| **Leaf Blight** | Irregular brown patches that expand rapidly, causing defoliation |
| **Healthy** | Vibrant, disease-free grape leaf |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5 |
| **Backend** | Flask (Python) |
| **Database** | MongoDB (pymongo) |
| **AI Model** | TensorFlow / Keras (CNN) |
| **Authentication** | JWT (PyJWT) + bcrypt |
| **Image Processing** | Pillow, NumPy |
| **Evaluation** | scikit-learn, matplotlib, seaborn |

---

## 📁 Project Structure

```
GrapevineDisease/
│
├── Original Data/              # Dataset
│   ├── train/
│   │   ├── Black Rot/
│   │   ├── ESCA/
│   │   ├── Healthy/
│   │   └── Leaf Blight/
│   └── test/
│       ├── Black Rot/
│       ├── ESCA/
│       ├── Healthy/
│       └── Leaf Blight/
│
├── model/
│   ├── model_training.py       # CNN training script
│   ├── predict.py              # Prediction module
│   └── grape_disease_model.h5  # Trained model (generated)
│
├── backend/
│   ├── app.py                  # Flask API server
│   ├── database.py             # MongoDB operations
│   └── auth.py                 # JWT authentication
│
├── frontend/
│   ├── index.html              # Home page
│   ├── login.html              # Login page
│   ├── register.html           # Registration page
│   ├── dashboard.html          # Prediction history
│   ├── predict.html            # Disease prediction page
│   └── styles.css              # Global stylesheet
│
├── static/                     # Static assets
├── uploads/                    # Uploaded images
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## ⚙️ Setup & Installation

### Prerequisites

- **Python 3.8+**
- **MongoDB** (running on localhost:27017)
- **pip** (Python package manager)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Start MongoDB

Make sure MongoDB is running:

```bash
mongod
```

### Step 3: Train the Model (First time only)

```bash
python model/model_training.py
```

This will:
- Load the dataset from `Original Data/`
- Train the CNN with data augmentation and class balancing
- Save the model to `model/grape_disease_model.h5`
- Generate evaluation plots (confusion matrix, training curves)

### Step 4: Run the Application

```bash
python backend/app.py
```

The application will be available at: **http://localhost:5000**

---

## 🚀 Running the Application

```bash
# Quick start (after setup is complete):
python backend/app.py
```

Then open your browser and navigate to:
- **Home**: http://localhost:5000
- **Register**: http://localhost:5000/register
- **Login**: http://localhost:5000/login
- **Predict**: http://localhost:5000/predict-page
- **Dashboard**: http://localhost:5000/dashboard

---

## 🧠 Model Training

The CNN model architecture:

```
Conv2D(32) → BatchNorm → MaxPool →
Conv2D(64) → BatchNorm → MaxPool →
Conv2D(128) → BatchNorm → MaxPool →
Conv2D(256) → BatchNorm → MaxPool →
Flatten → Dense(512) → Dropout(0.5) →
Dense(256) → Dropout(0.3) → Softmax(4)
```

**Training Features:**
- Data augmentation (rotation, zoom, flip, shift, brightness)
- Class weight balancing for imbalanced data
- Early stopping to prevent overfitting
- Learning rate reduction on plateau
- Confusion matrix and classification report

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Home page | No |
| GET | `/login` | Login page | No |
| GET | `/register` | Register page | No |
| GET | `/predict-page` | Prediction page | No (client-side check) |
| GET | `/dashboard` | Dashboard page | No (client-side check) |
| POST | `/register` | Create new user | No |
| POST | `/login` | Authenticate user | No |
| POST | `/predict` | Upload & predict | Yes (JWT) |
| GET | `/api/history` | Get predictions | Yes (JWT) |

---

## 🔮 Future Improvements

- Transfer learning with MobileNetV2/ResNet for better accuracy
- Real-time webcam prediction
- Treatment recommendations for each disease
- Mobile-responsive PWA
- Multi-language support
- Export prediction reports as PDF
- Cloud deployment (AWS/GCP/Azure)

---

## 📝 License

This project is developed for educational and research purposes.

---

**Developed with ❤️ for Sustainable Agriculture**
