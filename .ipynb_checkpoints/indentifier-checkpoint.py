import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import os
from PIL import Image
import numpy as np

# Set image dimensions and parameters
IMG_HEIGHT = 224
IMG_WIDTH = 224
BATCH_SIZE = 32
NUM_CLASSES = 3  # 3 different lab logos


def create_cnn_model():
    """
    Create a CNN model for logo classification
    """
    model = models.Sequential([
        # First Convolutional Block
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        layers.MaxPooling2D(2, 2),

        # Second Convolutional Block
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),

        # Third Convolutional Block
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),

        # Fourth Convolutional Block
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),

        # Flatten and Dense layers
        layers.Flatten(),
        layers.Dropout(0.5),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(NUM_CLASSES, activation='softmax')
    ])

    return model


def create_transfer_learning_model():
    """
    Alternative: Use transfer learning with MobileNetV2
    This often works better with limited data
    """
    base_model = tf.keras.applications.MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)
    )

    # Freeze base model
    base_model.trainable = False

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.2),
        layers.Dense(NUM_CLASSES, activation='softmax')
    ])

    return model


def setup_data_generators(train_dir, validation_dir=None):
    """
    Setup data generators with augmentation
    """
    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1. / 255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        zoom_range=0.2,
        validation_split=0.2 if validation_dir is None else 0.0
    )

    # No augmentation for validation
    validation_datagen = ImageDataGenerator(rescale=1. / 255)

    if validation_dir is None:
        # Split training data
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(IMG_HEIGHT, IMG_WIDTH),
            batch_size=BATCH_SIZE,
            class_mode='categorical',
            subset='training'
        )

        validation_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(IMG_HEIGHT, IMG_WIDTH),
            batch_size=BATCH_SIZE,
            class_mode='categorical',
            subset='validation'
        )
    else:
        # Separate validation directory
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(IMG_HEIGHT, IMG_WIDTH),
            batch_size=BATCH_SIZE,
            class_mode='categorical'
        )

        validation_generator = validation_datagen.flow_from_directory(
            validation_dir,
            target_size=(IMG_HEIGHT, IMG_WIDTH),
            batch_size=BATCH_SIZE,
            class_mode='categorical'
        )

    return train_generator, validation_generator


def train_model(model, train_generator, validation_generator, epochs=50):
    """
    Train the model with callbacks
    """
    # Compile model
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # Callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            patience=10,
            restore_best_weights=True,
            monitor='val_accuracy'
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            factor=0.2,
            patience=5,
            monitor='val_loss'
        ),
        tf.keras.callbacks.ModelCheckpoint(
            'best_logo_model.h5',
            save_best_only=True,
            monitor='val_accuracy'
        )
    ]

    # Train model
    history = model.fit(
        train_generator,
        epochs=epochs,
        validation_data=validation_generator,
        callbacks=callbacks
    )

    return history


def plot_training_history(history):
    """
    Plot training and validation accuracy/loss
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Plot accuracy
    ax1.plot(history.history['accuracy'], label='Training Accuracy')
    ax1.plot(history.history['val_accuracy'], label='Validation Accuracy')
    ax1.set_title('Model Accuracy')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.legend()

    # Plot loss
    ax2.plot(history.history['loss'], label='Training Loss')
    ax2.plot(history.history['val_loss'], label='Validation Loss')
    ax2.set_title('Model Loss')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.legend()

    plt.tight_layout()
    plt.show()


def predict_logo(model, image, class_names):
    """
    Predict logo class for a single image object

    Args:
        model: Trained Keras model
        image: PIL Image object or numpy array
        class_names: List of class names

    Returns:
        tuple: (predicted_class_name, confidence)
    """
    # Handle different image input types
    if isinstance(image, np.ndarray):
        # If it's already a numpy array
        img = Image.fromarray(image.astype('uint8'))
    else:
        # Assume it's a PIL Image
        img = image

    # Resize to model's expected input size
    img = img.resize((IMG_HEIGHT, IMG_WIDTH))

    # Convert to RGB if needed (handles RGBA, grayscale, etc.)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Convert to array and normalize
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, 0)  # Create batch dimension
    img_array = img_array.astype('float32') / 255.0  # Normalize

    predictions = model.predict(img_array)
    predicted_class = np.argmax(predictions[0])
    confidence = np.max(predictions[0])

    return class_names[predicted_class], confidence


# Main training pipeline
def main():
    """
    Main function to run the training pipeline
    """
    # Set your data directory path here
    # Expected structure:
    # data/
    #   lab1/
    #     logo1.jpg, logo2.jpg, ...
    #   lab2/
    #     logo1.jpg, logo2.jpg, ...
    #   lab3/
    #     logo1.jpg, logo2.jpg, ...

    DATA_DIR = "Logo"  # Change this to your data directory

    if not os.path.exists(DATA_DIR):
        print(f"Please create the data directory: {DATA_DIR}")
        print("Organize your images in subdirectories named after each lab")
        return

    # Setup data generators
    train_gen, val_gen = setup_data_generators(DATA_DIR)

    print(f"Found {train_gen.samples} training images")
    print(f"Found {val_gen.samples} validation images")
    print(f"Class names: {list(train_gen.class_indices.keys())}")

    # Create model (choose one)
    print("Creating model...")
    # model = create_cnn_model()  # Custom CNN
    model = create_transfer_learning_model()  # Transfer learning (recommended)

    print(model.summary())

    # Train model
    print("Starting training...")
    history = train_model(model, train_gen, val_gen, epochs=30)

    # Plot results
    plot_training_history(history)

    # Save final model
    model.save('lab_logo_classifier.h5')
    print("Model saved as 'lab_logo_classifier.h5'")

    # Example prediction (uncomment to use)
    # class_names = list(train_gen.class_indices.keys())
    # predicted_class, confidence = predict_logo(model, "test_image.jpg", class_names)
    # print(f"Predicted: {predicted_class} (Confidence: {confidence:.2f})")


if __name__ == "__main__":
    main()