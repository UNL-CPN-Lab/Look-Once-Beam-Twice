#train_mlp.py


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import joblib

# Define the MLP model
class OffsetMLP(nn.Module):
    def __init__(self, input_dim, hidden_dim=128):
        super(OffsetMLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim)
        self.norm3 = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(0.2)
        self.fc4 = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = torch.relu(self.norm1(self.fc1(x)))
        x = torch.relu(self.norm2(self.fc2(x)))
        x = self.dropout(torch.relu(self.norm3(self.fc3(x))))
        return self.fc4(x)

# Load and clean dataset
def load_clean_offset_dataset(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df.drop(columns=[col for col in df.columns if "Unnamed" in col], errors='ignore')
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()
    return df

# Train model using enriched dataset
def train_offset_model(dataset_path, num_epochs=200, batch_size=32, learning_rate=0.001, test_split=0.2):
    df = load_clean_offset_dataset(dataset_path)

    # Use full enriched dataset
    feature_cols = [
        "Boresight",
        "snr_thresh_db",
        "Rx Beam Index (YOLO Predicted)",
        "Initial SNR (dB)"
    ]
    X = df[feature_cols].values
    y = df['Offset Error'].values.reshape(-1, 1)

    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=test_split, random_state=42)

    # Convert to tensors
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test, dtype=torch.float32)

    # DataLoader
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Initialize model
    model = OffsetMLP(input_dim=X.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn = nn.SmoothL1Loss()

    # Train loop
    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            predictions = model(batch_X)
            loss = loss_fn(predictions, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss:.4f}")

    # Evaluate
    model.eval()
    with torch.no_grad():
        y_pred = model(X_test_tensor).numpy()
        mse = mean_squared_error(y_test, y_pred)
        print(f"\nTest MSE: {mse:.4f}")

    # Save artifacts
    torch.save(model.state_dict(), "offset_mlp_model_sc_jul20_offline.pt")
    joblib.dump(scaler, "offset_scaler_sc_jul20_offline.pkl")

    return model, scaler, y_test, y_pred, y

# Train
model, scaler, y_test, y_pred, y_all = train_offset_model("offset_dataset_sc_jul20_offline.csv")

# Plot predictions vs actual
plt.figure(figsize=(10,5))
plt.scatter(y_test, y_pred, alpha=0.5, label="Predictions")
plt.plot([y_all.min(), y_all.max()], [y_all.min(), y_all.max()], 'r--', label="Ideal")
plt.xlabel("Actual Offset Error")
plt.ylabel("Predicted Offset Error")
plt.title("Predicted vs Actual Offset Error")
plt.legend()
plt.grid(True)
plt.show()

# Plot error histogram
errors = y_test - y_pred
plt.hist(errors, bins=30, alpha=0.7, edgecolor='black')
plt.title("Histogram of Prediction Errors")
plt.xlabel("Prediction Error")
plt.ylabel("Frequency")
plt.grid(True)
plt.show()
