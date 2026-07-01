import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from dataset import Dataset
from model import CNN
from sklearn.model_selection import train_test_split
from torch.utils.data import Subset


EPOCHS = 20
BATCH_SIZE = 32
LR = 1e-3
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train():
    dataset = Dataset()

    labels = [label for _, label in dataset.all_files]
    train_idx, val_idx = train_test_split(
        range(len(dataset)), test_size=0.2, stratify=labels, random_state=42
    )
    
    train_set = Subset(dataset, train_idx)
    val_set = Subset(dataset, val_idx)

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE)


    model = CNN().to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.BCEWithLogitsLoss()

    best_val_loss = float("inf")

    for epoch in range(EPOCHS):
        # --- train ---
        model.train()
        train_loss = 0
        for x, y in train_loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()
            pred = model(x).squeeze(1)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # --- val ---
        model.eval()
        val_loss = 0
        correct = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(DEVICE), y.to(DEVICE)
                pred = model(x).squeeze(1)
                val_loss += criterion(pred, y).item()
                correct += ((pred > 0.0) == y).sum().item()

        val_acc = correct / len(val_set)
        print(f"Epoch {epoch+1}/{EPOCHS} | train_loss: {train_loss/len(train_loader):.4f} | val_loss: {val_loss/len(val_loader):.4f} | val_acc: {val_acc:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "best_model.pt")
            print("  => saved best model")

if __name__ == "__main__":
    train()