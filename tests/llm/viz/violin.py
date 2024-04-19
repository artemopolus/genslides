import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Generate some random data for 3 vectors
vector1 = np.random.normal(0, 1, 1000)
vector2 = np.random.normal(1, 1.5, 1000)
vector3 = np.random.normal(-1, 0.5, 1000)

# Combine the data into a single DataFrame
data = {"Vector 1": vector1, "Vector 2": vector2, "Vector 3": vector3}
df = pd.DataFrame(data)

# Create a violin plot
sns.violinplot(data=df, inner="quartile", palette="Set3")

# Add a title and labels
plt.title("Violin Plot of Different Vectors")
plt.xlabel("Vectors")
plt.ylabel("Values")

# Show the plot
plt.show()

