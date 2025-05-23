# -*- coding: utf-8 -*-
"""Plant Disease Detection.ipynb


"""

# ============== SETUP ==============
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
from PIL import Image
from google.colab import drive, files
import seaborn as sns

# Connect to Google Drive
drive.mount('/content/drive')

# Check device (GPU or CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# ============== DATA LOADING ==============

data_dir = "/content/drive/MyDrive/CSE400/PlantVillage"  # dataset path

# Data transformations for training and testing
train_transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(20),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Normalize for ResNet
])

test_transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Normalize for ResNet
])

# Load dataset using ImageFolder
full_dataset = datasets.ImageFolder(data_dir, transform=train_transform)
class_names = full_dataset.classes

# Split dataset into train and test sets
train_size = int(0.8 * len(full_dataset))
test_size = len(full_dataset) - train_size
train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

# Apply transforms to train and test datasets
train_dataset.dataset.transform = train_transform
test_dataset.dataset.transform = test_transform

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32)

print(f"Total classes: {len(class_names)}")
print("Sample classes:", class_names[:5])


# Load pretrained ResNet18 model
model = models.resnet18(pretrained=True)

# Modify the last layer to match the number of classes in the dataset
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, len(class_names))  # Change output layer for the number of classes

# Move model to the available device on colab (GPU/CPU)
model = model.to(device)

# ============== TRAINING ==============
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

epochs = 5
train_losses = []

for epoch in range(epochs):
    model.train()
    running_loss = 0
    all_preds, all_labels = [], []

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        all_preds.extend(torch.argmax(outputs, 1).cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    train_loss = running_loss / len(train_loader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='weighted')

    print(f"Epoch {epoch+1}/{epochs} | Loss: {train_loss:.4f} | Acc: {acc:.4f} | F1: {f1:.4f}")
    train_losses.append(train_loss)

# ============== TESTING ==============
model.eval()
test_preds, test_labels = [], []

with torch.no_grad():
    for images, labels in test_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        preds = torch.argmax(outputs, 1)
        test_preds.extend(preds.cpu().numpy())
        test_labels.extend(labels.cpu().numpy())

test_acc = accuracy_score(test_labels, test_preds)
test_f1 = f1_score(test_labels, test_preds, average='weighted')
print(f"\nTest Accuracy: {test_acc:.4f} | Test F1 Score: {test_f1:.4f}")

# ============== CONFUSION MATRIX ==============
# Compute confusion matrix
cm = confusion_matrix(test_labels, test_preds)

# Plot confusion matrix using seaborn
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap="Blues", xticklabels=class_names, yticklabels=class_names)
plt.xlabel('Predicted Labels')
plt.ylabel('True Labels')
plt.title('Confusion Matrix')
plt.show()

# ============== VISUALIZATION ==============
plt.figure(figsize=(8, 5))
plt.plot(range(1, epochs + 1), train_losses, marker='o')
plt.title("Training Loss per Epoch")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.grid(True)
plt.show()

# ============== PREDICT CUSTOM IMAGE ==============
# Upload a custom image for prediction
uploaded = files.upload()
img_path = list(uploaded.keys())[0]
img = Image.open(img_path).convert("RGB")

# Apply the test transform to the uploaded image
img_tensor = test_transform(img).unsqueeze(0).to(device)

# Predict the class
model.eval()
with torch.no_grad():
    output = model(img_tensor)
    _, pred = torch.max(output, 1)
    predicted_class = class_names[pred.item()]
    print(f"\n✅ Predicted Disease/Class: {predicted_class}")

# Show the uploaded image
plt.imshow(img)
plt.title(f"Predicted: {predicted_class}")
plt.axis('off')
plt.show()
