import matplotlib.pyplot as plt
import pandas as pd


plt.rcParams["font.family"] = "Helvetica"
plt.rcParams["font.size"] = 16


df = pd.read_csv("/Users/taromakino/git/diffusers/examples/text_to_image/results/train_loss.csv")

fig, ax = plt.subplots(1, 1, figsize=(6, 3))
ax.plot(df.epoch, df.train_loss)

ax.set_xlabel("Epoch")
ax.set_ylabel("Train loss")

fig.tight_layout()
fig.savefig("train_loss.jpeg")